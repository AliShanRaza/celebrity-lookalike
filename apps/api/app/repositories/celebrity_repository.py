from typing import List, Tuple, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.config import settings
from app.models.celebrity import Celebrity
from app.models.celebrity_image import CelebrityImage
from app.models.celebrity_embedding import CelebrityEmbedding


class CelebrityRepository:
    """
    Repository handling PostgreSQL + pgvector persistence and cosine similarity search.
    Provides automatic fallback to CelebrityDatasetRegistry for local reference dataset matching.
    """

    @staticmethod
    def search_nearest_embeddings(
        session: Session,
        query_vector: List[float],
        model_version: str,
        target_gender: Optional[str] = None,
        target_origin: Optional[str] = None,
        limit: int = 50,
        active_only: bool = True
    ) -> List[Tuple[CelebrityEmbedding, CelebrityImage, Celebrity, float]]:
        """
        Performs nearest-neighbor cosine distance search over celebrity_embeddings
        filtered strictly to a single model_version, optional target_gender, target_origin, and active status flags.

        Returns a list of (embedding, image, celebrity, cosine_distance) tuples
        sorted by ascending cosine_distance (0.0 = identical, 2.0 = opposite).
        """
        # Calculate pgvector cosine distance column expression
        distance_col = CelebrityEmbedding.embedding.cosine_distance(query_vector).label("distance")

        stmt = (
            select(CelebrityEmbedding, CelebrityImage, Celebrity, distance_col)
            .join(CelebrityImage, CelebrityEmbedding.celebrity_image_id == CelebrityImage.id)
            .join(Celebrity, CelebrityEmbedding.celebrity_id == Celebrity.id)
            .where(CelebrityEmbedding.model_version == model_version)
        )

        if target_gender:
            stmt = stmt.where(Celebrity.gender == target_gender.lower())

        if target_origin:
            stmt = stmt.where(Celebrity.origin == target_origin.lower())

        if active_only:
            stmt = stmt.where(
                CelebrityEmbedding.is_active.is_(True),
                CelebrityImage.is_active.is_(True),
                Celebrity.is_active.is_(True)
            )

        stmt = stmt.order_by(distance_col).limit(limit)

        try:
            result = session.execute(stmt).all()
            if result:
                return [(row[0], row[1], row[2], float(row[3])) for row in result]
            # Fallback to dataset registry if database table is empty
            return CelebrityRepository._get_standalone_mock_candidates(query_vector, model_version, limit=limit, target_gender=target_gender, target_origin=target_origin)
        except Exception:
            return CelebrityRepository._get_standalone_mock_candidates(query_vector, model_version, limit=limit, target_gender=target_gender, target_origin=target_origin)

    @staticmethod
    def _get_standalone_mock_candidates(
        query_vector: List[float] | None = None,
        model_version: str = "real_v1",
        limit: int = 200,
        target_gender: str | None = None,
        target_origin: str | None = None
    ) -> List[Tuple[CelebrityEmbedding, CelebrityImage, Celebrity, float]]:
        """
        Returns dynamic celebrity matches for local dataset searching by computing
        cosine distance between query_vector and reference dataset embeddings.
        """
        from app.services.dataset_registry import dataset_registry
        vec = query_vector if query_vector else [0.0] * 512
        return dataset_registry.search_nearest(query_vector=vec, model_version=model_version, limit=limit, target_gender=target_gender, target_origin=target_origin)

    @staticmethod
    def create_celebrity(
        session: Session,
        name: str,
        gender: str,
        origin: str = "bollywood",
        bio: str | None = None,
        is_active: bool = True
    ) -> Celebrity:
        celebrity = Celebrity(name=name, gender=gender, origin=origin, bio=bio, is_active=is_active)
        session.add(celebrity)
        session.flush()
        return celebrity

    @staticmethod
    def create_celebrity_image(
        session: Session,
        celebrity_id: str,
        image_url: str,
        licence_text: str | None = None,
        attribution: str | None = None,
        is_active: bool = True
    ) -> CelebrityImage:
        image = CelebrityImage(
            celebrity_id=celebrity_id,
            image_url=image_url,
            is_active=is_active
        )
        session.add(image)
        session.flush()
        return image

    @staticmethod
    def create_celebrity_embedding(
        session: Session,
        celebrity_id: str,
        celebrity_image_id: str,
        embedding: List[float],
        model_version: str = "fake_v1",
        is_active: bool = True
    ) -> CelebrityEmbedding:
        emb = CelebrityEmbedding(
            celebrity_id=celebrity_id,
            celebrity_image_id=celebrity_image_id,
            embedding=embedding,
            model_version=model_version,
            is_active=is_active
        )
        session.add(emb)
        session.flush()
        return emb
