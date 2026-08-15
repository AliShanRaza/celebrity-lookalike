import time
from typing import List, Dict, Optional
from uuid import uuid4
from sqlalchemy.orm import Session

from app.schemas.matching import CelebrityMatchItem, MatchResultResponse, BestPairMatches, FacialLandmarks
from app.repositories.celebrity_repository import CelebrityRepository
from app.services.calibration import ScoreCalibrator, SigmoidCalibrator
from app.services.aggregation import IdentityAggregator, QualityWeightedTopKAggregator
from app.services.metrics import metrics_collector


class MatchingService:
    """
    Service responsible for vector similarity search, reference-imbalance invariant identity aggregation,
    score calibration, and returning gender-filtered top celebrity resemblance lists and best pair.
    """

    def __init__(
        self,
        db: Session,
        calibrator: Optional[ScoreCalibrator] = None,
        aggregator: Optional[IdentityAggregator] = None
    ):
        self.db = db
        self.calibrator = calibrator or SigmoidCalibrator()
        self.aggregator = aggregator or QualityWeightedTopKAggregator()

    def find_matches(
        self,
        query_embedding: List[float],
        model_version: str,
        target_gender: Optional[str] = None,
        target_origin: Optional[str] = None,
        landmarks: Optional[FacialLandmarks] = None,
        top_k_per_gender: int = 10,
        top_k_overall: int = 10,
        candidate_limit: int = 200,
        request_id: Optional[str] = None
    ) -> MatchResultResponse:
        """
        Given a normalized 512d user face embedding:
        1. Queries candidate reference embeddings via pgvector cosine distance filtered by gender and origin.
        2. Aggregates candidate hits using QualityWeightedTopKAggregator (imbalance-invariant top-M consensus).
        3. Calibrates raw cosine similarity to 0-100% resemblance score using ScoreCalibrator.
        4. Produces distinct celebrities for female, male, overall, and best pair.
        """
        req_id = request_id or str(uuid4())

        # Determine target gender and origin
        tg_clean = (target_gender or "").strip().lower()
        if tg_clean not in ("male", "female"):
            raise ValueError(f"Invalid target_gender '{target_gender}'. Must be 'male' or 'female'.")

        to_clean = (target_origin or "bollywood").strip().lower()
        if to_clean not in ("bollywood", "hollywood"):
            raise ValueError(f"Invalid target_origin '{target_origin}'. Must be 'bollywood' or 'hollywood'.")

        # 1. Retrieve candidate embeddings from repository & track vector search duration
        start_time = time.perf_counter()
        candidates = CelebrityRepository.search_nearest_embeddings(
            session=self.db,
            query_vector=query_embedding,
            model_version=model_version,
            target_gender=tg_clean,
            target_origin=to_clean,
            limit=candidate_limit,
            active_only=True
        )
        elapsed_ms = (time.perf_counter() - start_time) * 1000.0
        metrics_collector.record_vector_search_duration(elapsed_ms)

        # 2. Imbalance-invariant Identity Aggregation
        celeb_best_map = self.aggregator.aggregate_candidate_hits(candidates)

        # 3. Calibrate scores & build distinct CelebrityMatchItem objects
        distinct_matches: List[CelebrityMatchItem] = []
        for celeb_id, (aggregated_sim, image_url, celeb) in celeb_best_map.items():
            resemblance = self.calibrator.calibrate(aggregated_sim)
            match_item = CelebrityMatchItem(
                celebrity_id=celeb.id,
                name=celeb.name,
                gender=celeb.gender.lower(),
                origin=getattr(celeb, "origin", "bollywood"),
                image_url=image_url,
                resemblance_score=resemblance,
                bio=celeb.bio
            )
            distinct_matches.append(match_item)

        # 4. Sort distinct celebrities by descending resemblance score
        distinct_matches.sort(key=lambda item: item.resemblance_score, reverse=True)

        # 5. Filter into male, female, and overall top lists
        male_matches = [m for m in distinct_matches if m.gender == "male"][:top_k_per_gender]
        female_matches = [m for m in distinct_matches if m.gender == "female"][:top_k_per_gender]
        overall_matches = distinct_matches[:top_k_overall]

        primary_target = tg_clean
        detected_gender = primary_target

        # 6. Best Pair pairing (top male + top female candidate)
        top_male = male_matches[0] if male_matches else (distinct_matches[0] if tg_clean == "male" and distinct_matches else None)
        top_female = female_matches[0] if female_matches else (distinct_matches[0] if tg_clean == "female" and distinct_matches else None)
        pair_score = round(((top_male.resemblance_score if top_male else 0.0) + (top_female.resemblance_score if top_female else 0.0)) / 2.0, 1)

        best_pair = BestPairMatches(
            male_match=top_male,
            female_match=top_female,
            pair_score=pair_score
        )

        return MatchResultResponse(
            request_id=req_id,
            model_version=model_version,
            score_version=self.calibrator.calibrator_type,
            detected_gender=detected_gender,
            primary_target_gender=primary_target,
            primary_target_origin=to_clean,
            landmarks=landmarks,
            best_pair=best_pair,
            male_matches=male_matches,
            female_matches=female_matches,
            overall_matches=overall_matches
        )
