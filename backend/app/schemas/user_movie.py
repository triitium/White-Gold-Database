from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class UserMovieUpdate(BaseModel):
    rating: int | None = Field(default=None, ge=0, le=100)
    watched: bool | None = None
    favorite: bool | None = None


class UserMovieRead(BaseModel):
    user_id: UUID
    movie_id: UUID

    rating: int | None
    watched: bool
    favorite: bool

    created_at: datetime
    updated_at: datetime
