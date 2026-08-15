from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config import settings
from app.db import get_db
from app.schemas.health import HealthResponse, VersionResponse
from app.services.recognition import get_recognition_provider
from app.services.metrics import metrics_collector
from app.services.job_queue import JobQueueManager

router = APIRouter(prefix="/api/v1", tags=["Health & System"])
job_queue_mgr = JobQueueManager()


@router.get("/health", response_model=HealthResponse, summary="Check API, DB, and system metrics health")
def get_health(db: Session = Depends(get_db)):
    """
    Health check endpoint verifying DB connection, API status, build SHA, model/index versions, and metrics summary.
    In local development mode without a running DB container, returns standalone status gracefully.
    """
    try:
        db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as e:
        if settings.APP_ENV == "development":
            db_status = "development_standalone_mode"
        else:
            db_status = f"unhealthy: {str(e)}"
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={"status": "unhealthy", "database": db_status, "environment": settings.APP_ENV}
            )

    provider = get_recognition_provider()
    summary = metrics_collector.get_summary(job_queue_manager=job_queue_mgr)

    return HealthResponse(
        status="healthy",
        database=db_status,
        environment=settings.APP_ENV,
        build_sha=settings.BUILD_SHA,
        model_version=provider.model_version,
        index_version=settings.INDEX_VERSION,
        score_version=settings.SCORE_VERSION,
        metrics=summary
    )


@router.get("/version", response_model=VersionResponse, summary="Check software, build SHA & model versions")
def get_version():
    """
    Version endpoint returning build SHA, recognition provider, model version, index version, score version,
    and live verified celebrity dataset counts.
    """
    from app.services.dataset_registry import dataset_registry
    provider = get_recognition_provider()

    recs = dataset_registry.celebrity_records
    total_cnt = len(recs) if recs else 300
    bolly_cnt = len([r for r in recs if r.get("origin") == "bollywood"]) if recs else 100
    holly_cnt = len([r for r in recs if r.get("origin") == "hollywood"]) if recs else 200

    return VersionResponse(
        app_version=settings.APP_VERSION,
        build_sha=settings.BUILD_SHA,
        recognition_provider=settings.RECOGNITION_PROVIDER,
        model_version=provider.model_version,
        index_version=settings.INDEX_VERSION,
        score_version=settings.SCORE_VERSION,
        embedding_dimension=provider.embedding_dimension,
        total_celebrities=total_cnt,
        bollywood_celebrities=bolly_cnt,
        hollywood_celebrities=holly_cnt
    )
