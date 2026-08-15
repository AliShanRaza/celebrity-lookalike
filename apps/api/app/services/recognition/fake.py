import io
import math
import time
from typing import List, Dict, Any
from PIL import Image

from app.services.recognition.base import (
    RecognitionProvider,
    FaceDetectionError,
    InvalidImageError,
    NoFaceError,
    MultipleFacesError,
    FaceTooSmallError,
    LowImageQualityError,
)
from app.services.metrics import metrics_collector


class FakeRecognitionProvider(RecognitionProvider):
    """
    Fake recognition provider for Phase 1 and deterministic test execution.
    Decodes actual image content via PIL to validate decoded image structure.
    """

    def __init__(self, dimension: int = 512, model_ver: str = "fake_v1"):
        self._dimension = dimension
        self._model_ver = model_ver

    def validate_and_align(self, image_bytes: bytes) -> bytes:
        start_time = time.perf_counter()
        try:
            if not image_bytes or len(image_bytes) < 10:
                metrics_collector.record_face_validation("invalid_image")
                raise InvalidImageError("Empty or corrupt file content.")

            # Test trigger hooks for deterministic failure path testing
            if b"TRIGGER_NO_FACE" in image_bytes:
                metrics_collector.record_face_validation("no_face")
                raise NoFaceError("No face detected in portrait. Please upload a clear single portrait.")
            if b"TRIGGER_MULTI_FACE" in image_bytes:
                metrics_collector.record_face_validation("multiple_faces")
                raise MultipleFacesError("Multiple faces detected. Exactly one face is allowed.")
            if b"TRIGGER_SMALL_FACE" in image_bytes:
                metrics_collector.record_face_validation("face_too_small")
                raise FaceTooSmallError("Detected face is too small. Please upload a closer portrait.")
            if b"TRIGGER_LOW_QUALITY" in image_bytes:
                metrics_collector.record_face_validation("low_image_quality")
                raise LowImageQualityError("Image quality is too low or overly blurry.")

            # Validate image by actual decoded content (Pillow parser), NOT file extension
            with Image.open(io.BytesIO(image_bytes)) as img:
                img.verify()
            
            with Image.open(io.BytesIO(image_bytes)) as img:
                img = img.convert("RGB")
                width, height = img.size
                if width < 80 or height < 80:
                    metrics_collector.record_face_validation("face_too_small")
                    raise FaceTooSmallError(f"Image resolution {width}x{height} is too small. Minimum 80x80 required.")
                
                aligned_crop = img.resize((112, 112))
                output = io.BytesIO()
                aligned_crop.save(output, format="JPEG")
                metrics_collector.record_face_validation("success")
                return output.getvalue()
        except Exception as e:
            if isinstance(e, FaceDetectionError):
                raise
            metrics_collector.record_face_validation("invalid_image")
            raise InvalidImageError(f"Failed to decode image content: {str(e)}")
        finally:
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            metrics_collector.record_inference_duration(elapsed_ms)

    def generate_embedding(self, aligned_face_bytes: bytes) -> List[float]:
        # Return deterministic normalized L2 unit vector for testing
        vector = [0.0] * self._dimension
        vector[0] = 1.0
        return vector

    def extract_landmarks(self, image_bytes: bytes) -> Dict[str, List[Dict[str, float]]]:
        # Deterministic facial landmarks (eyebrows, eyes, nose, mouth, contour)
        return {
            "eyebrows": [
                {"x": 0.32, "y": 0.32}, {"x": 0.38, "y": 0.30}, {"x": 0.44, "y": 0.32},
                {"x": 0.56, "y": 0.32}, {"x": 0.62, "y": 0.30}, {"x": 0.68, "y": 0.32}
            ],
            "left_eye": [
                {"x": 0.33, "y": 0.38}, {"x": 0.38, "y": 0.36}, {"x": 0.43, "y": 0.38}, {"x": 0.38, "y": 0.40}
            ],
            "right_eye": [
                {"x": 0.57, "y": 0.38}, {"x": 0.62, "y": 0.36}, {"x": 0.67, "y": 0.38}, {"x": 0.62, "y": 0.40}
            ],
            "nose": [
                {"x": 0.50, "y": 0.42}, {"x": 0.50, "y": 0.48}, {"x": 0.47, "y": 0.54}, {"x": 0.50, "y": 0.55}, {"x": 0.53, "y": 0.54}
            ],
            "mouth": [
                {"x": 0.38, "y": 0.66}, {"x": 0.44, "y": 0.64}, {"x": 0.50, "y": 0.65}, {"x": 0.56, "y": 0.64},
                {"x": 0.62, "y": 0.66}, {"x": 0.56, "y": 0.70}, {"x": 0.50, "y": 0.71}, {"x": 0.44, "y": 0.70}
            ],
            "contour": [
                {"x": 0.22, "y": 0.35}, {"x": 0.24, "y": 0.50}, {"x": 0.28, "y": 0.65}, {"x": 0.36, "y": 0.78},
                {"x": 0.50, "y": 0.85}, {"x": 0.64, "y": 0.78}, {"x": 0.72, "y": 0.65}, {"x": 0.76, "y": 0.50}, {"x": 0.78, "y": 0.35}
            ]
        }

    def self_test(self) -> Dict[str, Any]:
        dummy_crop = b"fake_aligned_crop_bytes"
        embedding = self.generate_embedding(dummy_crop)

        dim_passed = (len(embedding) == self._dimension)
        all_finite = all(math.isfinite(x) for x in embedding)
        l2_norm = math.sqrt(sum(x * x for x in embedding))
        norm_passed = (abs(l2_norm - 1.0) < 1e-4)

        success = dim_passed and all_finite and norm_passed

        return {
            "status": "passed" if success else "failed",
            "provider": "fake",
            "model_version": self._model_ver,
            "embedding_dimension": len(embedding),
            "expected_dimension": self._dimension,
            "all_finite": all_finite,
            "l2_norm": round(l2_norm, 6),
            "norm_passed": norm_passed,
        }

    @property
    def model_version(self) -> str:
        return self._model_ver

    @property
    def embedding_dimension(self) -> int:
        return self._dimension
