import uuid
import pytest
from unittest.mock import MagicMock
import fakeredis

from app.main import app
from app.db import get_db
from app.config import settings
from app.schemas.jobs import JobStatusEnum
from app.services.job_queue import JobQueueManager, QueueFullError
from app.models.celebrity import Celebrity
from app.models.celebrity_image import CelebrityImage
from app.models.celebrity_embedding import CelebrityEmbedding


@pytest.fixture
def fake_redis_client():
    return fakeredis.FakeRedis()


@pytest.fixture
def test_queue_manager(fake_redis_client):
    return JobQueueManager(redis_client=fake_redis_client)


def test_enqueue_and_poll_succeeded_job(client, sample_image_bytes, test_queue_manager, monkeypatch):
    mock_db = MagicMock()
    app.dependency_overrides[get_db] = lambda: mock_db
    monkeypatch.setattr("app.routers.matching.job_queue_manager", test_queue_manager)

    # Synthetic mock candidates
    celeb_id = uuid.uuid4()
    celeb = Celebrity(id=celeb_id, name="Brad Pitt", gender="male", origin="hollywood", bio="Actor")
    img = CelebrityImage(id=uuid.uuid4(), celebrity_id=celeb_id, image_url="brad.jpg")
    emb = CelebrityEmbedding(id=uuid.uuid4(), celebrity_id=celeb_id, celebrity_image_id=img.id)
    mock_candidates = [(emb, img, celeb, 0.2)] # distance = 0.2 -> sim = 0.8 -> score = 90.0%

    monkeypatch.setattr(
        "app.repositories.celebrity_repository.CelebrityRepository.search_nearest_embeddings",
        lambda session, query_vector, model_version, target_gender=None, target_origin=None, limit=50, active_only=True: mock_candidates
    )

    try:
        # 1. Enqueue Job (POST 202)
        response = client.post(
            "/api/v1/matches?async_mode=true",
            files={"file": ("portrait.jpg", sample_image_bytes, "image/jpeg")},
            data={"target_gender": "male", "target_origin": "hollywood"}
        )
        assert response.status_code == 202
        async_data = response.json()
        job_id = async_data["job_id"]
        assert async_data["status"] == "queued"

        # 2. Poll initial queued status
        poll_resp = client.get(f"/api/v1/matches/{job_id}")
        assert poll_resp.status_code == 200
        assert poll_resp.json()["status"] == "queued"

        # 3. Process job via worker logic
        processed_id = test_queue_manager.process_next_job(db=mock_db)
        assert processed_id == job_id

        # 4. Poll completed status & verify results
        completed_resp = client.get(f"/api/v1/matches/{job_id}")
        assert completed_resp.status_code == 200
        comp_data = completed_resp.json()
        assert comp_data["status"] == "completed"
        assert comp_data["result"] is not None
        assert comp_data["result"]["overall_matches"][0]["name"] == "Brad Pitt"

    finally:
        app.dependency_overrides.clear()


def test_poll_failed_job_domain_error(client, sample_image_bytes, test_queue_manager, monkeypatch):
    mock_db = MagicMock()
    app.dependency_overrides[get_db] = lambda: mock_db
    monkeypatch.setattr("app.routers.matching.job_queue_manager", test_queue_manager)

    try:
        no_face_bytes = sample_image_bytes + b"_TRIGGER_NO_FACE"

        # 1. Enqueue job with trigger
        response = client.post(
            "/api/v1/matches?async_mode=true",
            files={"file": ("noface.jpg", no_face_bytes, "image/jpeg")},
            data={"target_gender": "male", "target_origin": "bollywood"}
        )
        assert response.status_code == 202
        job_id = response.json()["job_id"]

        # 2. Worker processes job
        test_queue_manager.process_next_job(db=mock_db)

        # 3. Poll failed job status
        failed_resp = client.get(f"/api/v1/matches/{job_id}")
        assert failed_resp.status_code == 200
        data = failed_resp.json()
        assert data["status"] == "failed"
        assert data["error_code"] == "NO_FACE"

    finally:
        app.dependency_overrides.clear()


def test_poll_non_existent_or_expired_job(client, test_queue_manager, monkeypatch):
    monkeypatch.setattr("app.routers.matching.job_queue_manager", test_queue_manager)

    response = client.get("/api/v1/matches/job_non_existent_999")
    assert response.status_code == 404
    data = response.json()
    assert "error" in data["detail"]


def test_queue_bounding_and_503_full_error(client, sample_image_bytes, test_queue_manager, monkeypatch):
    monkeypatch.setattr("app.routers.matching.job_queue_manager", test_queue_manager)
    monkeypatch.setattr(settings, "MAX_QUEUE_CAPACITY", 2)

    # Fill queue to capacity (2 jobs)
    test_queue_manager.enqueue_job(sample_image_bytes, "p1.jpg", target_gender="male", target_origin="bollywood")
    test_queue_manager.enqueue_job(sample_image_bytes, "p2.jpg", target_gender="male", target_origin="bollywood")

    # 3rd job exceeds capacity
    response = client.post(
        "/api/v1/matches?async_mode=true",
        files={"file": ("p3.jpg", sample_image_bytes, "image/jpeg")},
        data={"target_gender": "male", "target_origin": "bollywood"}
    )
    assert response.status_code == 503
    data = response.json()
    assert data["error"] == "QUEUE_FULL"


def test_queue_metrics_endpoint(client, sample_image_bytes, test_queue_manager, monkeypatch):
    monkeypatch.setattr("app.routers.matching.job_queue_manager", test_queue_manager)

    test_queue_manager.enqueue_job(sample_image_bytes, "p1.jpg")

    response = client.get("/api/v1/matches/queue/metrics")
    assert response.status_code == 200
    metrics = response.json()
    assert metrics["queued_jobs"] >= 1
    assert "queue_capacity" in metrics
