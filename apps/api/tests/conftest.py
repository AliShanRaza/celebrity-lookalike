import io
import pytest
from fastapi.testclient import TestClient
from PIL import Image

from app.main import app


@pytest.fixture
def client():
    """FastAPI TestClient fixture."""
    return TestClient(app)


@pytest.fixture
def sample_image_bytes():
    """Generates valid 200x200 RGB JPEG bytes for testing."""
    img = Image.new("RGB", (200, 200), color="blue")
    output = io.BytesIO()
    img.save(output, format="JPEG")
    return output.getvalue()
