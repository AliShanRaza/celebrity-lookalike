from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.logging_config import setup_logging
from app.routers.health import router as health_router
from app.routers.matching import router as matching_router
from app.services.recognition.base import FaceDetectionError


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize privacy-preserving logging
    setup_logging()
    yield
    # Shutdown logic if needed


app = FastAPI(
    title="Celebrity Look-Alike API",
    description="Privacy-first celebrity look-alike recognition and similarity search API",
    version=settings.APP_VERSION,
    lifespan=lifespan
)

# Configure CORS (Allows all origins in local development mode for seamless local web app integration)
cors_origins = ["*"] if settings.APP_ENV == "development" else settings.cors_origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception handlers for typed domain errors
@app.exception_handler(FaceDetectionError)
async def face_detection_error_handler(request: Request, exc: FaceDetectionError):
    return JSONResponse(
        status_code=400,
        content={
            "error": exc.error_code,
            "message": exc.message
        }
    )

# Include routers
app.include_router(health_router)
app.include_router(matching_router)


@app.get("/")
def root():
    return {
        "name": "Celebrity Look-Alike API",
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "health": "/api/v1/health"
    }
