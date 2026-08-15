import uuid
from datetime import datetime
from typing import List, TYPE_CHECKING
from sqlalchemy import String, Text, DateTime, Boolean, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.celebrity_image import CelebrityImage
    from app.models.celebrity_embedding import CelebrityEmbedding


class Celebrity(Base):
    __tablename__ = "celebrities"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    gender: Mapped[str] = mapped_column(String(20), nullable=False, index=True)  # 'male', 'female', 'non_binary'
    origin: Mapped[str] = mapped_column(String(50), nullable=False, server_default='bollywood', index=True)  # 'bollywood', 'hollywood'
    bio: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default=func.text('true'), nullable=False, index=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    images: Mapped[List["CelebrityImage"]] = relationship(
        "CelebrityImage", back_populates="celebrity", cascade="all, delete-orphan"
    )
    embeddings: Mapped[List["CelebrityEmbedding"]] = relationship(
        "CelebrityEmbedding", back_populates="celebrity", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Celebrity(id={self.id}, name='{self.name}', gender='{self.gender}', is_active={self.is_active})>"
