from __future__ import annotations

from datetime import datetime
import uuid

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Integer, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class UserMovie(Base):
    __tablename__ = "user_movies"
    __table_args__ = (
        CheckConstraint("rating IS NULL OR (rating >= 0 AND rating <= 100)", name="rating_range"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    movie_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("movies.id", ondelete="CASCADE"), primary_key=True
    )
    rating: Mapped[int | None] = mapped_column(Integer)
    watched: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    favorite: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    user = relationship("User", back_populates="user_movies")
    movie = relationship("Movie", back_populates="user_states")
