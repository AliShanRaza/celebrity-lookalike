from datetime import datetime, timezone
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field

from app.schemas.matching import MatchResultResponse


class JobStatusEnum(str, Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    EXPIRED = "expired"


class JobAsyncResponse(BaseModel):
    job_id: str = Field(..., description="Unique background job identifier")
    status: JobStatusEnum = Field(JobStatusEnum.QUEUED, description="Current job processing status")
    poll_url: str = Field(..., description="API URL endpoint to poll job status and results")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class JobStatusResponse(BaseModel):
    job_id: str = Field(..., description="Unique background job identifier")
    status: JobStatusEnum = Field(..., description="Current job status (queued, processing, completed, failed, expired)")
    result: Optional[MatchResultResponse] = Field(None, description="Match results payload upon completion")
    error_code: Optional[str] = Field(None, description="Typed error code if job failed")
    error_message: Optional[str] = Field(None, description="User-facing error message if job failed")
    created_at: datetime = Field(...)
    updated_at: datetime = Field(...)
    ttl_seconds: Optional[int] = Field(None, description="Remaining seconds until result expiration")


class QueueMetricsResponse(BaseModel):
    queued_jobs: int = Field(..., description="Number of jobs currently waiting in queue")
    processing_jobs: int = Field(..., description="Number of jobs currently being processed by workers")
    completed_jobs: int = Field(..., description="Number of successfully completed jobs")
    failed_jobs: int = Field(..., description="Number of failed jobs")
    queue_capacity: int = Field(..., description="Maximum allowed queue capacity")
