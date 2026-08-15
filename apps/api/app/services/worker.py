import time
import logging

from app.db import SessionLocal
from app.services.job_queue import JobQueueManager

logger = logging.getLogger("celebrity_lookalike_worker")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")


def run_worker_loop():
    """Worker daemon entrypoint processing background matching jobs continuously."""
    logger.info("Celebrity Look-Alike Background Worker Service Started.")
    queue_manager = JobQueueManager()

    while True:
        db = SessionLocal()
        try:
            processed_job_id = queue_manager.process_next_job(db=db)
            if not processed_job_id:
                time.sleep(0.5) # Sleep briefly if queue is empty
        except Exception as e:
            logger.error(f"Worker unhandled error in loop: {str(e)}")
            time.sleep(1.0)
        finally:
            db.close()


if __name__ == "__main__":
    run_worker_loop()
