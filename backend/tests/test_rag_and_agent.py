"""
Tests for the RAG layer and the agentic (LangGraph) forecast routing.
Run with: pytest tests/test_rag_and_agent.py -v
"""
import io
import os
import random

os.environ["DATABASE_URL"] = "sqlite:///./test_rag_ci.db"
os.environ["CHROMA_PERSIST_DIR"] = "./test_chroma_store"

from fastapi.testclient import TestClient
from app.main import app
from app.rag.store import retrieve_context


def _build_sales_csv() -> str:
    random.seed(7)
    rows = ["date,revenue,region"]
    for month in range(1, 8):
        base = 200 + month * 8  # steady upward trend, good for forecast test
        for day in range(1, 21):
            rows.append(f"2026-0{month}-{day:02d},{base + random.randint(-10, 10)},East")
    return "\n".join(rows)


def _auth_headers(client, email: str) -> dict:
    r = client.post("/register", json={"email": email, "password": "pass1234"})
    token = r.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_rag_indexes_schema_and_glossary_on_upload():
    with TestClient(app) as client:
        headers = _auth_headers(client, "rag_test@test.com")
        r = client.post("/projects", json={"name": "RAG Test"}, headers=headers)
        project_id = r.json()["id"]

        csv_content = "revenue,region,sku\n100,East,A1\n200,West,B2\n"
        files = {"file": ("retail.csv", io.BytesIO(csv_content.encode()), "text/csv")}
        r = client.post(f"/datasets/upload?project_id={project_id}", files=files, headers=headers)
        dataset_id = r.json()["id"]

        # Domain should be detected as retail given the 'sku' column
        assert r.json()["domain"] == "retail"

        # Schema docs should now be retrievable for a relevant question
        context = retrieve_context(dataset_id, "tell me about the revenue column")
        assert "Schema notes" in context
        assert "revenue" in context.lower()


def test_agentic_graph_routes_forecast_questions_differently():
    with TestClient(app) as client:
        headers = _auth_headers(client, "forecast_test@test.com")
        r = client.post("/projects", json={"name": "Forecast Test"}, headers=headers)
        project_id = r.json()["id"]

        files = {"file": ("sales.csv", io.BytesIO(_build_sales_csv().encode()), "text/csv")}
        r = client.post(f"/datasets/upload?project_id={project_id}", files=files, headers=headers)
        dataset_id = r.json()["id"]

        r = client.post(
            f"/analyst/{dataset_id}/ask",
            json={"question": "Forecast revenue for next month"},
            headers=headers,
        )
        assert r.status_code == 200
        body = r.json()

        # Forecast branch should not run a SQL-based stat test
        assert body["stat_test"] is None
        assert "trend" in body["explanation"].lower() or "forecast" in body["explanation"].lower()

        # Compare against a diagnostic question on the same dataset — should take the SQL path
        r2 = client.post(
            f"/analyst/{dataset_id}/ask",
            json={"question": "Why did revenue change in March?"},
            headers=headers,
        )
        body2 = r2.json()
        assert body2["stat_test"] is not None
