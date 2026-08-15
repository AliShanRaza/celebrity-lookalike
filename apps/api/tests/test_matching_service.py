import uuid
import pytest
from unittest.mock import MagicMock

from app.services.calibration import MonotonicPlaceholderCalibrator, SigmoidCalibrator
from app.services.matching import MatchingService
from app.schemas.matching import MatchResultResponse
from app.models.celebrity import Celebrity
from app.models.celebrity_image import CelebrityImage
from app.models.celebrity_embedding import CelebrityEmbedding


def test_monotonic_placeholder_calibrator():
    calibrator = MonotonicPlaceholderCalibrator()
    assert calibrator.is_calibrated is False
    assert "uncalibrated" in calibrator.calibrator_type

    score_min = calibrator.calibrate(-1.0)
    score_mid = calibrator.calibrate(0.0)
    score_max = calibrator.calibrate(1.0)

    assert score_min == 0.0
    assert score_mid == 50.0
    assert score_max == 100.0


def test_matching_service_identity_aggregation_and_gender_filtering(monkeypatch):
    mock_db = MagicMock()

    # Create synthetic celebrity entities
    celeb_male_id = uuid.uuid4()
    celeb_female_id = uuid.uuid4()

    celeb_male = Celebrity(id=celeb_male_id, name="Famous Actor", gender="male", origin="bollywood", bio="Actor Bio")
    celeb_female = Celebrity(id=celeb_female_id, name="Famous Actress", gender="female", origin="hollywood", bio="Actress Bio")

    img_m1 = CelebrityImage(id=uuid.uuid4(), celebrity_id=celeb_male_id, image_url="actor_photo1.jpg")
    img_m2 = CelebrityImage(id=uuid.uuid4(), celebrity_id=celeb_male_id, image_url="actor_photo2_better.jpg")
    img_f1 = CelebrityImage(id=uuid.uuid4(), celebrity_id=celeb_female_id, image_url="actress_photo1.jpg")

    emb_m1 = CelebrityEmbedding(id=uuid.uuid4(), celebrity_id=celeb_male_id, celebrity_image_id=img_m1.id)
    emb_m2 = CelebrityEmbedding(id=uuid.uuid4(), celebrity_id=celeb_male_id, celebrity_image_id=img_m2.id)
    emb_f1 = CelebrityEmbedding(id=uuid.uuid4(), celebrity_id=celeb_female_id, celebrity_image_id=img_f1.id)

    # Candidate tuple: (embedding, image, celebrity, cosine_distance)
    # Cosine similarity = 1.0 - distance
    mock_candidates = [
        (emb_m2, img_m2, celeb_male, 0.1),      # sim = 0.9 (Best match)
        (emb_m1, img_m1, celeb_male, 0.4),      # sim = 0.6
        (emb_f1, img_f1, celeb_female, 0.2),    # sim = 0.8 (Female celebrity match)
    ]

    def mock_search_nearest(session, query_vector, model_version, target_gender=None, target_origin=None, limit=200, active_only=True):
        if target_gender == "male" and target_origin == "bollywood":
            return [c for c in mock_candidates if c[2].gender == "male" and c[2].origin == "bollywood"]
        elif target_gender == "female" and target_origin == "hollywood":
            return [c for c in mock_candidates if c[2].gender == "female" and c[2].origin == "hollywood"]
        return mock_candidates

    monkeypatch.setattr(
        "app.repositories.celebrity_repository.CelebrityRepository.search_nearest_embeddings",
        mock_search_nearest
    )

    service = MatchingService(db=mock_db)
    query_vec = [1.0] + [0.0] * 511

    # Test male request
    result_m = service.find_matches(query_embedding=query_vec, model_version="fake_v1", target_gender="male", target_origin="bollywood")
    assert isinstance(result_m, MatchResultResponse)
    assert result_m.model_version == "fake_v1"
    assert result_m.primary_target_gender == "male"
    assert result_m.primary_target_origin == "bollywood"
    assert len(result_m.male_matches) == 1
    assert result_m.male_matches[0].name == "Famous Actor"
    assert result_m.male_matches[0].image_url == "actor_photo2_better.jpg"

    # Test female request
    result_f = service.find_matches(query_embedding=query_vec, model_version="fake_v1", target_gender="female", target_origin="hollywood")
    assert isinstance(result_f, MatchResultResponse)
    assert result_f.primary_target_gender == "female"
    assert result_f.primary_target_origin == "hollywood"
    assert len(result_f.female_matches) == 1
    assert result_f.female_matches[0].name == "Famous Actress"
