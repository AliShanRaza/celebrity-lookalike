import time
import logging
from typing import Dict, Any, Optional
from collections import defaultdict
from app.config import settings

logger = logging.getLogger(__name__)


class MetricsCollector:
    """
    In-memory metrics collector tracking request counts, face validation outcomes,
    inference duration, vector search duration, job failure codes, and transient file
    deletion outcomes. Absolutely zero biometric or user image content is tracked.
    """

    def __init__(self):
        self.request_counts: Dict[str, int] = defaultdict(int)
        self.face_validation_outcomes: Dict[str, int] = defaultdict(int)
        self.job_failure_codes: Dict[str, int] = defaultdict(int)
        self.transient_deletion_outcomes: Dict[str, int] = defaultdict(int)

        self._inference_count: int = 0
        self._inference_total_ms: float = 0.0

        self._vector_search_count: int = 0
        self._vector_search_total_ms: float = 0.0

    def record_request(self, endpoint: str, status_code: int) -> None:
        key = f"{endpoint}:{status_code}"
        self.request_counts[key] += 1

    def record_face_validation(self, outcome: str) -> None:
        self.face_validation_outcomes[outcome.lower()] += 1

    def record_inference_duration(self, duration_ms: float) -> None:
        self._inference_count += 1
        self._inference_total_ms += duration_ms

    def record_vector_search_duration(self, duration_ms: float) -> None:
        self._vector_search_count += 1
        self._vector_search_total_ms += duration_ms

    def record_job_failure(self, error_code: str) -> None:
        self.job_failure_codes[error_code] += 1

    def record_transient_deletion(self, success: bool) -> None:
        outcome = "success" if success else "failure"
        self.transient_deletion_outcomes[outcome] += 1

    def get_summary(self, job_queue_manager: Optional[Any] = None) -> Dict[str, Any]:
        """Returns structured metrics summary."""
        avg_inf = (self._inference_total_ms / self._inference_count) if self._inference_count > 0 else 0.0
        avg_vec = (self._vector_search_total_ms / self._vector_search_count) if self._vector_search_count > 0 else 0.0

        queue_metrics: Dict[str, Any] = {
            "queue_depth": 0,
            "oldest_job_age_seconds": 0.0
        }

        if job_queue_manager:
            try:
                qm = job_queue_manager.get_queue_metrics()
                queue_metrics["queue_depth"] = qm.queued_jobs
                # Compute oldest job age if queued jobs exist
                oldest_age = 0.0
                queue_ids = job_queue_manager.redis.lrange("job_queue", 0, 0)
                if queue_ids:
                    first_id = queue_ids[0].decode("utf-8") if isinstance(queue_ids[0], bytes) else queue_ids[0]
                    created_at_str = job_queue_manager.redis.hget(f"job:{first_id}", "created_at")
                    if created_at_str:
                        from datetime import datetime, timezone
                        c_str = created_at_str.decode("utf-8") if isinstance(created_at_str, bytes) else created_at_str
                        created_dt = datetime.fromisoformat(c_str)
                        oldest_age = max(0.0, (datetime.now(timezone.utc) - created_dt).total_seconds())
                queue_metrics["oldest_job_age_seconds"] = round(oldest_age, 2)
            except Exception as e:
                logger.warning(f"Could not compute queue metrics: {str(e)}")

        return {
            "requests": dict(self.request_counts),
            "face_validation_outcomes": dict(self.face_validation_outcomes),
            "inference_duration": {
                "count": self._inference_count,
                "total_ms": round(self._inference_total_ms, 2),
                "avg_ms": round(avg_inf, 2)
            },
            "vector_search_duration": {
                "count": self._vector_search_count,
                "total_ms": round(self._vector_search_total_ms, 2),
                "avg_ms": round(avg_vec, 2)
            },
            "queue_metrics": queue_metrics,
            "job_failure_codes": dict(self.job_failure_codes),
            "transient_deletion_outcomes": dict(self.transient_deletion_outcomes)
        }


# Global Metrics Collector Singleton
metrics_collector = MetricsCollector()
