from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class ReviewCreate(BaseModel):
    title: str | None = Field(default=None, max_length=300)
    body: str = Field(min_length=1)
    contains_spoilers: bool = False


class ReviewUpdate(BaseModel):
    title: str | None = Field(default=None, max_length=300)
    body: str | None = Field(default=None, min_length=1)
    contains_spoilers: bool | None = None


class ReviewAuthorRead(BaseModel):
    id: UUID
    username: str


class UserReviewRead(BaseModel):
    id: UUID
    movie_id: UUID
    user: ReviewAuthorRead

    title: str | None
    body: str
    contains_spoilers: bool

    rating: int | None

    created_at: datetime
    updated_at: datetime
