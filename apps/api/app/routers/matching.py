import os
from typing import Optional, Union
from uuid import uuid4
from fastapi import APIRouter, Depends, File, Form, Header, Query, Request, UploadFile, status, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas.matching import MatchResultResponse
from app.schemas.jobs import JobAsyncResponse, JobStatusResponse, QueueMetricsResponse
from app.services.image_intake import SecureImageIntakeService
from app.services.url_intake import SecureURLIntakeService
from app.services.recognition import get_recognition_provider
from app.services.matching import MatchingService
from app.services.job_queue import JobQueueManager, QueueFullError
from app.services.privacy import hash_client_identifier
from app.services.rate_limiter import RateLimiterService
from app.services.recognition.base import InvalidImageError

router = APIRouter(prefix="/api/v1", tags=["Matching Engine"])

# Singleton Services
job_queue_manager = JobQueueManager()
rate_limiter_service = RateLimiterService(job_queue_manager=job_queue_manager)


@router.get(
    "/images/serve",
    summary="Serve local reference celebrity dataset images"
)
def serve_celebrity_image(path: str):
    """
    Safely serves local dataset image files for rendering on the web client.
    """
    candidates = [
        path,
        os.path.abspath(path),
        os.path.join(os.getcwd(), path),
        os.path.join(os.getcwd(), "apps", "api", path)
    ]
    for candidate in candidates:
        if os.path.exists(candidate) and os.path.isfile(candidate):
            return FileResponse(candidate)

    # Fallback to fuzzy match folder under data/images
    folder_name = os.path.basename(os.path.dirname(path))
    img_file = os.path.basename(path)
    data_img_dir = os.path.join(os.getcwd(), "data", "images")
    if os.path.exists(data_img_dir):
        for sd in os.listdir(data_img_dir):
            if sd.encode("ascii", "ignore") == folder_name.encode("ascii", "ignore"):
                candidate = os.path.join(data_img_dir, sd, img_file)
                if os.path.exists(candidate):
                    return FileResponse(candidate)

    raise HTTPException(status_code=404, detail=f"Image file not found at path '{path}'.")


