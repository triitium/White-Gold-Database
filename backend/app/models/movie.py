from __future__ import annotations

from datetime import date, datetime
import uuid

from sqlalchemy import BigInteger, CheckConstraint, Date, DateTime, ForeignKey, Index, Integer, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Movie(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "movies"
    __table_args__ = (
        CheckConstraint(
            "release_year IS NULL OR (release_year >= 1880 AND release_year <= 2200)",
            name="release_year_range",
        ),
        CheckConstraint(
            "runtime_minutes IS NULL OR runtime_minutes > 0",
            name="runtime_positive",
        ),
        Index("ix_movies_title", "title"),
        Index("ix_movies_release_date", "release_date"),
    )

    title: Mapped[str] = mapped_column(String(500), nullable=False)
    original_title: Mapped[str | None] = mapped_column(String(500))
    release_year: Mapped[int | None] = mapped_column(Integer)
    release_date: Mapped[date | None] = mapped_column(Date)
    runtime_minutes: Mapped[int | None] = mapped_column(Integer)
    overview: Mapped[str | None] = mapped_column(Text)
    editorial_note: Mapped[str | None] = mapped_column(Text)

    poster_url: Mapped[str | None] = mapped_column(Text)
    poster_path: Mapped[str | None] = mapped_column(Text)

    tmdb_id: Mapped[int | None] = mapped_column(BigInteger, unique=True)
    imdb_id: Mapped[str | None] = mapped_column(String(20), unique=True)

    created_by_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    deleted_by_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
    )

    created_by = relationship("User", foreign_keys=[created_by_id])
    deleted_by = relationship("User", foreign_keys=[deleted_by_id])

    person_credits = relationship(
        "MoviePerson",
        back_populates="movie",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    genres = relationship(
        "MovieGenre",
        back_populates="movie",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    countries = relationship(
        "MovieCountry",
        back_populates="movie",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    languages = relationship(
        "MovieLanguage",
        back_populates="movie",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    studios = relationship(
        "MovieStudio",
        back_populates="movie",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    user_states = relationship(
        "UserMovie",
        back_populates="movie",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    reviews = relationship(
        "UserReview",
        back_populates="movie",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    external_ratings = relationship(
        "ExternalRating",
        back_populates="movie",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    links = relationship(
        "MovieLink",
        back_populates="movie",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
