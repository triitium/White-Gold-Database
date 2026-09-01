"""
A fuller admin router. Merge these handlers with the existing admin.py
(create-user route) or replace that file with a combined version.
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.api.deps import AdminUser, CsrfProtected, SessionDep
from app.models.audit import AuditLog
from app.models.movie import Movie
from app.models.user import User
from app.schemas.admin import (
    AuditActorRead,
    AuditLogRead,
    DeletedMovieRead,
)
from app.schemas.user import UserActiveUpdate, UserRead, UserRoleUpdate
from app.services import admin_user as admin_user_service


router = APIRouter(
    prefix="/admin",
    tags=["admin"],
)


@router.get("/users", response_model=list[UserRead])
async def list_users(
    session: SessionDep,
    admin: AdminUser,
    q: Annotated[str | None, Query(max_length=200)] = None,
):
    users = await admin_user_service.list_users(session, q=q)
    return [UserRead.model_validate(x) for x in users]


@router.patch(
    "/users/{user_id}/role",
    response_model=UserRead,
)
async def update_user_role(
    user_id: UUID,
    data: UserRoleUpdate,
    session: SessionDep,
    admin: AdminUser,
    _csrf: CsrfProtected,
):
    user = await session.get(User, user_id)

    if user is None:
        raise HTTPException(404, "User not found")

    try:
        user = await admin_user_service.change_role(
            session,
            target=user,
            new_role=data.role,
            actor_user_id=admin.id,
        )
        await session.commit()
        return UserRead.model_validate(user)
    except ValueError as exc:
        await session.rollback()
        raise HTTPException(422, str(exc)) from exc


@router.patch(
    "/users/{user_id}/active",
    response_model=UserRead,
)
async def update_user_active(
    user_id: UUID,
    data: UserActiveUpdate,
    session: SessionDep,
    admin: AdminUser,
    _csrf: CsrfProtected,
):
    if user_id == admin.id and not data.is_active:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "You cannot deactivate your own active admin session",
        )

    user = await session.get(User, user_id)

    if user is None:
        raise HTTPException(404, "User not found")

    user = await admin_user_service.change_active(
        session,
        target=user,
        is_active=data.is_active,
        actor_user_id=admin.id,
    )
    await session.commit()

    return UserRead.model_validate(user)


@router.get(
    "/deleted-movies",
    response_model=list[DeletedMovieRead],
)
async def list_deleted_movies(
    session: SessionDep,
    admin: AdminUser,
):
    rows = (
        await session.execute(
            select(Movie)
            .where(Movie.deleted_at.is_not(None))
            .options(selectinload(Movie.deleted_by))
            .order_by(Movie.deleted_at.desc())
        )
    ).scalars().all()

    return [
        DeletedMovieRead(
            id=movie.id,
            title=movie.title,
            original_title=movie.original_title,
            release_year=movie.release_year,
            poster_url=movie.poster_url,
            poster_path=movie.poster_path,
            deleted_at=movie.deleted_at,
            deleted_by_username=(
                movie.deleted_by.username
                if movie.deleted_by is not None
                else None
            ),
        )
        for movie in rows
    ]


@router.get(
    "/audit",
    response_model=list[AuditLogRead],
)
async def list_audit(
    session: SessionDep,
    admin: AdminUser,
    entity_type: Annotated[str | None, Query(max_length=100)] = None,
    entity_id: UUID | None = None,
    action: Annotated[str | None, Query(max_length=50)] = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
):
    stmt = (
        select(AuditLog)
        .options(selectinload(AuditLog.actor))
        .order_by(AuditLog.created_at.desc())
        .limit(limit)
    )

    if entity_type:
        stmt = stmt.where(AuditLog.entity_type == entity_type)

    if entity_id:
        stmt = stmt.where(AuditLog.entity_id == entity_id)

    if action:
        stmt = stmt.where(AuditLog.action == action)

    rows = (await session.scalars(stmt)).all()

    return [
        AuditLogRead(
            id=row.id,
            actor=(
                AuditActorRead(
                    id=row.actor.id,
                    username=row.actor.username,
                )
                if row.actor is not None
                else None
            ),
            action=row.action,
            entity_type=row.entity_type,
            entity_id=row.entity_id,
            before_data=row.before_data,
            after_data=row.after_data,
            created_at=row.created_at,
        )
        for row in rows
    ]
