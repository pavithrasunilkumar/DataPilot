"""
Basic end-to-end API tests.
Run with: pytest tests/test_api.py -v

Uses an in-memory-ish sqlite file so tests don't touch your real database.
"""
import io
import os

os.environ["DATABASE_URL"] = "sqlite:///./test_ci.db"

from fastapi.testclient import TestClient
from app.main import app


def test_health():
    with TestClient(app) as client:
        r = client.get("/health")
        assert r.status_code == 200
        assert r.json() == {"status": "ok"}


def test_register_login_and_upload_flow():
    with TestClient(app) as client:
        r = client.post(
            "/register",
            json={"email": "pytest@example.com", "password": "pass1234", "full_name": "Py Test"},
        )
        assert r.status_code == 201
        token = r.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        r = client.post("/login", json={"email": "pytest@example.com", "password": "pass1234"})
        assert r.status_code == 200

        r = client.post("/login", json={"email": "pytest@example.com", "password": "wrong"})
        assert r.status_code == 401

        r = client.post("/projects", json={"name": "Test Project"}, headers=headers)
        assert r.status_code == 201
        project_id = r.json()["id"]

        csv_content = "revenue,region\n100,East\n200,West\n,East\n100000,West\n100,East\n"
        files = {"file": ("sales.csv", io.BytesIO(csv_content.encode()), "text/csv")}
        r = client.post(
            f"/datasets/upload?project_id={project_id}", files=files, headers=headers
        )
        assert r.status_code == 201
        body = r.json()
        assert body["row_count"] == 5
        assert body["quality_score"] < 100  # the messy data should reduce the score

        dataset_id = body["id"]
        r = client.get(f"/datasets/{dataset_id}/quality-report", headers=headers)
        assert r.status_code == 200
        report = r.json()
        assert report["duplicate_row_pct"] == 20.0
        assert any("outlier" in w.lower() for w in report["warnings"])


def test_unauthenticated_requests_are_rejected():
    with TestClient(app) as client:
        r = client.get("/projects")
        assert r.status_code == 401
