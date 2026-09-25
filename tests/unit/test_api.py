import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.main import app
from src.database.models import Base
from src.database.db import get_db

@pytest.fixture
def client():
    # Use StaticPool with in-memory SQLite so all connections share the same database
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

def test_health(client):
    res = client.get("/api/v1/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"

def test_status(client):
    res = client.get("/api/v1/status")
    assert res.status_code == 200
    assert "stats" in res.json()
    assert "credit_safety_mode" in res.json()

def test_capabilities(client):
    res = client.get("/api/v1/capabilities")
    assert res.status_code == 200
    data = res.json()
    assert data["standard_generation"] is True
    assert len(data["models_available"]) > 0
    assert data["credit_status"] in ["VERIFIED", "UNKNOWN"]

def test_job_lifecycle(client):
    # 1. Create job
    create_payload = {
        "prompt": "Cinematic test prompt for API validation",
        "model": "Nano Banana 2",
        "orientation": "16:9",
        "duration": "5",
        "output_count": 1,
    }
    create_res = client.post("/api/v1/jobs", json=create_payload)
    assert create_res.status_code == 201
    job = create_res.json()
    job_id = job["id"]
    assert job["prompt"] == create_payload["prompt"]
    assert job["status"] == "QUEUED"
    assert job["requested_model"] == "Nano Banana 2"

    # 2. Get job
    get_res = client.get(f"/api/v1/jobs/{job_id}")
    assert get_res.status_code == 200
    assert get_res.json()["id"] == job_id

    # 3. List jobs
    list_res = client.get("/api/v1/jobs")
    assert list_res.status_code == 200
    assert len(list_res.json()) >= 1

    # 4. Cancel job
    cancel_res = client.post(f"/api/v1/jobs/{job_id}/cancel")
    assert cancel_res.status_code == 200
    assert cancel_res.json()["status"] == "CANCELLED"

    # 5. Retry job
    retry_res = client.post(f"/api/v1/jobs/{job_id}/retry")
    assert retry_res.status_code == 200
    assert retry_res.json()["status"] == "QUEUED"

    # 6. Duplicate job
    dup_res = client.post(f"/api/v1/jobs/{job_id}/duplicate")
    assert dup_res.status_code == 201
    assert dup_res.json()["id"] != job_id
    assert dup_res.json()["prompt"] == create_payload["prompt"]

def test_settings_api(client):
    res = client.get("/api/v1/settings")
    assert res.status_code == 200
    assert "DEFAULT_MODEL" in res.json()
    assert "CREDIT_SAFETY_MODE" in res.json()

    # Update settings
    put_res = client.put("/api/v1/settings", json={"CREDIT_SAFETY_MODE": "WARN"})
    assert put_res.status_code == 200
    assert put_res.json()["status"] == "updated"
