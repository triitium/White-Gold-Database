from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel


class GenreRead(BaseModel):
    id: UUID
    name: str


class CountryRead(BaseModel):
    id: UUID
    name: str
    iso2: str | None
    iso3: str | None


class LanguageRead(BaseModel):
    id: UUID
    name: str
    iso_code: str
    is_original: bool


class StudioRead(BaseModel):
    id: UUID
    name: str


class PersonCreditRead(BaseModel):
    credit_id: UUID
    person_id: UUID
    name: str
    credit_type: str
    job: str | None
    character_name: str | None
    billing_order: int | None


class ExternalRatingRead(BaseModel):
    source: str
    rating_type: str
    value: float
    scale: float
    vote_count: int | None
    source_url: str | None


class MovieLinkRead(BaseModel):
    id: UUID
    source: str
    url: str
    label: str | None


class MovieRead(BaseModel):
    id: UUID
    title: str
    original_title: str | None
    release_year: int | None
    release_date: date | None
    runtime_minutes: int | None
    overview: str | None
    editorial_note: str | None
    poster_url: str | None
    poster_path: str | None
    tmdb_id: int | None
    imdb_id: str | None

    genres: list[GenreRead]
    countries: list[CountryRead]
    languages: list[LanguageRead]
    studios: list[StudioRead]
    credits: list[PersonCreditRead]
    links: list[MovieLinkRead]
    external_ratings: list[ExternalRatingRead]

    community_rating: float | None
    rating_count: int
    created_at: datetime
    updated_at: datetime


class MovieListItem(BaseModel):
    id: UUID
    title: str
    original_title: str | None
    release_year: int | None
    runtime_minutes: int | None
    poster_url: str | None
    poster_path: str | None
    genres: list[str]

    imdb_rating: float | None
    rt_critics_rating: float | None
    rt_audience_rating: float | None
    metacritic_critics_rating: float | None
    metacritic_audience_rating: float | None

    community_rating: float | None
    rating_count: int
