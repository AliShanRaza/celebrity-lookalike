from unittest.mock import MagicMock
from app.db import get_db
from app.main import app


def test_root_endpoint(client):
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Celebrity Look-Alike API"
    assert "version" in data


def test_version_endpoint(client, monkeypatch):
    monkeypatch.setattr("app.config.settings.RECOGNITION_PROVIDER", "fake")
    response = client.get("/api/v1/version")
    assert response.status_code == 200
    data = response.json()
    assert "app_version" in data
    assert "build_sha" in data
    assert data["recognition_provider"] == "fake"
    assert data["model_version"] == "fake_v1"
    assert data["index_version"] == "pgvector_cosine_v1"
    assert data["score_version"] == "sigmoid_calibrated_v1"
    assert data["embedding_dimension"] == 512


def test_health_endpoint_success(client, monkeypatch):
    monkeypatch.setattr("app.config.settings.RECOGNITION_PROVIDER", "fake")
    mock_db = MagicMock()
    app.dependency_overrides[get_db] = lambda: mock_db

    try:
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["database"] == "connected"
        assert "build_sha" in data
        assert data["model_version"] == "fake_v1"
        assert data["index_version"] == "pgvector_cosine_v1"
        assert data["score_version"] == "sigmoid_calibrated_v1"
        assert "metrics" in data
        assert "face_validation_outcomes" in data["metrics"]
    finally:
        app.dependency_overrides.clear()
