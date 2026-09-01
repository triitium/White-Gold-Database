from __future__ import annotations

import uuid

from sqlalchemy import BigInteger, Boolean, ForeignKey, Index, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Genre(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "genres"

    name: Mapped[str] = mapped_column(String(150), unique=True, nullable=False)
    tmdb_id: Mapped[int | None] = mapped_column(BigInteger, unique=True)

    movies = relationship("MovieGenre", back_populates="genre", passive_deletes=True)


class MovieGenre(Base):
    __tablename__ = "movie_genres"

    movie_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("movies.id", ondelete="CASCADE"), primary_key=True
    )
    genre_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("genres.id", ondelete="CASCADE"), primary_key=True
    )

    movie = relationship("Movie", back_populates="genres")
    genre = relationship("Genre", back_populates="movies")


class Country(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "countries"

    name: Mapped[str] = mapped_column(String(150), unique=True, nullable=False)
    iso2: Mapped[str | None] = mapped_column(String(2), unique=True)
    iso3: Mapped[str | None] = mapped_column(String(3), unique=True)

    movies = relationship("MovieCountry", back_populates="country", passive_deletes=True)


class MovieCountry(Base):
    __tablename__ = "movie_countries"

    movie_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("movies.id", ondelete="CASCADE"), primary_key=True
    )
    country_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("countries.id", ondelete="CASCADE"), primary_key=True
    )

    movie = relationship("Movie", back_populates="countries")
    country = relationship("Country", back_populates="movies")


class Language(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "languages"

    iso_code: Mapped[str] = mapped_column(String(10), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(150), unique=True, nullable=False)

    movies = relationship("MovieLanguage", back_populates="language", passive_deletes=True)


class MovieLanguage(Base):
    __tablename__ = "movie_languages"

    movie_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("movies.id", ondelete="CASCADE"), primary_key=True
    )
    language_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("languages.id", ondelete="CASCADE"), primary_key=True
    )
    is_original: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    movie = relationship("Movie", back_populates="languages")
    language = relationship("Language", back_populates="movies")


class Studio(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "studios"
    __table_args__ = (Index("ix_studios_name", "name"),)

    name: Mapped[str] = mapped_column(String(300), nullable=False)
    tmdb_id: Mapped[int | None] = mapped_column(BigInteger, unique=True)

    movies = relationship("MovieStudio", back_populates="studio", passive_deletes=True)


class MovieStudio(Base):
    __tablename__ = "movie_studios"

    movie_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("movies.id", ondelete="CASCADE"), primary_key=True
    )
    studio_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("studios.id", ondelete="CASCADE"), primary_key=True
    )

    movie = relationship("Movie", back_populates="studios")
    studio = relationship("Studio", back_populates="movies")
