from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class MovieListCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str | None = None


class MovieListUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None


class MovieListItemCreate(BaseModel):
    movie_id: UUID
    note: str | None = None


class MovieListItemUpdate(BaseModel):
    note: str | None = None


class MovieListReorder(BaseModel):
    movie_ids: list[UUID]


class MovieListOwnerRead(BaseModel):
    id: UUID
    username: str


class MovieListMovieRead(BaseModel):
    id: UUID
    title: str
    original_title: str | None
    release_year: int | None
    poster_url: str | None
    poster_path: str | None


class MovieListEntryRead(BaseModel):
    movie: MovieListMovieRead
    position: int
    note: str | None


class MovieListSummaryRead(BaseModel):
    id: UUID
    title: str
    description: str | None
    created_by: MovieListOwnerRead | None
    item_count: int
    created_at: datetime
    updated_at: datetime


class MovieListRead(BaseModel):
    id: UUID
    title: str
    description: str | None
    created_by: MovieListOwnerRead | None
    items: list[MovieListEntryRead]
    created_at: datetime
    updated_at: datetime
