import json
import logging
import time
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from uuid import uuid4

import fakeredis
import redis
from sqlalchemy.orm import Session

from app.config import settings
from app.schemas.jobs import (
    JobStatusEnum,
    JobAsyncResponse,
    JobStatusResponse,
    QueueMetricsResponse,
)
from app.schemas.matching import MatchResultResponse
from app.services.image_intake import SecureImageIntakeService
from app.services.recognition import get_recognition_provider
from app.services.recognition.base import FaceDetectionError, InvalidImageError
from app.services.matching import MatchingService

logger = logging.getLogger(__name__)


class QueueFullError(Exception):
    """Raised when the job queue exceeds maximum capacity."""
    def __init__(self, message: str = "Job queue is full. Please try again shortly."):
        super().__init__(message)


class JobQueueManager:
    """
    Asynchronous job queue manager for background portrait processing.
    Uses Redis (or Fakeredis for testing/development).
    Supports queue bounding, TTL expiration, retry policies, and metrics.
    """

    def __init__(self, redis_client: Optional[redis.Redis] = None):
        if redis_client is not None:
            self.redis = redis_client
        else:
            # Fallback to Fakeredis in testing/local dev if Redis daemon is not reachable
            try:
                client = redis.Redis.from_url(settings.REDIS_URL, socket_timeout=1.0)
                client.ping()
                self.redis = client
            except Exception:
                logger.info("Local Redis daemon not reached. Utilizing in-memory Fakeredis client.")
                self.redis = fakeredis.FakeRedis()

    def enqueue_job(self, image_bytes: bytes, filename_hint: str = "upload.jpg", target_gender: str = "male", target_origin: str = "bollywood") -> JobAsyncResponse:
        """
        Enqueues a background matching job.
        Raises QueueFullError if queue size exceeds MAX_QUEUE_CAPACITY.
        """
        queue_len = self.redis.llen("job_queue")
        if queue_len >= settings.MAX_QUEUE_CAPACITY:
            logger.warning(f"Queue rejected job: Current depth {queue_len} >= capacity {settings.MAX_QUEUE_CAPACITY}.")
            raise QueueFullError("Job queue is full. Please try again shortly.")

        job_id = f"job_{uuid4().hex}"
        now_str = datetime.now(timezone.utc).isoformat()

        # Save transient upload bytes & initial metadata in Redis with TTL
        job_data = {
            "job_id": job_id,
            "status": JobStatusEnum.QUEUED.value,
            "filename_hint": filename_hint,
            "target_gender": target_gender,
            "target_origin": target_origin,
            "image_bytes_hex": image_bytes.hex(),
            "created_at": now_str,
            "updated_at": now_str,
            "retry_count": 0,
            "error_code": "",
            "error_message": "",
            "result_json": ""
        }

        # Store job hash with TTL
        self.redis.hset(f"job:{job_id}", mapping=job_data)
        self.redis.expire(f"job:{job_id}", settings.JOB_RESULT_TTL_SECONDS)

        # Push to work queue
        self.redis.rpush("job_queue", job_id)

        # Track metrics
        self.redis.incr("metrics:queued_count")

        poll_url = f"/api/v1/matches/{job_id}"
        logger.info(f"Enqueued job '{job_id}' (Queue Depth: {queue_len + 1}/{settings.MAX_QUEUE_CAPACITY}).")

        return JobAsyncResponse(
            job_id=job_id,
            status=JobStatusEnum.QUEUED,
            poll_url=poll_url
        )

    def get_job_status(self, job_id: str) -> Optional[JobStatusResponse]:
        """
        Retrieves status, results, and TTL for a given job_id.
        Returns None if job does not exist or has expired.
        """
        job_key = f"job:{job_id}"
        job_data = self.redis.hgetall(job_key)

        if not job_data:
            return None

        # Decode bytes from Redis
        decoded = {k.decode("utf-8") if isinstance(k, bytes) else k: v.decode("utf-8") if isinstance(v, bytes) else v for k, v in job_data.items()}

        status_str = decoded.get("status", JobStatusEnum.EXPIRED.value)
        status = JobStatusEnum(status_str)

        result: Optional[MatchResultResponse] = None
        if decoded.get("result_json"):
            try:
                result = MatchResultResponse.model_validate_json(decoded["result_json"])
            except Exception:
                result = None

        ttl = self.redis.ttl(job_key)

        return JobStatusResponse(
            job_id=job_id,
            status=status,
            result=result,
            error_code=decoded.get("error_code") or None,
            error_message=decoded.get("error_message") or None,
            created_at=datetime.fromisoformat(decoded["created_at"]),
            updated_at=datetime.fromisoformat(decoded["updated_at"]),
            ttl_seconds=ttl if ttl > 0 else 0
        )

    def process_next_job(self, db: Session) -> Optional[str]:
        """
        Processes next job from the queue.
        Retries transient failures up to MAX_TRANSIENT_RETRIES.
        Does NOT retry deterministic domain errors (e.g. NO_FACE, MULTIPLE_FACES).
        Expiring results after TTL.
        """
        job_id_bytes = self.redis.lpop("job_queue")
        if not job_id_bytes:
            return None

        job_id = job_id_bytes.decode("utf-8") if isinstance(job_id_bytes, bytes) else job_id_bytes
        job_key = f"job:{job_id}"

        job_data = self.redis.hgetall(job_key)
        if not job_data:
            return None

        decoded = {k.decode("utf-8") if isinstance(k, bytes) else k: v.decode("utf-8") if isinstance(v, bytes) else v for k, v in job_data.items()}
        retry_count = int(decoded.get("retry_count", 0))

        # Update status to processing
        now_str = datetime.now(timezone.utc).isoformat()
        self.redis.hset(job_key, mapping={"status": JobStatusEnum.PROCESSING.value, "updated_at": now_str})
        self.redis.incr("metrics:processing_count")

        try:
            image_bytes = bytes.fromhex(decoded["image_bytes_hex"])
            filename_hint = decoded.get("filename_hint", "upload.jpg")

            # 1. Secure Image Intake
            processed_bytes, _ = SecureImageIntakeService.process_image_bytes(image_bytes, filename_hint=filename_hint)

            # 2. Recognition Provider
            provider = get_recognition_provider()
            aligned_crop_bytes = provider.validate_and_align(processed_bytes)
            user_embedding = provider.generate_embedding(aligned_crop_bytes)

            target_gender = decoded.get("target_gender", "male")
            target_origin = decoded.get("target_origin", "bollywood")

            # 3. Matching Service
            matching_service = MatchingService(db=db)
            match_result = matching_service.find_matches(
                query_embedding=user_embedding,
                model_version=provider.model_version,
                target_gender=target_gender,
                target_origin=target_origin,
                request_id=job_id
            )

            # Mark completed & store result json
            done_str = datetime.now(timezone.utc).isoformat()
            self.redis.hset(job_key, mapping={
                "status": JobStatusEnum.COMPLETED.value,
                "result_json": match_result.model_dump_json(),
                "image_bytes_hex": "", # Delete transient raw upload bytes immediately upon success
                "updated_at": done_str
            })
            self.redis.expire(job_key, settings.JOB_RESULT_TTL_SECONDS)
            self.redis.incr("metrics:completed_count")
            logger.info(f"Successfully completed background job '{job_id}'.")
            return job_id

        except FaceDetectionError as fde:
            # Deterministic domain error: do NOT retry
            fail_str = datetime.now(timezone.utc).isoformat()
            self.redis.hset(job_key, mapping={
                "status": JobStatusEnum.FAILED.value,
                "error_code": fde.error_code,
                "error_message": fde.message,
                "image_bytes_hex": "", # Delete transient raw upload bytes on failure
                "updated_at": fail_str
            })
            self.redis.expire(job_key, settings.JOB_RESULT_TTL_SECONDS)
            self.redis.incr("metrics:failed_count")
            logger.warning(f"Background job '{job_id}' failed with domain error: {fde.error_code} - {fde.message}")
            return job_id

        except Exception as exc:
            # Transient error: retry if retry_count < MAX_TRANSIENT_RETRIES
            if retry_count < settings.MAX_TRANSIENT_RETRIES:
                retry_count += 1
                logger.warning(f"Transient failure in job '{job_id}' (Retry {retry_count}/{settings.MAX_TRANSIENT_RETRIES}): {str(exc)}")
                self.redis.hset(job_key, mapping={"retry_count": retry_count, "status": JobStatusEnum.QUEUED.value})
                self.redis.rpush("job_queue", job_id)
            else:
                fail_str = datetime.now(timezone.utc).isoformat()
                self.redis.hset(job_key, mapping={
                    "status": JobStatusEnum.FAILED.value,
                    "error_code": "TRANSIENT_RETRY_EXHAUSTED",
                    "error_message": f"Job failed after {retry_count} retries: {str(exc)}",
                    "image_bytes_hex": "",
                    "updated_at": fail_str
                })
                self.redis.expire(job_key, settings.JOB_RESULT_TTL_SECONDS)
                self.redis.incr("metrics:failed_count")
                logger.error(f"Background job '{job_id}' failed after exhausting retries.")
            return job_id

    def get_queue_metrics(self) -> QueueMetricsResponse:
        """Returns current queue metrics."""
        queued = self.redis.llen("job_queue")
        completed = int(self.redis.get("metrics:completed_count") or 0)
        failed = int(self.redis.get("metrics:failed_count") or 0)
        processing = int(self.redis.get("metrics:processing_count") or 0)

        return QueueMetricsResponse(
            queued_jobs=queued,
            processing_jobs=processing,
            completed_jobs=completed,
            failed_jobs=failed,
            queue_capacity=settings.MAX_QUEUE_CAPACITY
        )
