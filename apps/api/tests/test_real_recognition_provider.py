import math
import pytest

from app.config import settings
from app.services.recognition import (
    get_recognition_provider,
    FakeRecognitionProvider,
    RealRecognitionProvider,
)


def test_real_recognition_provider_self_test():
    provider = RealRecognitionProvider(dimension=512, model_version="real_v1")
    result = provider.self_test()

    assert result["status"] == "passed"
    assert result["provider"] == "real"
    assert result["model_version"] == "real_v1"
    assert result["embedding_dimension"] == 512
    assert result["all_finite"] is True
    assert result["norm_passed"] is True
    assert pytest.approx(result["l2_norm"], abs=1e-4) == 1.0


def test_real_recognition_provider_l2_normalization(sample_image_bytes):
    provider = RealRecognitionProvider(dimension=512, model_version="real_v1")
    aligned_bytes = provider.validate_and_align(sample_image_bytes)
    embedding = provider.generate_embedding(aligned_bytes)

    # 1. Dimension check
    assert len(embedding) == 512

    # 2. Finite values check
    assert all(math.isfinite(x) for x in embedding)

    # 3. L2 norm approximately 1.0
    l2_norm = math.sqrt(sum(x * x for x in embedding))
    assert pytest.approx(l2_norm, abs=1e-4) == 1.0


def test_factory_switching(monkeypatch):
    # Test 'fake' selection
    monkeypatch.setattr(settings, "RECOGNITION_PROVIDER", "fake")
    provider_fake = get_recognition_provider()
    assert isinstance(provider_fake, FakeRecognitionProvider)

    # Test 'real' selection
    monkeypatch.setattr(settings, "RECOGNITION_PROVIDER", "real")
    provider_real = get_recognition_provider()
    assert isinstance(provider_real, RealRecognitionProvider)
