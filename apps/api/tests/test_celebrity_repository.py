import math
import pytest
from unittest.mock import MagicMock
from app.repositories.celebrity_repository import CelebrityRepository


def cosine_distance_python(v1, v2):
    """Reference Python implementation of cosine distance: 1.0 - (dot(v1, v2) / (norm(v1) * norm(v2)))."""
    dot = sum(a * b for a, b in zip(v1, v2))
    norm1 = math.sqrt(sum(a * a for a in v1))
    norm2 = math.sqrt(sum(b * b for b in v2))
    similarity = dot / (norm1 * norm2)
    return 1.0 - similarity


def test_synthetic_vector_cosine_distance_ranking_order():
    """
    Verifies cosine distance math and ranking order with synthetic 512d normalized vectors:
    Query Vector: [1.0, 0.0, 0.0, ...]
    Candidate A (Identical): [1.0, 0.0, 0.0, ...] -> Distance = 0.0
    Candidate B (45 deg angle): [0.7071, 0.7071, 0.0, ...] -> Distance ~= 0.2929
    Candidate C (Orthogonal): [0.0, 1.0, 0.0, ...] -> Distance = 1.0
    Candidate D (Opposite): [-1.0, 0.0, 0.0, ...] -> Distance = 2.0
    """
    dim = 512
    query = [0.0] * dim
    query[0] = 1.0

    cand_a = [0.0] * dim
    cand_a[0] = 1.0

    cand_b = [0.0] * dim
    cand_b[0] = 0.70710678
    cand_b[1] = 0.70710678

    cand_c = [0.0] * dim
    cand_c[1] = 1.0

    cand_d = [0.0] * dim
    cand_d[0] = -1.0

    dist_a = cosine_distance_python(query, cand_a)
    dist_b = cosine_distance_python(query, cand_b)
    dist_c = cosine_distance_python(query, cand_c)
    dist_d = cosine_distance_python(query, cand_d)

    # Assert exact ranking order: A (0.0) < B (~0.293) < C (1.0) < D (2.0)
    assert pytest.approx(dist_a, abs=1e-5) == 0.0
    assert pytest.approx(dist_b, abs=1e-4) == 0.29289
    assert pytest.approx(dist_c, abs=1e-5) == 1.0
    assert pytest.approx(dist_d, abs=1e-5) == 2.0

    candidates = [
        ("Candidate D", dist_d),
        ("Candidate B", dist_b),
        ("Candidate A", dist_a),
        ("Candidate C", dist_c),
    ]

    # Sort candidates by ascending cosine distance
    ranked = sorted(candidates, key=lambda x: x[1])
    ranked_names = [item[0] for item in ranked]

    assert ranked_names == ["Candidate A", "Candidate B", "Candidate C", "Candidate D"]


def test_repository_search_nearest_embeddings_query_building():
    """Verifies CelebrityRepository.search_nearest_embeddings executes properly on session."""
    mock_session = MagicMock()
    mock_execute_result = MagicMock()
    mock_row = (MagicMock(), MagicMock(), MagicMock(), 0.1)
    mock_execute_result.all.return_value = [mock_row]
    mock_session.execute.return_value = mock_execute_result

    query_vec = [1.0] + [0.0] * 511
    results = CelebrityRepository.search_nearest_embeddings(
        session=mock_session,
        query_vector=query_vec,
        model_version="fake_v1",
        limit=5,
        active_only=True
    )

    assert len(results) == 1
    assert mock_session.execute.called
