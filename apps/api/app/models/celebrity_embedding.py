import uuid
from datetime import datetime
from typing import TYPE_CHECKING
from sqlalchemy import String, Boolean, ForeignKey, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from pgvector.sqlalchemy import Vector

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.celebrity import Celebrity
    from app.models.celebrity_image import CelebrityImage


class CelebrityEmbedding(Base):
    __tablename__ = "celebrity_embeddings"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    celebrity_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("celebrities.id", ondelete="CASCADE"), nullable=False, index=True
    )
    celebrity_image_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("celebrity_images.id", ondelete="CASCADE"), nullable=False, index=True
    )
    model_version: Mapped[str] = mapped_column(String(100), nullable=False, index=True, default="fake_v1")
    embedding: Mapped[list] = mapped_column(Vector(512), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default=func.text('true'), nullable=False, index=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    celebrity: Mapped["Celebrity"] = relationship("Celebrity", back_populates="embeddings")
    image: Mapped["CelebrityImage"] = relationship("CelebrityImage", back_populates="embeddings")

    def __repr__(self) -> str:
        return f"<CelebrityEmbedding(id={self.id}, celebrity_id={self.celebrity_id}, model_version='{self.model_version}', is_active={self.is_active})>"