@router.post(
    "/matches",
    response_model=Union[MatchResultResponse, JobAsyncResponse],
    status_code=status.HTTP_200_OK,
    summary="Upload portrait photo or URL for synchronous or asynchronous celebrity look-alike search"
)
async def find_celebrity_matches(
    request: Request,
    file: Optional[UploadFile] = File(None, description="Uploaded user portrait photo (JPEG, PNG, WebP)"),
    image_url: Optional[str] = Form(None, description="Optional SSRF-protected image URL"),
    target_gender: Optional[str] = Form(None, description="Required target gender filter ('female', 'male')"),
    target_origin: Optional[str] = Form(None, description="Required target origin filter ('bollywood', 'hollywood')"),
    async_mode: bool = Query(False, description="Set to true to process job asynchronously in background queue"),
    x_session_token: Optional[str] = Header(None, alias="X-Session-Token"),
    db: Session = Depends(get_db)
):
    """
    Dual-mode celebrity match endpoint:
    - Synchronous Mode (async_mode=false): Processes request immediately and returns MatchResultResponse (HTTP 200).
    - Asynchronous Mode (async_mode=true): Enqueues job into background queue and returns JobAsyncResponse (HTTP 202).
    - Enforces privacy-conscious hashed rate limiting and active concurrent job limits per client.
    """
    # Target gender requirement check
    tg_clean = (target_gender or "").strip().lower()
    if not tg_clean or tg_clean not in ("male", "female"):
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "error": "MISSING_TARGET_GENDER" if not tg_clean else "INVALID_TARGET_GENDER",
                "message": "Field 'target_gender' is required and must be either 'male' or 'female'."
            }
        )

    # Target origin requirement check
    to_clean = (target_origin or "").strip().lower()
    if not to_clean or to_clean not in ("bollywood", "hollywood"):
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "error": "MISSING_TARGET_ORIGIN" if not to_clean else "INVALID_TARGET_ORIGIN",
                "message": "Field 'target_origin' is required and must be either 'bollywood' or 'hollywood'."
            }
        )

    request_id = str(uuid4())

    # Step 0: Privacy-conscious client hashing & rate limiting
    client_ip = request.client.host if request.client else "127.0.0.1"
    client_hash = hash_client_identifier(ip_address=client_ip, session_token=x_session_token)

    rate_limiter_service.enforce_rate_limits(client_hash)

    raw_bytes: Optional[bytes] = None

    try:
        # Step 1: Intake Validation & RGB Normalization
        if image_url and image_url.strip():
            processed_bytes, _ = SecureURLIntakeService.fetch_image_from_url(image_url.strip())
            filename_hint = image_url.strip()
        elif file and file.filename:
            raw_bytes = await file.read()
            processed_bytes, _ = SecureImageIntakeService.process_image_bytes(
                raw_bytes, filename_hint=file.filename
            )
            filename_hint = file.filename
        else:
            raise InvalidImageError("Either a portrait photo file or a valid image_url must be provided.")

        # Asynchronous Queue Mode
        if async_mode:
            try:
                job_async = job_queue_manager.enqueue_job(
                    processed_bytes,
                    filename_hint=filename_hint,
                    target_gender=tg_clean,
                    target_origin=to_clean
                )
                rate_limiter_service.register_client_job(client_hash, job_async.job_id)
                return JSONResponse(
                    status_code=status.HTTP_202_ACCEPTED,
                    content=job_async.model_dump(mode="json")
                )
            except QueueFullError as qfe:
                return JSONResponse(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    content={
                        "error": "QUEUE_FULL",
                        "message": str(qfe)
                    }
                )

        # Synchronous Development Mode
        provider = get_recognition_provider()
        aligned_face_bytes = provider.validate_and_align(processed_bytes)
        user_embedding = provider.generate_embedding(aligned_face_bytes)

        # Extract facial landmark point keypoints and format UI visualization coordinates
        from app.services.landmark_service import LandmarkService
        raw_landmarks = provider.extract_landmarks(processed_bytes)
        formatted_landmarks = LandmarkService.format_ui_landmarks(raw_landmarks)
        landmarks_obj = None
        if formatted_landmarks:
            from app.schemas.matching import FacialLandmarks, LandmarkPoint
            landmarks_obj = FacialLandmarks(
                eyebrows=[LandmarkPoint(**pt) for pt in formatted_landmarks.get("eyebrows", [])],
                left_eye=[LandmarkPoint(**pt) for pt in formatted_landmarks.get("left_eye", [])],
                right_eye=[LandmarkPoint(**pt) for pt in formatted_landmarks.get("right_eye", [])],
                nose=[LandmarkPoint(**pt) for pt in formatted_landmarks.get("nose", [])],
                mouth=[LandmarkPoint(**pt) for pt in formatted_landmarks.get("mouth", [])],
                contour=[LandmarkPoint(**pt) for pt in formatted_landmarks.get("contour", [])],
            )

        matching_service = MatchingService(db=db)
        match_result = matching_service.find_matches(
            query_embedding=user_embedding,
            model_version=provider.model_version,
            target_gender=tg_clean,
            target_origin=to_clean,
            landmarks=landmarks_obj,
            request_id=request_id
        )

        return match_result

    finally:
        if raw_bytes is not None:
            del raw_bytes


@router.get(
    "/matches/queue/metrics",
    response_model=QueueMetricsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get background job queue metrics"
)
def get_queue_metrics() -> QueueMetricsResponse:
    """Returns background job queue metrics and queue capacity."""
    return job_queue_manager.get_queue_metrics()


@router.get(
    "/matches/{job_id}",
    response_model=JobStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Poll status and results for an asynchronous matching job"
)
def get_job_status(job_id: str) -> JobStatusResponse:
    """
    Polls status for a given job_id.
    Returns JobStatusResponse with status (queued, processing, completed, failed, expired)
    and MatchResultResponse if completed.
    """
    job_status = job_queue_manager.get_job_status(job_id)
    if not job_status:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "JOB_NOT_FOUND_OR_EXPIRED",
                "message": f"Job '{job_id}' not found or result expired."
            }
        )
    return job_status
