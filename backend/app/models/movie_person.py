from __future__ import annotations

import uuid

from sqlalchemy import CheckConstraint, ForeignKey, Integer, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, UUIDPrimaryKeyMixin


class MoviePerson(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "movie_people"
    __table_args__ = (
        CheckConstraint("credit_type IN ('cast', 'crew')", name="credit_type_valid"),
        CheckConstraint("billing_order IS NULL OR billing_order >= 0", name="billing_order_nonnegative"),
    )

    movie_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("movies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    person_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("people.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    credit_type: Mapped[str] = mapped_column(String(10), nullable=False)
    job: Mapped[str | None] = mapped_column(String(150))
    character_name: Mapped[str | None] = mapped_column(String(300))
    billing_order: Mapped[int | None] = mapped_column(Integer)
    tmdb_credit_id: Mapped[str | None] = mapped_column(String(100))

    movie = relationship("Movie", back_populates="person_credits")
    person = relationship("Person", back_populates="movie_credits")
