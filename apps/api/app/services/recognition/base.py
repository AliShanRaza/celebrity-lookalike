from abc import ABC, abstractmethod
from typing import List, Dict, Any


class FaceDetectionError(Exception):
    """Base exception for face validation and recognition errors."""
    def __init__(self, message: str, error_code: str = "FACE_DETECTION_ERROR"):
        super().__init__(message)
        self.message = message
        self.error_code = error_code


class InvalidImageError(FaceDetectionError):
    """Raised when file content is corrupt, empty, or cannot be decoded as an image."""
    def __init__(self, message: str = "Invalid image content or corrupted file."):
        super().__init__(message, error_code="INVALID_IMAGE")


class NoFaceError(FaceDetectionError):
    """Raised when no face is detected in the uploaded portrait."""
    def __init__(self, message: str = "No face detected in portrait. Please upload a clear single portrait."):
        super().__init__(message, error_code="NO_FACE")


class MultipleFacesError(FaceDetectionError):
    """Raised when more than one face is detected in the uploaded image."""
    def __init__(self, message: str = "Multiple faces detected. Exactly one face is allowed."):
        super().__init__(message, error_code="MULTIPLE_FACES")


class FaceTooSmallError(FaceDetectionError):
    """Raised when the detected face is too small (e.g. less than 80x80 pixels)."""
    def __init__(self, message: str = "Detected face is too small. Please upload a closer portrait."):
        super().__init__(message, error_code="FACE_TOO_SMALL")


class LowImageQualityError(FaceDetectionError):
    """Raised when image resolution or sharpness is too low for face recognition."""
    def __init__(self, message: str = "Image quality is too low or overly blurry."):
        super().__init__(message, error_code="LOW_IMAGE_QUALITY")


class RecognitionProvider(ABC):
    """
    Abstract interface decoupling face detection, face alignment, and embedding generation
    from the FastAPI endpoints and database storage.
    """

    @abstractmethod
    def validate_and_align(self, image_bytes: bytes) -> bytes:
        """
        Validates image content (decoded image header/pixels, not extension),
        enforces exactly one face, quality/size thresholds, and returns aligned face crop bytes.

        Raises FaceDetectionError (or subclasses) on validation failures.
        """
        pass

    @abstractmethod
    def generate_embedding(self, aligned_face_bytes: bytes) -> List[float]:
        """
        Generates face recognition embedding vector from aligned face crop.
        Returns an L2-normalized float list of size matching embedding_dimension (e.g., 512).
        """
        pass

    @abstractmethod
    def extract_landmarks(self, image_bytes: bytes) -> Dict[str, List[Dict[str, float]]]:
        """
        Extracts key facial landmark points (eyebrows, eyes, nose, mouth, contour)
        normalized to [0.0, 1.0] relative to image dimensions.
        """
        pass

    @abstractmethod
    def self_test(self) -> Dict[str, Any]:
        """
        Runs model self-test verifying embedding dimension, finite values (no NaN/Inf),
        and L2 norm approximately equal to 1.0. Returns test status summary dict.
        """
        pass

    @property
    @abstractmethod
    def model_version(self) -> str:
        """Returns the version identifier string of the active recognition model."""
        pass

    @property
    @abstractmethod
    def embedding_dimension(self) -> int:
        """Returns the vector size output by this recognition provider."""
        pass
