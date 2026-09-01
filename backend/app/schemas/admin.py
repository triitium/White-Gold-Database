from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel

from app.schemas.user import UserRead


class AuditActorRead(BaseModel):
    id: UUID
    username: str


class AuditLogRead(BaseModel):
    id: UUID
    actor: AuditActorRead | None

    action: str
    entity_type: str
    entity_id: UUID

    before_data: dict[str, Any] | None
    after_data: dict[str, Any] | None

    created_at: datetime


class DeletedMovieRead(BaseModel):
    id: UUID
    title: str
    original_title: str | None
    release_year: int | None
    poster_url: str | None
    poster_path: str | None

    deleted_at: datetime
    deleted_by_username: str | None
