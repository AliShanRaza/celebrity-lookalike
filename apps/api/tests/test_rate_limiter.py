import pytest
from unittest.mock import MagicMock
from fastapi import HTTPException
import fakeredis

from app.main import app
from app.db import get_db
from app.abuse_config import abuse_config
from app.services.privacy import hash_client_identifier
from app.services.job_queue import JobQueueManager
from app.services.rate_limiter import RateLimiterService


@pytest.fixture
def fake_redis():
    return fakeredis.FakeRedis()


@pytest.fixture
def test_queue_mgr(fake_redis):
    return JobQueueManager(redis_client=fake_redis)


@pytest.fixture
def rate_limiter(test_queue_mgr):
    return RateLimiterService(job_queue_manager=test_queue_mgr)


def test_privacy_conscious_ip_hashing():
    ip = "192.168.1.50"
    session = "session_xyz123"

    hash_1 = hash_client_identifier(ip_address=ip, session_token=session)
    hash_2 = hash_client_identifier(ip_address=ip, session_token=session)

    # 1. Deterministic hashing output
    assert hash_1 == hash_2
    # 2. Never contains raw IP string in output
    assert ip not in hash_1
    assert "client_hash:" in hash_1


def test_rate_limiting_exceeded(rate_limiter, monkeypatch):
    client_hash = "client_hash_test_rate_limit"
    monkeypatch.setattr(abuse_config, "RATE_LIMIT_REQUESTS_PER_MINUTE", 3)

    # First 3 requests succeed
    rate_limiter.enforce_rate_limits(client_hash)
    rate_limiter.enforce_rate_limits(client_hash)
    rate_limiter.enforce_rate_limits(client_hash)

    # 4th request exceeds rate limit (429)
    with pytest.raises(HTTPException) as exc_info:
        rate_limiter.enforce_rate_limits(client_hash)

    assert exc_info.value.status_code == 429
    assert exc_info.value.detail["error"] == "RATE_LIMIT_EXCEEDED"


def test_concurrent_active_job_limits(rate_limiter, test_queue_mgr, sample_image_bytes, monkeypatch):
    client_hash = "client_hash_test_concurrent"
    monkeypatch.setattr(abuse_config, "MAX_CONCURRENT_JOBS_PER_CLIENT", 2)

    # Enqueue 2 active jobs for client
    job_1 = test_queue_mgr.enqueue_job(sample_image_bytes, "img1.jpg")
    job_2 = test_queue_mgr.enqueue_job(sample_image_bytes, "img2.jpg")

    rate_limiter.register_client_job(client_hash, job_1.job_id)
    rate_limiter.register_client_job(client_hash, job_2.job_id)

    # Requesting a 3rd job while 2 are active triggers concurrent limit (429)
    with pytest.raises(HTTPException) as exc_info:
        rate_limiter.enforce_rate_limits(client_hash)

    assert exc_info.value.status_code == 429
    assert exc_info.value.detail["error"] == "CONCURRENT_JOB_LIMIT_EXCEEDED"


def test_blocked_client_hash(rate_limiter, monkeypatch):
    blocked_hash = "client_hash_malicious_bot"
    monkeypatch.setattr(abuse_config, "BLOCKED_CLIENT_HASHES", {blocked_hash})

    with pytest.raises(HTTPException) as exc_info:
        rate_limiter.enforce_rate_limits(blocked_hash)

    assert exc_info.value.status_code == 403
    assert exc_info.value.detail["error"] == "CLIENT_BLOCKED"


def test_rate_limit_integration_via_client(client, sample_image_bytes, monkeypatch):
    mock_db = MagicMock()
    app.dependency_overrides[get_db] = lambda: mock_db
    monkeypatch.setattr(abuse_config, "RATE_LIMIT_REQUESTS_PER_MINUTE", 2)

    monkeypatch.setattr(
        "app.repositories.celebrity_repository.CelebrityRepository.search_nearest_embeddings",
        lambda session, query_vector, model_version, target_gender=None, target_origin=None, limit=50, active_only=True: []
    )

    # Use unique session token header to isolate counter
    headers = {"X-Session-Token": "test_isolated_session_999"}

    try:
        # Request 1 & 2 succeed (HTTP 200)
        res1 = client.post(
            "/api/v1/matches",
            files={"file": ("p1.jpg", sample_image_bytes, "image/jpeg")},
            data={"target_gender": "male", "target_origin": "bollywood"},
            headers=headers
        )
        res2 = client.post(
            "/api/v1/matches",
            files={"file": ("p2.jpg", sample_image_bytes, "image/jpeg")},
            data={"target_gender": "male", "target_origin": "bollywood"},
            headers=headers
        )
        assert res1.status_code == 200
        assert res2.status_code == 200

        # 3rd match request exceeds limit (HTTP 429)
        res3 = client.post(
            "/api/v1/matches",
            files={"file": ("p3.jpg", sample_image_bytes, "image/jpeg")},
            data={"target_gender": "male", "target_origin": "bollywood"},
            headers=headers
        )
        assert res3.status_code == 429
        assert res3.json()["detail"]["error"] == "RATE_LIMIT_EXCEEDED"
    finally:
        app.dependency_overrides.clear()
