from __future__ import annotations

from datetime import date
from uuid import UUID

from pydantic import BaseModel, Field


class MoviePersonInput(BaseModel):
    person_id: UUID
    credit_type: str = Field(pattern=r"^(cast|crew)$")
    job: str | None = Field(default=None, max_length=150)
    character_name: str | None = Field(default=None)
    billing_order: int | None = Field(default=None, ge=0)
    tmdb_credit_id: str | None = Field(default=None, max_length=100)


class MovieLanguageInput(BaseModel):
    language_id: UUID
    is_original: bool = False


class MovieLinkInput(BaseModel):
    source: str = Field(min_length=1, max_length=50)
    url: str = Field(min_length=1, max_length=2000)
    label: str | None = Field(default=None, max_length=150)


class MovieCreate(BaseModel):
    title: str = Field(min_length=1, max_length=500)
    original_title: str | None = Field(default=None, max_length=500)
    release_year: int | None = Field(default=None, ge=1880, le=2200)
    release_date: date | None = None
    runtime_minutes: int | None = Field(default=None, gt=0)
    overview: str | None = None
    editorial_note: str | None = None
    poster_url: str | None = None
    poster_path: str | None = None
    tmdb_id: int | None = None
    imdb_id: str | None = Field(default=None, max_length=20)
    genre_ids: list[UUID] = Field(default_factory=list)
    country_ids: list[UUID] = Field(default_factory=list)
    languages: list[MovieLanguageInput] = Field(default_factory=list)
    studio_ids: list[UUID] = Field(default_factory=list)
    person_credits: list[MoviePersonInput] = Field(default_factory=list)
    links: list[MovieLinkInput] = Field(default_factory=list)


class MovieUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=500)
    original_title: str | None = Field(default=None, max_length=500)
    release_year: int | None = Field(default=None, ge=1880, le=2200)
    release_date: date | None = None
    runtime_minutes: int | None = Field(default=None, gt=0)
    overview: str | None = None
    editorial_note: str | None = None
    poster_url: str | None = None
    poster_path: str | None = None
    tmdb_id: int | None = None
    imdb_id: str | None = Field(default=None, max_length=20)
    genre_ids: list[UUID] | None = None
    country_ids: list[UUID] | None = None
    languages: list[MovieLanguageInput] | None = None
    studio_ids: list[UUID] | None = None
    person_credits: list[MoviePersonInput] | None = None
    links: list[MovieLinkInput] | None = None
