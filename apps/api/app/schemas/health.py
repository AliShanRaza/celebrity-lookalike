from typing import Dict, Any, Optional
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = Field(..., description="Service health status ('healthy', 'degraded')")
    database: str = Field(..., description="Database connection status ('connected', 'disconnected')")
    environment: str = Field(..., description="Runtime deployment environment")
    build_sha: str = Field(..., description="Git commit / build SHA identifier")
    model_version: str = Field(..., description="Active recognition model version")
    index_version: str = Field(..., description="Vector database index version")
    score_version: str = Field(..., description="Resemblance score calibrator version")
    metrics: Optional[Dict[str, Any]] = Field(None, description="Structured operational metrics summary")


class VersionResponse(BaseModel):
    app_version: str = Field(..., description="Application semantic version")
    build_sha: str = Field(..., description="Git commit / build SHA identifier")
    recognition_provider: str = Field(..., description="Configured recognition provider ('fake', 'real')")
    model_version: str = Field(..., description="Active recognition model version")
    index_version: str = Field(..., description="Vector database index version")
    score_version: str = Field(..., description="Resemblance score calibrator version")
    embedding_dimension: int = Field(..., description="Model vector embedding dimension")
    total_celebrities: Optional[int] = Field(300, description="Total verified reference celebrities count")
    bollywood_celebrities: Optional[int] = Field(100, description="Bollywood dataset celebrities count")
    hollywood_celebrities: Optional[int] = Field(200, description="Hollywood dataset celebrities count")