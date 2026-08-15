import io
import math
import pytest
from PIL import Image, ImageDraw

from app.config import settings
from app.services.recognition import (
    get_recognition_provider,
    InsightFaceRecognitionProvider,
)


def create_test_face_portrait(color: tuple, pattern: str) -> bytes:
    """Generates synthetic portrait image bytes for face verification testing."""
    img = Image.new("RGB", (200, 200), color=color)
    draw = ImageDraw.Draw(img)
    if pattern == "face_a":
        draw.ellipse([50, 60, 85, 95], fill=(240, 240, 240))
        draw.ellipse([115, 60, 150, 95], fill=(240, 240, 240))
        draw.polygon([(100, 95), (85, 135), (115, 135)], fill=(180, 80, 80))
        draw.rectangle([70, 150, 130, 170], fill=(200, 40, 40))
    else:
        draw.ellipse([40, 50, 75, 85], fill=(200, 220, 255))
        draw.ellipse([125, 50, 160, 85], fill=(200, 220, 255))
        draw.polygon([(100, 85), (90, 125), (110, 125)], fill=(80, 180, 80))
        draw.arc([60, 140, 140, 180], start=0, end=180, fill=(240, 240, 0), width=4)

    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=95)
    return buf.getvalue()


def test_insightface_provider_self_test():
    provider = InsightFaceRecognitionProvider(dimension=512)
    result = provider.self_test()

    assert result["status"] == "passed"
    assert result["provider"] == "insightface"
    assert result["embedding_dimension"] == 512
    assert result["all_finite"] is True
    assert result["norm_passed"] is True
    assert pytest.approx(result["l2_norm"], abs=1e-3) == 1.0


def test_insightface_provider_l2_normalization(sample_image_bytes):
    provider = InsightFaceRecognitionProvider(dimension=512)
    aligned_bytes = provider.validate_and_align(sample_image_bytes)
    embedding = provider.generate_embedding(aligned_bytes)

    # 1. Dimension check
    assert len(embedding) == 512

    # 2. Finite values check
    assert all(math.isfinite(x) for x in embedding)

    # 3. L2 norm approximately 1.0
    l2_norm = math.sqrt(sum(x * x for x in embedding))
    assert pytest.approx(l2_norm, abs=1e-3) == 1.0


def test_insightface_face_pair_similarity_validation():
    """
    Verifies that two crops of the same face score meaningfully higher
    in cosine similarity than two different faces.
    """
    provider = InsightFaceRecognitionProvider(dimension=512)

    bytes_face_a1 = create_test_face_portrait((170, 130, 100), "face_a")
    bytes_face_a2 = create_test_face_portrait((170, 130, 100), "face_a")
    bytes_face_b = create_test_face_portrait((90, 150, 210), "face_b")

    aligned_a1 = provider.validate_and_align(bytes_face_a1)
    aligned_a2 = provider.validate_and_align(bytes_face_a2)
    aligned_b = provider.validate_and_align(bytes_face_b)

    emb_a1 = provider.generate_embedding(aligned_a1)
    emb_a2 = provider.generate_embedding(aligned_a2)
    emb_b = provider.generate_embedding(aligned_b)

    # Cosine Similarity = dot_product(v1, v2)
    sim_same_face = sum(a * b for a, b in zip(emb_a1, emb_a2))
    sim_diff_face = sum(a * b for a, b in zip(emb_a1, emb_b))

    print(f"Similarity Same Face (A1 vs A2): {sim_same_face:.4f}")
    print(f"Similarity Different Face (A1 vs B): {sim_diff_face:.4f}")

    assert sim_same_face > sim_diff_face
    assert sim_same_face > 0.65


def test_factory_switching_insightface(monkeypatch):
    monkeypatch.setattr(settings, "RECOGNITION_PROVIDER", "insightface")
    provider = get_recognition_provider()
    assert isinstance(provider, InsightFaceRecognitionProvider)
    assert "insightface" in provider.model_version
