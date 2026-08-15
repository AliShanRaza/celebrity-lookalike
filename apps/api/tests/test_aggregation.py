import uuid
import pytest
from app.models.celebrity import Celebrity
from app.models.celebrity_image import CelebrityImage
from app.models.celebrity_embedding import CelebrityEmbedding
from app.services.aggregation import QualityWeightedTopKAggregator


def test_quality_weighted_top_k_aggregator_imbalance_invariance():
    aggregator = QualityWeightedTopKAggregator(top_m=3)

    celeb_a_id = uuid.uuid4()
    celeb_b_id = uuid.uuid4()

    celeb_a = Celebrity(id=celeb_a_id, name="Celebrity A (50 Reference Photos)", gender="male")
    celeb_b = Celebrity(id=celeb_b_id, name="Celebrity B (2 Reference Photos)", gender="male")

    candidate_hits = []

    # Celebrity A has 10 noisy candidate hits in vector search results (sims: 0.85, 0.50, 0.45, 0.40, 0.35, ...)
    # Raw max similarity = 0.85, but average of top-3 consensus = (0.85 + 0.50 + 0.45) / 3 = 0.60
    a_sims = [0.85, 0.50, 0.45, 0.40, 0.38, 0.35, 0.30, 0.25, 0.20, 0.15]
    for sim in a_sims:
        dist = 1.0 - sim
        img = CelebrityImage(id=uuid.uuid4(), celebrity_id=celeb_a_id, image_url="celeb_a.jpg", quality_score=1.0)
        emb = CelebrityEmbedding(id=uuid.uuid4(), celebrity_id=celeb_a_id)
        candidate_hits.append((emb, img, celeb_a, dist))

    # Celebrity B has 2 highly consistent candidate hits in vector search results (sims: 0.78, 0.76)
    # Average top-3 consensus = (0.78 + 0.76) / 2 = 0.77
    b_sims = [0.78, 0.76]
    for sim in b_sims:
        dist = 1.0 - sim
        img = CelebrityImage(id=uuid.uuid4(), celebrity_id=celeb_b_id, image_url="celeb_b.jpg", quality_score=1.0)
        emb = CelebrityEmbedding(id=uuid.uuid4(), celebrity_id=celeb_b_id)
        candidate_hits.append((emb, img, celeb_b, dist))

    # Perform aggregation
    result = aggregator.aggregate_candidate_hits(candidate_hits)

    assert str(celeb_a_id) in result
    assert str(celeb_b_id) in result

    agg_sim_a, _, _ = result[str(celeb_a_id)]
    agg_sim_b, _, _ = result[str(celeb_b_id)]

    # In raw max aggregation, Celebrity A would be ranked #1 (0.85 vs 0.78).
    # Under QualityWeightedTopKAggregator consensus, Celebrity B is correctly ranked #1 (0.77 vs 0.60),
    # eliminating unfair max-sampling advantage from photo count imbalance!
    assert agg_sim_b > agg_sim_a
    assert agg_sim_b == 0.77
    assert agg_sim_a == 0.60
