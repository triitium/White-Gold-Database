from datetime import date

from pydantic import BaseModel


class TmdbMovieSearchItem(BaseModel):
    tmdb_id: int
    title: str
    original_title: str | None
    release_date: date | None
    release_year: int | None
    overview: str | None
    poster_url: str | None


class TmdbMovieSearchResponse(BaseModel):
    page: int
    total_pages: int
    total_results: int
    results: list[TmdbMovieSearchItem]


class TmdbGenrePreview(BaseModel):
    tmdb_id: int
    name: str


class TmdbCountryPreview(BaseModel):
    iso2: str | None
    name: str


class TmdbLanguagePreview(BaseModel):
    iso_code: str
    name: str | None
    is_original: bool


class TmdbStudioPreview(BaseModel):
    tmdb_id: int
    name: str


class TmdbCreditPreview(BaseModel):
    tmdb_person_id: int
    name: str
    credit_type: str
    job: str | None = None
    character_name: str | None = None
    billing_order: int | None = None
    tmdb_credit_id: str | None = None


class TmdbMoviePreview(BaseModel):
    tmdb_id: int
    imdb_id: str | None

    title: str
    original_title: str | None

    release_date: date | None
    release_year: int | None
    runtime_minutes: int | None

    overview: str | None
    poster_url: str | None

    genres: list[TmdbGenrePreview]
    countries: list[TmdbCountryPreview]
    languages: list[TmdbLanguagePreview]
    studios: list[TmdbStudioPreview]
    credits: list[TmdbCreditPreview]
