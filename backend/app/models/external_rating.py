from __future__ import annotations

from datetime import datetime
import uuid

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class ExternalRating(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "external_ratings"
    __table_args__ = (
        UniqueConstraint("movie_id", "source", "rating_type", name="uq_external_ratings_movie_source_type"),
    )

    movie_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("movies.id", ondelete="CASCADE"), nullable=False, index=True
    )
    source: Mapped[str] = mapped_column(String(50), nullable=False)
    rating_type: Mapped[str] = mapped_column(String(50), nullable=False)
    value = mapped_column(Numeric(7, 3), nullable=False)
    scale = mapped_column(Numeric(7, 3), nullable=False)
    vote_count: Mapped[int | None] = mapped_column(Integer)
    source_url: Mapped[str | None] = mapped_column(Text)
    retrieved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    movie = relationship("Movie", back_populates="external_ratings")
