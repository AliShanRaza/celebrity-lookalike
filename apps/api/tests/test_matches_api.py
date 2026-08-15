import io
import uuid
import pytest
from unittest.mock import MagicMock
from PIL import Image

from app.main import app
from app.db import get_db
from app.models.celebrity import Celebrity
from app.models.celebrity_image import CelebrityImage
from app.models.celebrity_embedding import CelebrityEmbedding


@pytest.fixture(autouse=True)
def override_db_dependency():
    """Autouse fixture overriding get_db dependency with a mock database session."""
    mock_db = MagicMock()
    app.dependency_overrides[get_db] = lambda: mock_db
    yield mock_db
    app.dependency_overrides.clear()


def test_post_matches_success(client, sample_image_bytes, monkeypatch):
    # Create synthetic candidates for mock repository response
    celeb_id = uuid.uuid4()
    celeb = Celebrity(id=celeb_id, name="Leonardo DiCaprio", gender="male", origin="hollywood", bio="Actor")
    img = CelebrityImage(id=uuid.uuid4(), celebrity_id=celeb_id, image_url="leo.jpg")
    emb = CelebrityEmbedding(id=uuid.uuid4(), celebrity_id=celeb_id, celebrity_image_id=img.id)

    mock_candidates = [(emb, img, celeb, 0.1)] # distance = 0.1 -> sim = 0.9 -> Sigmoid score = 99.5%

    monkeypatch.setattr(
        "app.repositories.celebrity_repository.CelebrityRepository.search_nearest_embeddings",
        lambda session, query_vector, model_version, target_gender, target_origin, limit, active_only: mock_candidates
    )

    response = client.post(
        "/api/v1/matches",
        files={"file": ("portrait.jpg", sample_image_bytes, "image/jpeg")},
        data={"target_gender": "male", "target_origin": "hollywood"}
    )

    assert response.status_code == 200
    data = response.json()

    assert "request_id" in data
    assert data["model_version"] in ("fake_v1", "google/siglip2-base-patch16-224", "insightface_buffalo_l_arcface", "real_v1")
    assert data["score_version"].startswith("sigmoid_calibrated")
    assert "male_matches" in data
    assert "female_matches" in data
    assert "overall_matches" in data

    assert len(data["male_matches"]) == 1
    assert data["male_matches"][0]["name"] == "Leonardo DiCaprio"
    assert data["male_matches"][0]["resemblance_score"] > 95.0


def test_post_matches_missing_target_gender_error(client, sample_image_bytes):
    response = client.post(
        "/api/v1/matches",
        files={"file": ("portrait.jpg", sample_image_bytes, "image/jpeg")},
        data={"target_origin": "bollywood"}
    )
    assert response.status_code == 400
    data = response.json()
    assert data["error"] == "MISSING_TARGET_GENDER"
    assert "required" in data["message"]


def test_post_matches_invalid_target_gender_error(client, sample_image_bytes):
    response = client.post(
        "/api/v1/matches",
        files={"file": ("portrait.jpg", sample_image_bytes, "image/jpeg")},
        data={"target_gender": "unknown_gender", "target_origin": "bollywood"}
    )
    assert response.status_code == 400
    data = response.json()
    assert data["error"] == "INVALID_TARGET_GENDER"


def test_post_matches_missing_target_origin_error(client, sample_image_bytes):
    response = client.post(
        "/api/v1/matches",
        files={"file": ("portrait.jpg", sample_image_bytes, "image/jpeg")},
        data={"target_gender": "male"}
    )
    assert response.status_code == 400
    data = response.json()
    assert data["error"] == "MISSING_TARGET_ORIGIN"
    assert "required" in data["message"]


def test_post_matches_invalid_target_origin_error(client, sample_image_bytes):
    response = client.post(
        "/api/v1/matches",
        files={"file": ("portrait.jpg", sample_image_bytes, "image/jpeg")},
        data={"target_gender": "male", "target_origin": "invalid_origin"}
    )
    assert response.status_code == 400
    data = response.json()
    assert data["error"] == "INVALID_TARGET_ORIGIN"


