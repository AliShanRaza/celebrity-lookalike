from typing import List, Optional
from pydantic import BaseModel, Field


class CelebrityMatchResult(BaseModel):
    celebrity_id: str = Field(..., description="Unique UUID of the celebrity")
    name: str = Field(..., description="Full name of the celebrity")
    gender: str = Field(..., description="Gender metadata ('male', 'female', 'non_binary')")
    resemblance_score: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Calibrated entertainment resemblance score (percentage 0-100%). NOT identity probability."
    )
    sample_image_url: str = Field(..., description="URL of reference image with closest match")
    bio: Optional[str] = Field(None, description="Brief celebrity bio")


class MatchResponse(BaseModel):
    model_version: str = Field(..., description="Recognition model version used for matching")
    overall_matches: List[CelebrityMatchResult] = Field(..., description="Top overall celebrity matches")
    male_matches: List[CelebrityMatchResult] = Field(..., description="Top male celebrity matches")
    female_matches: List[CelebrityMatchResult] = Field(..., description="Top female celebrity matches")


class ImageValidationError(BaseModel):
    detail: str
    error_code: str  # e.g., NO_FACE_DETECTED, MULTIPLE_FACES_DETECTED, INVALID_IMAGE_CONTENT
