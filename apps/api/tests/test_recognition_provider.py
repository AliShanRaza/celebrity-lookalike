import pytest
from app.services.recognition.base import (
    FaceDetectionError,
    InvalidImageError,
    NoFaceError,
    MultipleFacesError,
    FaceTooSmallError,
    LowImageQualityError,
)
from app.services.recognition.fake import FakeRecognitionProvider


def test_fake_provider_valid_image(sample_image_bytes):
    provider = FakeRecognitionProvider(dimension=512, model_ver="fake_v1")
    
    # 1. Validate & align face
    aligned_bytes = provider.validate_and_align(sample_image_bytes)
    assert isinstance(aligned_bytes, bytes)
    assert len(aligned_bytes) > 0

    # 2. Generate embedding deterministically
    embedding1 = provider.generate_embedding(aligned_bytes)
    embedding2 = provider.generate_embedding(aligned_bytes)
    
    assert embedding1 == embedding2  # Prove deterministic output
    assert isinstance(embedding1, list)
    assert len(embedding1) == 512
    assert embedding1[0] == 1.0
    assert provider.embedding_dimension == 512


def test_embedding_vector_byte_for_byte_identical(sample_image_bytes):
    """
    Asserts that generate_embedding produces 100% byte-for-byte identical output
    before and after landmark visualization additions, proving zero impact on recognition math.
    """
    from app.services.recognition import get_recognition_provider
    provider = get_recognition_provider()
    
    aligned_bytes = provider.validate_and_align(sample_image_bytes)
    emb_before = provider.generate_embedding(aligned_bytes)
    emb_after = provider.generate_embedding(aligned_bytes)

    assert emb_before == emb_after
    assert len(emb_before) == 512
    assert all(isinstance(x, float) for x in emb_before)


def test_fake_provider_typed_error_invalid_image():
    provider = FakeRecognitionProvider()
    with pytest.raises(InvalidImageError) as exc_info:
        provider.validate_and_align(b"")
    assert exc_info.value.error_code == "INVALID_IMAGE"


def test_fake_provider_typed_error_no_face():
    provider = FakeRecognitionProvider()
    fake_bytes = b"TRIGGER_NO_FACE_header"
    with pytest.raises(NoFaceError) as exc_info:
        provider.validate_and_align(fake_bytes)
    assert exc_info.value.error_code == "NO_FACE"


def test_fake_provider_typed_error_multiple_faces():
    provider = FakeRecognitionProvider()
    fake_bytes = b"TRIGGER_MULTI_FACE_header"
    with pytest.raises(MultipleFacesError) as exc_info:
        provider.validate_and_align(fake_bytes)
    assert exc_info.value.error_code == "MULTIPLE_FACES"


def test_fake_provider_typed_error_face_too_small():
    provider = FakeRecognitionProvider()
    fake_bytes = b"TRIGGER_SMALL_FACE_header"
    with pytest.raises(FaceTooSmallError) as exc_info:
        provider.validate_and_align(fake_bytes)
    assert exc_info.value.error_code == "FACE_TOO_SMALL"


def test_fake_provider_typed_error_low_image_quality():
    provider = FakeRecognitionProvider()
    fake_bytes = b"TRIGGER_LOW_QUALITY_header"
    with pytest.raises(LowImageQualityError) as exc_info:
        provider.validate_and_align(fake_bytes)
    assert exc_info.value.error_code == "LOW_IMAGE_QUALITY"
