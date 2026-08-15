import uuid
from datetime import datetime
from typing import TYPE_CHECKING
from sqlalchemy import String, ForeignKey, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from pgvector.sqlalchemy import Vector

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.celebrity import Celebrity


class CelebrityReferenceEmbedding(Base):
    __tablename__ = "celebrity_reference_embeddings"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    celebrity_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("celebrities.id", ondelete="CASCADE"), nullable=False, index=True
    )
    image_url: Mapped[str] = mapped_column(String(1024), nullable=False)
    model_version: Mapped[str] = mapped_column(String(100), nullable=False, index=True, default="fake_v1")
    embedding: Mapped[list] = mapped_column(Vector(512), nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationship back to celebrity
    celebrity: Mapped["Celebrity"] = relationship("Celebrity", back_populates="reference_embeddings")

    def __repr__(self) -> str:
        return f"<CelebrityReferenceEmbedding(id={self.id}, celebrity_id={self.celebrity_id}, model_version='{self.model_version}')>"
