"""
Tests for the AI Analyst pipeline (fallback/demo mode — no API key needed).
Run with: pytest tests/test_analyst.py -v
"""
import io
import os
import random

os.environ["DATABASE_URL"] = "sqlite:///./test_analyst_ci.db"

from fastapi.testclient import TestClient
from app.main import app


def _build_sales_csv() -> str:
    random.seed(42)
    rows = ["date,revenue,region"]
    for month in range(1, 7):
        base = 200 + month * 5
        if month == 3:
            base -= 40  # deliberate dip so the significance test has something real to find
        for day in range(1, 21):
            rows.append(f"2026-0{month}-{day:02d},{base + random.randint(-15, 15)},East")
    return "\n".join(rows)


def _setup_dataset(client, headers) -> str:
    r = client.post("/projects", json={"name": "Retail Analysis"}, headers=headers)
    project_id = r.json()["id"]

    files = {"file": ("sales.csv", io.BytesIO(_build_sales_csv().encode()), "text/csv")}
    r = client.post(f"/datasets/upload?project_id={project_id}", files=files, headers=headers)
    assert r.status_code == 201
    return r.json()["id"]


def _auth_headers(client, email="analyst@test.com") -> dict:
    r = client.post("/register", json={"email": email, "password": "pass1234"})
    token = r.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_ask_returns_real_stats_and_skeptic_critique():
    with TestClient(app) as client:
        headers = _auth_headers(client, "analyst1@test.com")
        dataset_id = _setup_dataset(client, headers)

        r = client.post(
            f"/analyst/{dataset_id}/ask",
            json={"question": "Why did revenue decrease in March?"},
            headers=headers,
        )
        assert r.status_code == 200
        body = r.json()

        # The stat test must be computed, not invented — check it looks real
        assert body["stat_test"] is not None
        assert body["stat_test"]["test"] == "welch_t_test"
        assert "p_value" in body["stat_test"]

        # Skeptic Agent must flag limited history (only 6 months of data)
        flag_types = [f["type"] for f in body["critique"]["flags"]]
        assert "insufficient_history_for_seasonality" in flag_types
        assert "correlation_not_causation" in flag_types  # always included
        assert body["critique"]["trust_level"] in ("high", "medium", "low")

        # Confidence should be reduced below a naive 90+ due to the flags raised
        assert body["confidence_score"] < 90


def test_insight_diffing_triggers_on_similar_question():
    with TestClient(app) as client:
        headers = _auth_headers(client, "analyst2@test.com")
        dataset_id = _setup_dataset(client, headers)

        r1 = client.post(
            f"/analyst/{dataset_id}/ask",
            json={"question": "Why did revenue decrease in March?"},
            headers=headers,
        )
        assert r1.json()["diff_summary"] is None  # nothing to compare against yet

        r2 = client.post(
            f"/analyst/{dataset_id}/ask",
            json={"question": "Why did revenue decrease in March again?"},
            headers=headers,
        )
        body2 = r2.json()
        assert body2["diff_summary"] is not None
        assert body2["compared_insight_id"] is not None


def test_analyst_history_persists_insights():
    with TestClient(app) as client:
        headers = _auth_headers(client, "analyst3@test.com")
        dataset_id = _setup_dataset(client, headers)

        client.post(f"/analyst/{dataset_id}/ask", json={"question": "Why did revenue drop?"}, headers=headers)
        client.post(f"/analyst/{dataset_id}/ask", json={"question": "What about churn?"}, headers=headers)

        r = client.get(f"/analyst/{dataset_id}/history", headers=headers)
        assert r.status_code == 200
        assert len(r.json()) == 2
