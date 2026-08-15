from app.config import settings
from app.services.recognition.base import RecognitionProvider, FaceDetectionError
from app.services.recognition.fake import FakeRecognitionProvider
from app.services.recognition.real import RealRecognitionProvider
from app.services.recognition.siglip2 import SigLIP2RecognitionProvider
from app.services.recognition.insightface_provider import InsightFaceRecognitionProvider


def get_recognition_provider() -> RecognitionProvider:
    """
    Factory function returning active RecognitionProvider instance based on configuration settings.
    Supported options: 'insightface', 'siglip2', 'real', 'fake'.
    """
    provider_name = settings.RECOGNITION_PROVIDER.lower()
    if provider_name in ("insightface", "buffalo_l", "arcface"):
        return InsightFaceRecognitionProvider(
            model_name=getattr(settings, "INSIGHTFACE_MODEL_NAME", "buffalo_l"),
            weights_path=getattr(settings, "MODEL_WEIGHTS_PATH", None),
            dimension=settings.EMBEDDING_DIMENSION
        )
    elif provider_name in ("siglip2", "siglip"):
        return SigLIP2RecognitionProvider()
    elif provider_name == "real":
        return RealRecognitionProvider(
            dimension=settings.EMBEDDING_DIMENSION,
            model_version=settings.REAL_MODEL_VERSION,
            weights_path=settings.MODEL_WEIGHTS_PATH,
            license_path=settings.MODEL_LICENSE_PATH
        )
    else:
        return FakeRecognitionProvider(
            dimension=settings.EMBEDDING_DIMENSION,
            model_ver="fake_v1"
        )


__all__ = [
    "RecognitionProvider",
    "FaceDetectionError",
    "FakeRecognitionProvider",
    "RealRecognitionProvider",
    "SigLIP2RecognitionProvider",
    "InsightFaceRecognitionProvider",
    "get_recognition_provider"
]