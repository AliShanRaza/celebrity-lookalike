import logging
from typing import Optional
from fastapi import HTTPException, status
import redis

from app.abuse_config import abuse_config
from app.services.job_queue import JobQueueManager

logger = logging.getLogger(__name__)


class RateLimiterService:
    """
    Rate limiting & abuse prevention service.
    Enforces privacy-conscious hashed IP/session sliding window rate limits,
    concurrent active job limits per client, and blocked hash lists.
    """

    def __init__(self, job_queue_manager: Optional[JobQueueManager] = None):
        self.job_queue = job_queue_manager or JobQueueManager()
        self.redis = self.job_queue.redis

    def enforce_rate_limits(self, client_hash: str) -> None:
        """
        Enforces rate limits and concurrent job limits for a hashed client identifier.
        Raises HTTP 429 if limits are exceeded or HTTP 403 if client is blocked.
        """
        # 1. Check blocked hash list
        if client_hash in abuse_config.BLOCKED_CLIENT_HASHES:
            logger.warning(f"Abuse Mitigation: Blocked client hash '{client_hash}' attempted request.")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": "CLIENT_BLOCKED",
                    "message": "Access restricted due to automated abuse policy."
                }
            )

        # 2. Enforce sliding window rate limit per minute
        rate_key = f"ratelimit:{client_hash}"
        current_requests = self.redis.incr(rate_key)
        if current_requests == 1:
            self.redis.expire(rate_key, 60) # 1 minute window

        if current_requests > abuse_config.RATE_LIMIT_REQUESTS_PER_MINUTE:
            logger.warning(f"Rate limit exceeded for client '{client_hash}' ({current_requests}/{abuse_config.RATE_LIMIT_REQUESTS_PER_MINUTE} req/min).")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "error": "RATE_LIMIT_EXCEEDED",
                    "message": f"Rate limit exceeded ({abuse_config.RATE_LIMIT_REQUESTS_PER_MINUTE} requests/min). Please try again shortly."
                }
            )

        # 3. Enforce maximum concurrent active jobs per client
        active_jobs = self._count_active_jobs_for_client(client_hash)
        if active_jobs >= abuse_config.MAX_CONCURRENT_JOBS_PER_CLIENT:
            logger.warning(f"Concurrent job limit exceeded for client '{client_hash}' ({active_jobs} active jobs).")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "error": "CONCURRENT_JOB_LIMIT_EXCEEDED",
                    "message": f"Maximum concurrent active jobs limit ({abuse_config.MAX_CONCURRENT_JOBS_PER_CLIENT}) reached. Please wait for current jobs to finish."
                }
            )

    def register_client_job(self, client_hash: str, job_id: str) -> None:
        """Associates active job_id with hashed client identifier."""
        client_jobs_key = f"client_active_jobs:{client_hash}"
        self.redis.sadd(client_jobs_key, job_id)
        self.redis.expire(client_jobs_key, 600)

    def _count_active_jobs_for_client(self, client_hash: str) -> int:
        """Counts queued or processing active jobs for a hashed client identifier."""
        client_jobs_key = f"client_active_jobs:{client_hash}"
        job_ids = self.redis.smembers(client_jobs_key)
        if not job_ids:
            return 0

        active_count = 0
        stale_jobs = []
        for j_id_bytes in job_ids:
            j_id = j_id_bytes.decode("utf-8") if isinstance(j_id_bytes, bytes) else j_id_bytes
            status_val = self.redis.hget(f"job:{j_id}", "status")
            if status_val:
                st = status_val.decode("utf-8") if isinstance(status_val, bytes) else status_val
                if st in ("queued", "processing"):
                    active_count += 1
                else:
                    stale_jobs.append(j_id)
            else:
                stale_jobs.append(j_id)

        if stale_jobs:
            self.redis.srem(client_jobs_key, *stale_jobs)

        return active_count
