from abc import ABC, abstractmethod
from typing import List, Dict, Tuple, Any


class IdentityAggregator(ABC):
    """
    Abstract interface for identity-level match aggregation.
    Aggregates image-level candidate vector similarities into distinct celebrity identity scores.
    """

    @abstractmethod
    def aggregate_candidate_hits(
        self,
        candidate_hits: List[Tuple[Any, Any, Any, float]]
    ) -> Dict[str, Tuple[float, str, Any]]:
        """
        Groups candidate tuples (embedding, image, celebrity, cosine_distance) by celebrity_id.
        Returns map: {celeb_id: (aggregated_similarity, representative_image_url, celebrity_obj)}
        """
        pass

    @property
    @abstractmethod
    def aggregator_type(self) -> str:
        """Returns aggregator strategy identifier."""
        pass


class QualityWeightedTopKAggregator(IdentityAggregator):
    """
    Imbalance-invariant identity aggregator.
    
    Mitigates reference photo count imbalance and extreme-value sampling bias by:
    1. Grouping candidate hits by celebrity_id.
    2. Evaluating the top M (default top_m=3) best reference photo matches per celebrity identity.
    3. Computing a quality-weighted top-M consensus similarity:
       S_identity = sum(q_i * s_i for i in top_M) / sum(q_i for i in top_M)
    4. Eliminating unfair max-sampling advantage for identities with 50+ reference photos.
    """

    def __init__(self, top_m: int = 3, default_quality: float = 1.0):
        self.top_m = top_m
        self.default_quality = default_quality

    def aggregate_candidate_hits(
        self,
        candidate_hits: List[Tuple[Any, Any, Any, float]]
    ) -> Dict[str, Tuple[float, str, Any]]:
        # Group candidates by celebrity_id: {celeb_id: [(raw_sim, quality, img_url, celeb_obj)]}
        grouped: Dict[str, List[Tuple[float, float, str, Any]]] = {}

        for emb, img, celeb, distance in candidate_hits:
            raw_sim = 1.0 - float(distance)
            celeb_id = str(celeb.id)

            # Extract quality score if available on CelebrityImage model, else default
            quality = getattr(img, "quality_score", None)
            if quality is None or not (0.1 <= float(quality) <= 1.0):
                quality = self.default_quality
            else:
                quality = float(quality)

            item = (raw_sim, quality, img.image_url, celeb)
            if celeb_id not in grouped:
                grouped[celeb_id] = [item]
            else:
                grouped[celeb_id].append(item)

        # Compute imbalance-invariant quality-weighted top-M consensus per celebrity
        aggregated_map: Dict[str, Tuple[float, str, Any]] = {}

        for celeb_id, items in grouped.items():
            # Sort items for this celebrity by descending raw similarity
            items.sort(key=lambda x: x[0], reverse=True)

            # Take top M best reference images for this celebrity identity
            top_m_items = items[:self.top_m]

            total_weighted_sim = sum(sim * q for sim, q, _, _ in top_m_items)
            total_weight = sum(q for _, q, _, _ in top_m_items)

            consensus_sim = total_weighted_sim / total_weight if total_weight > 0 else top_m_items[0][0]

            # Representative display image: image with highest similarity & quality in top M
            best_img_url = top_m_items[0][2]
            celeb_obj = top_m_items[0][3]

            aggregated_map[celeb_id] = (round(consensus_sim, 4), best_img_url, celeb_obj)

        return aggregated_map

    @property
    def aggregator_type(self) -> str:
        return "quality_weighted_top_3_consensus_v1"
