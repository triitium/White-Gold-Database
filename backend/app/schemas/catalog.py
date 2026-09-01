from __future__ import annotations

from datetime import date
from uuid import UUID

from pydantic import BaseModel, Field


class GenreOption(BaseModel):
    id: UUID
    name: str
    tmdb_id: int | None = None


class GenreCreate(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    tmdb_id: int | None = None


class GenreUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=150)
    tmdb_id: int | None = None


class CountryOption(BaseModel):
    id: UUID
    name: str
    iso2: str | None
    iso3: str | None


class CountryCreate(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    iso2: str | None = Field(default=None, min_length=2, max_length=2)
    iso3: str | None = Field(default=None, min_length=3, max_length=3)


class CountryUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=150)
    iso2: str | None = Field(default=None, min_length=2, max_length=2)
    iso3: str | None = Field(default=None, min_length=3, max_length=3)


class LanguageOption(BaseModel):
    id: UUID
    name: str
    iso_code: str


class LanguageCreate(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    iso_code: str = Field(min_length=1, max_length=10)


class LanguageUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=150)
    iso_code: str | None = Field(default=None, min_length=1, max_length=10)


class StudioOption(BaseModel):
    id: UUID
    name: str
    tmdb_id: int | None = None


class StudioCreate(BaseModel):
    name: str = Field(min_length=1, max_length=300)
    tmdb_id: int | None = None


class StudioUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=300)
    tmdb_id: int | None = None


class PersonOption(BaseModel):
    id: UUID
    name: str
    birth_date: date | None = None
    death_date: date | None = None
    biography: str | None = None
    profile_url: str | None = None
    profile_path: str | None = None
    tmdb_id: int | None
    imdb_id: str | None


class PersonCreate(BaseModel):
    name: str = Field(min_length=1, max_length=300)
    birth_date: date | None = None
    death_date: date | None = None
    biography: str | None = None
    profile_url: str | None = None
    profile_path: str | None = None
    tmdb_id: int | None = None
    imdb_id: str | None = Field(default=None, max_length=20)


class PersonUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=300)
    birth_date: date | None = None
    death_date: date | None = None
    biography: str | None = None
    profile_url: str | None = None
    profile_path: str | None = None
    tmdb_id: int | None = None
    imdb_id: str | None = Field(default=None, max_length=20)
