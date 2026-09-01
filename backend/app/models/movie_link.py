from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, String, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class MovieLink(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "movie_links"
    __table_args__ = (
        UniqueConstraint("movie_id", "source", "url", name="uq_movie_links_movie_source_url"),
    )

    movie_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("movies.id", ondelete="CASCADE"), nullable=False, index=True
    )
    source: Mapped[str] = mapped_column(String(50), nullable=False)
    url: Mapped[str] = mapped_column(String(2000), nullable=False)
    label: Mapped[str | None] = mapped_column(String(150))

    movie = relationship("Movie", back_populates="links")
