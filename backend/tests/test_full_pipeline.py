"""
Tests for auto-cleaning, ML training, autonomous analysis, dashboard
generation, and export endpoints.
Run with: pytest tests/test_full_pipeline.py -v
"""
import io
import os
import random

os.environ["DATABASE_URL"] = "sqlite:///./test_full_pipeline_ci.db"

from fastapi.testclient import TestClient
from app.main import app


def _build_churn_csv() -> str:
    random.seed(3)
    rows = ["date,revenue,region,plan,weekly_logins,churn"]
    for month in range(1, 13):
        base = 200 + month * 5
        for day in range(1, 16):
            logins = random.randint(1, 10)
            churn = 1 if logins < 3 and random.random() < 0.7 else (1 if random.random() < 0.05 else 0)
            region = random.choice(["East", "West"])
            plan = random.choice(["basic", "pro"])
            rows.append(f"2026-{month:02d}-{day:02d},{base + random.randint(-10, 10)},{region},{plan},{logins},{churn}")
    return "\n".join(rows)


def _auth_headers(client, email: str) -> dict:
    r = client.post("/register", json={"email": email, "password": "pass1234"})
    token = r.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _setup_dataset(client, headers) -> str:
    r = client.post("/projects", json={"name": "Pipeline Test"}, headers=headers)
    project_id = r.json()["id"]
    files = {"file": ("sales.csv", io.BytesIO(_build_churn_csv().encode()), "text/csv")}
    r = client.post(f"/datasets/upload?project_id={project_id}", files=files, headers=headers)
    assert r.status_code == 201
    return r.json()["id"]


def test_auto_clean_improves_or_maintains_quality_and_returns_report():
    with TestClient(app) as client:
        headers = _auth_headers(client, "clean_test@test.com")
        dataset_id = _setup_dataset(client, headers)

        r = client.post(f"/datasets/{dataset_id}/clean", headers=headers)
        assert r.status_code == 200
        body = r.json()
        assert "cleaning_report" in body
        assert body["quality_score_after"] >= body["quality_score_before"] - 0.01  # cleaning shouldn't make it worse

        # Cleaned file should now be downloadable
        r2 = client.get(f"/datasets/{dataset_id}/export/cleaned", headers=headers)
        assert r2.status_code == 200
        assert "revenue" in r2.text


def test_autonomous_analysis_returns_real_correlations_and_summary():
    with TestClient(app) as client:
        headers = _auth_headers(client, "analysis_test@test.com")
        dataset_id = _setup_dataset(client, headers)

        r = client.get(f"/datasets/{dataset_id}/analysis", headers=headers)
        assert r.status_code == 200
        body = r.json()

        # weekly_logins should show a real negative correlation with churn
        pairs = {(p["column_a"], p["column_b"]): p["correlation"] for p in body["correlations"]["top_pairs"]}
        found_relevant_pair = any(
            "churn" in pair and "weekly_logins" in pair for pair in pairs.keys()
        )
        assert found_relevant_pair

        # The summary must not be the generic "no rows returned" bug — it
        # should actually reference the computed findings.
        assert "no rows were returned" not in body["summary"].lower()
        assert len(body["trends"]) > 0


def test_ml_training_produces_real_metrics_and_feature_importance():
    with TestClient(app) as client:
        headers = _auth_headers(client, "ml_test@test.com")
        dataset_id = _setup_dataset(client, headers)

        r = client.post(f"/ml/{dataset_id}/train?target_column=churn", headers=headers)
        assert r.status_code == 200
        body = r.json()

        assert body["task_type"] == "binary_classification"
        assert 0 <= body["boosted_model"]["metrics"]["accuracy"] <= 1
        assert len(body["feature_importance"]) > 0
        # weekly_logins should be the (or a) top feature, since it's the
        # actual driver of churn in the synthetic data
        top_features = [f["feature"] for f in body["feature_importance"][:2]]
        assert "weekly_logins" in top_features

        # model-info should now be retrievable
        r2 = client.get(f"/ml/{dataset_id}/model-info", headers=headers)
        assert r2.status_code == 200


def test_ml_training_rejects_bad_target_column():
    with TestClient(app) as client:
        headers = _auth_headers(client, "ml_bad_test@test.com")
        dataset_id = _setup_dataset(client, headers)

        r = client.post(f"/ml/{dataset_id}/train?target_column=revenue", headers=headers)
        # revenue has too many distinct values for this classifier endpoint
        assert r.status_code == 400


def test_dashboard_includes_kpis_and_charts():
    with TestClient(app) as client:
        headers = _auth_headers(client, "dashboard_test@test.com")
        dataset_id = _setup_dataset(client, headers)

        r = client.get(f"/datasets/{dataset_id}/dashboard", headers=headers)
        assert r.status_code == 200
        body = r.json()

        assert len(body["kpi_cards"]) > 0
        assert body["time_series"] is not None
        assert "region" in body["bar_charts"]
        assert "date" not in body["bar_charts"]  # date should only appear as the time series, not also a bar chart


def test_pdf_report_export_produces_valid_pdf():
    with TestClient(app) as client:
        headers = _auth_headers(client, "pdf_test@test.com")
        dataset_id = _setup_dataset(client, headers)

        r = client.post(f"/datasets/{dataset_id}/export/report", headers=headers)
        assert r.status_code == 200
        assert r.headers["content-type"] == "application/pdf"
        assert r.content[:4] == b"%PDF"