def test_post_matches_dual_filtering_gender_and_origin(client, sample_image_bytes, monkeypatch):
    celeb_mb = Celebrity(id=uuid.uuid4(), name="Male Bollywood", gender="male", origin="bollywood")
    img_mb = CelebrityImage(id=uuid.uuid4(), celebrity_id=celeb_mb.id, image_url="mb.jpg")
    emb_mb = CelebrityEmbedding(id=uuid.uuid4(), celebrity_id=celeb_mb.id, celebrity_image_id=img_mb.id)

    celeb_fh = Celebrity(id=uuid.uuid4(), name="Female Hollywood", gender="female", origin="hollywood")
    img_fh = CelebrityImage(id=uuid.uuid4(), celebrity_id=celeb_fh.id, image_url="fh.jpg")
    emb_fh = CelebrityEmbedding(id=uuid.uuid4(), celebrity_id=celeb_fh.id, celebrity_image_id=img_fh.id)

    def mock_search(session, query_vector, model_version, target_gender=None, target_origin=None, limit=50, active_only=True):
        if target_gender == "male" and target_origin == "bollywood":
            return [(emb_mb, img_mb, celeb_mb, 0.1)]
        elif target_gender == "female" and target_origin == "hollywood":
            return [(emb_fh, img_fh, celeb_fh, 0.1)]
        return []

    monkeypatch.setattr(
        "app.repositories.celebrity_repository.CelebrityRepository.search_nearest_embeddings",
        mock_search
    )

    # Test male + bollywood request returns ONLY male bollywood celebs
    res_mb = client.post(
        "/api/v1/matches",
        files={"file": ("portrait.jpg", sample_image_bytes, "image/jpeg")},
        data={"target_gender": "male", "target_origin": "bollywood"}
    )
    assert res_mb.status_code == 200
    data_mb = res_mb.json()
    assert len(data_mb["overall_matches"]) == 1
    assert data_mb["overall_matches"][0]["name"] == "Male Bollywood"
    assert data_mb["overall_matches"][0]["gender"] == "male"
    assert data_mb["overall_matches"][0]["origin"] == "bollywood"

    # Test female + hollywood request returns ONLY female hollywood celebs
    res_fh = client.post(
        "/api/v1/matches",
        files={"file": ("portrait.jpg", sample_image_bytes, "image/jpeg")},
        data={"target_gender": "female", "target_origin": "hollywood"}
    )
    assert res_fh.status_code == 200
    data_fh = res_fh.json()
    assert len(data_fh["overall_matches"]) == 1
    assert data_fh["overall_matches"][0]["name"] == "Female Hollywood"
    assert data_fh["overall_matches"][0]["gender"] == "female"
    assert data_fh["overall_matches"][0]["origin"] == "hollywood"


def test_two_different_photos_produce_different_scores():
    from app.services.recognition import get_recognition_provider
    from app.services.image_intake import SecureImageIntakeService

    provider = get_recognition_provider()

    img1 = Image.new("RGB", (200, 200), color=(200, 50, 50))
    img2 = Image.new("RGB", (200, 200), color=(50, 200, 50))

    buf1, buf2 = io.BytesIO(), io.BytesIO()
    img1.save(buf1, format="JPEG")
    img2.save(buf2, format="JPEG")

    proc1, _ = SecureImageIntakeService.process_image_bytes(buf1.getvalue(), "p1.jpg")
    proc2, _ = SecureImageIntakeService.process_image_bytes(buf2.getvalue(), "p2.jpg")

    aligned1 = provider.validate_and_align(proc1)
    aligned2 = provider.validate_and_align(proc2)

    emb1 = provider.generate_embedding(aligned1)
    emb2 = provider.generate_embedding(aligned2)

    # Embeddings must not be identical
    assert emb1 != emb2
    # Dot product must be strictly less than 1.0 (different vectors)
    dot = sum(a * b for a, b in zip(emb1, emb2))
    assert dot < 0.999


def test_post_matches_error_invalid_image(client):
    response = client.post(
        "/api/v1/matches",
        files={"file": ("corrupt.jpg", b"NOT_VALID_IMAGE_DATA", "image/jpeg")},
        data={"target_gender": "male", "target_origin": "bollywood"}
    )
    assert response.status_code == 400
    data = response.json()
    assert data["error"] == "INVALID_IMAGE"


def test_post_matches_error_no_face_trigger(client, sample_image_bytes):
    fake_bytes = sample_image_bytes + b"_TRIGGER_NO_FACE"
    response = client.post(
        "/api/v1/matches",
        files={"file": ("noface.jpg", fake_bytes, "image/jpeg")},
        data={"target_gender": "male", "target_origin": "bollywood"}
    )
    assert response.status_code == 400
    data = response.json()
    assert data["error"] == "NO_FACE"


def test_post_matches_error_multi_face_trigger(client, sample_image_bytes):
    fake_bytes = sample_image_bytes + b"_TRIGGER_MULTI_FACE"
    response = client.post(
        "/api/v1/matches",
        files={"file": ("multiface.jpg", fake_bytes, "image/jpeg")},
        data={"target_gender": "male", "target_origin": "bollywood"}
    )
    assert response.status_code == 400
    data = response.json()
    assert data["error"] == "MULTIPLE_FACES"


def test_post_matches_error_small_face_trigger(client, sample_image_bytes):
    fake_bytes = sample_image_bytes + b"_TRIGGER_SMALL_FACE"
    response = client.post(
        "/api/v1/matches",
        files={"file": ("smallface.jpg", fake_bytes, "image/jpeg")},
        data={"target_gender": "male", "target_origin": "bollywood"}
    )
    assert response.status_code == 400
    data = response.json()
    assert data["error"] == "FACE_TOO_SMALL"
