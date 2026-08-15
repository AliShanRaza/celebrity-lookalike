from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID, uuid4
from pydantic import BaseModel, Field


class CelebrityMatchItem(BaseModel):
    celebrity_id: UUID = Field(..., description="Unique UUID of matched celebrity")
    name: str = Field(..., description="Celebrity display name")
    gender: str = Field(..., description="Gender metadata ('male', 'female', 'non_binary')")
    origin: str = Field("bollywood", description="Origin metadata ('bollywood', 'hollywood')")
    image_url: str = Field(..., description="Reference image URL")
    resemblance_score: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Calibrated entertainment resemblance score [0%, 100%]"
    )
    bio: Optional[str] = Field(None, description="Optional brief celebrity bio")


class LandmarkPoint(BaseModel):
    x: float = Field(..., description="Normalized X coordinate [0.0, 1.0]")
    y: float = Field(..., description="Normalized Y coordinate [0.0, 1.0]")


class FacialLandmarks(BaseModel):
    eyebrows: List[LandmarkPoint] = Field(default_factory=list, description="Eyebrow landmark keypoints")
    left_eye: List[LandmarkPoint] = Field(default_factory=list, description="Left eye landmark keypoints")
    right_eye: List[LandmarkPoint] = Field(default_factory=list, description="Right eye landmark keypoints")
    nose: List[LandmarkPoint] = Field(default_factory=list, description="Nose bridge and tip landmark keypoints")
    mouth: List[LandmarkPoint] = Field(default_factory=list, description="Mouth/lips landmark keypoints")
    contour: List[LandmarkPoint] = Field(default_factory=list, description="Face contour/jawline landmark keypoints")


class BestPairMatches(BaseModel):
    male_match: Optional[CelebrityMatchItem] = Field(None, description="Top male celebrity match")
    female_match: Optional[CelebrityMatchItem] = Field(None, description="Top female celebrity match")
    pair_score: float = Field(0.0, ge=0.0, le=100.0, description="Combined best pair resemblance score")


class MatchResultResponse(BaseModel):
    request_id: str = Field(default_factory=lambda: str(uuid4()), description="Unique request tracing ID")
    model_version: str = Field(..., description="Recognition model version used for feature extraction")
    score_version: str = Field(..., description="Calibrator type identifier used for score calculation")
    detected_gender: Optional[str] = Field("female", description="Detected facial gender ('female', 'male')")
    primary_target_gender: Optional[str] = Field(None, description="Requested target gender filter ('female', 'male', 'all')")
    primary_target_origin: Optional[str] = Field(None, description="Requested target origin filter ('bollywood', 'hollywood')")
    landmarks: Optional[FacialLandmarks] = Field(None, description="Detected facial landmark keypoints (eyebrows, eyes, nose, mouth, contour)")
    best_pair: Optional[BestPairMatches] = Field(None, description="Best pair pairing top male and female look-alikes")
    male_matches: List[CelebrityMatchItem] = Field(
        default_factory=list,
        description="Top celebrity matches filtered for male gender"
    )
    female_matches: List[CelebrityMatchItem] = Field(
        default_factory=list,
        description="Top celebrity matches filtered for female gender"
    )
    overall_matches: List[CelebrityMatchItem] = Field(
        default_factory=list,
        description="Top celebrity matches across all genders"
    )
    processed_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp of resemblance calculation"
    )

