import io
import pytest
from unittest.mock import MagicMock
from PIL import Image

from app.config import settings
from app.services.url_intake import (
    SecureURLIntakeService,
    SSRFProtectionError,
)
from app.services.recognition.base import InvalidImageError


def create_test_image_bytes(size=(200, 200), fmt="JPEG"):
    img = Image.new("RGB", size, color="green")
    out = io.BytesIO()
    img.save(out, format=fmt)
    return out.getvalue()


def test_url_uploads_disabled_by_default(monkeypatch):
    # Feature flag ENABLE_URL_UPLOADS is False by default
    monkeypatch.setattr(settings, "ENABLE_URL_UPLOADS", False)
    with pytest.raises(InvalidImageError) as exc_info:
        SecureURLIntakeService.fetch_image_from_url("http://example.com/photo.jpg")
    assert "disabled by feature flag" in exc_info.value.message.lower()


def test_ssrf_blocked_localhost_targets(monkeypatch):
    monkeypatch.setattr(settings, "ENABLE_URL_UPLOADS", True)

    blocked_urls = [
        "http://localhost/image.jpg",
        "http://127.0.0.1/image.jpg",
        "http://0.0.0.0/image.jpg",
        "http://169.254.169.254/latest/meta-data/",
        "http://metadata.google.internal/computeMetadata/v1/",
    ]

    for url in blocked_urls:
        with pytest.raises(InvalidImageError) as exc_info:
            SecureURLIntakeService.fetch_image_from_url(url)
        assert "blocked" in exc_info.value.message.lower() or "prohibited" in exc_info.value.message.lower()


def test_ssrf_blocked_private_ip_ranges(monkeypatch):
    monkeypatch.setattr(settings, "ENABLE_URL_UPLOADS", True)

    private_urls = [
        "http://10.0.0.1/photo.jpg",
        "http://172.16.0.1/photo.jpg",
        "http://192.168.1.1/photo.jpg",
    ]

    for url in private_urls:
        with pytest.raises(InvalidImageError) as exc_info:
            SecureURLIntakeService.fetch_image_from_url(url)
        assert "prohibited" in exc_info.value.message.lower()


def test_invalid_url_schemes(monkeypatch):
    monkeypatch.setattr(settings, "ENABLE_URL_UPLOADS", True)

    invalid_schemes = [
        "file:///etc/passwd",
        "ftp://example.com/photo.jpg",
        "gopher://127.0.0.1:70/",
        "dict://127.0.0.1:11211/",
    ]

    for url in invalid_schemes:
        with pytest.raises(InvalidImageError) as exc_info:
            SecureURLIntakeService.fetch_image_from_url(url)
        assert "forbidden url scheme" in exc_info.value.message.lower() or "prohibited" in exc_info.value.message.lower()


def test_valid_url_fetch_with_feature_flag(monkeypatch):
    monkeypatch.setattr(settings, "ENABLE_URL_UPLOADS", True)

    valid_jpeg = create_test_image_bytes(size=(200, 200))

    # Mock httpx response stream
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.headers = {"Content-Type": "image/jpeg", "Content-Length": str(len(valid_jpeg))}
    mock_response.iter_bytes.return_value = [valid_jpeg]

    mock_client = MagicMock()
    mock_client.stream.return_value.__enter__.return_value = mock_response

    monkeypatch.setattr("httpx.Client", lambda **kwargs: mock_client)

    processed_bytes, img = SecureURLIntakeService.fetch_image_from_url("http://93.184.216.34/photo.jpg")

    assert isinstance(processed_bytes, bytes)
    assert img.size == (200, 200)
    assert img.mode == "RGB"
