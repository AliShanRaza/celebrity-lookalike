import io
import os
import pytest
from PIL import Image

from app.services.image_intake import (
    SecureImageIntakeService,
    MAX_COMPRESSED_SIZE_BYTES,
    MAX_DECODED_PIXELS,
)
from app.services.recognition.base import InvalidImageError, FaceTooSmallError


def create_test_image(fmt: str = "JPEG", size=(200, 200), color="blue") -> bytes:
    """Helper to generate image bytes in memory."""
    img = Image.new("RGB", size, color=color)
    output = io.BytesIO()
    img.save(output, format=fmt)
    return output.getvalue()


def test_valid_jpeg_intake():
    jpeg_bytes = create_test_image(fmt="JPEG", size=(300, 300))
    processed_bytes, img = SecureImageIntakeService.process_image_bytes(jpeg_bytes, filename_hint="test.jpg")
    assert isinstance(processed_bytes, bytes)
    assert img.mode == "RGB"
    assert img.size == (300, 300)


def test_valid_png_intake():
    png_bytes = create_test_image(fmt="PNG", size=(250, 250))
    processed_bytes, img = SecureImageIntakeService.process_image_bytes(png_bytes, filename_hint="test.png")
    assert isinstance(processed_bytes, bytes)
    assert img.mode == "RGB"


def test_valid_webp_intake():
    webp_bytes = create_test_image(fmt="WEBP", size=(200, 200))
    processed_bytes, img = SecureImageIntakeService.process_image_bytes(webp_bytes, filename_hint="test.webp")
    assert isinstance(processed_bytes, bytes)
    assert img.mode == "RGB"


def test_unsupported_format_gif():
    gif_bytes = create_test_image(fmt="GIF", size=(200, 200))
    with pytest.raises(InvalidImageError) as exc_info:
        SecureImageIntakeService.process_image_bytes(gif_bytes, filename_hint="test.gif")
    assert exc_info.value.error_code == "INVALID_IMAGE"
    assert "Unsupported image format" in exc_info.value.message


def test_malformed_bytes():
    malformed = b"NOT_AN_IMAGE_PAYLOAD_BYTES"
    with pytest.raises(InvalidImageError) as exc_info:
        SecureImageIntakeService.process_image_bytes(malformed, filename_hint="bad.jpg")
    assert exc_info.value.error_code == "INVALID_IMAGE"


def test_oversized_compressed_file():
    # Simulate bytes exceeding 10MB limit
    huge_bytes = b"X" * (MAX_COMPRESSED_SIZE_BYTES + 100)
    with pytest.raises(InvalidImageError) as exc_info:
        SecureImageIntakeService.process_image_bytes(huge_bytes, filename_hint="huge.jpg")
    assert "compressed size limit" in exc_info.value.message.lower()


def test_oversized_decoded_pixels(monkeypatch):
    # Mock pixel count check by setting a small threshold for testing
    monkeypatch.setattr("app.services.image_intake.MAX_DECODED_PIXELS", 1000)
    img_bytes = create_test_image(size=(100, 100)) # 10,000 px > 1,000 px limit
    with pytest.raises(InvalidImageError) as exc_info:
        SecureImageIntakeService.process_image_bytes(img_bytes, filename_hint="big_res.jpg")
    assert "pixel limit" in exc_info.value.message.lower()


def test_face_too_small_resolution():
    small_bytes = create_test_image(size=(50, 50)) # 50x50 < 80x80 min
    with pytest.raises(FaceTooSmallError) as exc_info:
        SecureImageIntakeService.process_image_bytes(small_bytes, filename_hint="small.jpg")
    assert exc_info.value.error_code == "FACE_TOO_SMALL"


def test_guaranteed_temp_file_deletion_on_success():
    jpeg_bytes = create_test_image(fmt="JPEG", size=(200, 200))
    created_path = None

    with SecureImageIntakeService.create_sanitized_temp_file(jpeg_bytes) as temp_path:
        created_path = temp_path
        assert os.path.exists(temp_path)
        # Verify it's a random filename in temp dir
        assert "portrait_" in temp_path

    # Verify guaranteed deletion after context manager exit
    assert not os.path.exists(created_path)


def test_guaranteed_temp_file_deletion_on_exception():
    jpeg_bytes = create_test_image(fmt="JPEG", size=(200, 200))
    created_path = None

    with pytest.raises(RuntimeError):
        with SecureImageIntakeService.create_sanitized_temp_file(jpeg_bytes) as temp_path:
            created_path = temp_path
            assert os.path.exists(temp_path)
            raise RuntimeError("Simulated processing failure inside context block")

    # Verify guaranteed deletion even after exception inside block
    assert not os.path.exists(created_path)
