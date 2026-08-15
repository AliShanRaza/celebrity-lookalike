import uuid
from datetime import datetime
from typing import List, TYPE_CHECKING
from sqlalchemy import String, Boolean, Float, ForeignKey, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.celebrity import Celebrity
    from app.models.celebrity_embedding import CelebrityEmbedding


class CelebrityImage(Base):
    __tablename__ = "celebrity_images"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    celebrity_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("celebrities.id", ondelete="CASCADE"), nullable=False, index=True
    )
    image_url: Mapped[str] = mapped_column(String(1024), nullable=False)
    quality_score: Mapped[float | None] = mapped_column(Float, nullable=True, default=1.0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default=func.text('true'), nullable=False, index=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    celebrity: Mapped["Celebrity"] = relationship("Celebrity", back_populates="images")
    embeddings: Mapped[List["CelebrityEmbedding"]] = relationship(
        "CelebrityEmbedding", back_populates="image", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<CelebrityImage(id={self.id}, celebrity_id={self.celebrity_id}, is_active={self.is_active})>"
