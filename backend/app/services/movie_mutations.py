from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.movie import Movie
from app.services.audit import (
    AUDIT_HARD_DELETE,
    AUDIT_RESTORE,
    AUDIT_SOFT_DELETE,
    AUDIT_UPDATE,
    log_audit,
)
from app.services.movie_loader import reload_movie_full
from app.services.movie_snapshot import movie_snapshot


async def snapshot_before_change(
    session: AsyncSession,
    movie: Movie,
) -> dict:
    loaded = await reload_movie_full(
        session,
        movie.id,
        include_deleted=True,
    )
    return movie_snapshot(loaded)


async def finish_movie_update(
    session: AsyncSession,
    *,
    movie_id: UUID,
    actor_user_id: UUID,
    before_snapshot: dict,
) -> Movie:
    """
    Call after applying scalar/relation changes and flushing them.
    Adds the UPDATE audit record, but does not commit.
    """
    await session.flush()

    movie = await reload_movie_full(
        session,
        movie_id,
        include_deleted=True,
    )
    after_snapshot = movie_snapshot(movie)

    await log_audit(
        session,
        actor_user_id=actor_user_id,
        action=AUDIT_UPDATE,
        entity_type="movie",
        entity_id=movie.id,
        before_data=before_snapshot,
        after_data=after_snapshot,
        reduce_to_diff=True,
    )

    return movie


async def soft_delete_movie(
    session: AsyncSession,
    *,
    movie: Movie,
    actor_user_id: UUID,
) -> Movie:
    before = await snapshot_before_change(session, movie)

    movie.deleted_at = datetime.now(timezone.utc)
    movie.deleted_by_id = actor_user_id

    await session.flush()

    movie = await reload_movie_full(
        session,
        movie.id,
        include_deleted=True,
    )
    after = movie_snapshot(movie)

    await log_audit(
        session,
        actor_user_id=actor_user_id,
        action=AUDIT_SOFT_DELETE,
        entity_type="movie",
        entity_id=movie.id,
        before_data=before,
        after_data=after,
        reduce_to_diff=True,
    )

    return movie


async def restore_movie(
    session: AsyncSession,
    *,
    movie: Movie,
    actor_user_id: UUID,
) -> Movie:
    before = await snapshot_before_change(session, movie)

    movie.deleted_at = None
    movie.deleted_by_id = None

    await session.flush()

    movie = await reload_movie_full(
        session,
        movie.id,
        include_deleted=True,
    )
    after = movie_snapshot(movie)

    await log_audit(
        session,
        actor_user_id=actor_user_id,
        action=AUDIT_RESTORE,
        entity_type="movie",
        entity_id=movie.id,
        before_data=before,
        after_data=after,
        reduce_to_diff=True,
    )

    return movie


async def hard_delete_movie(
    session: AsyncSession,
    *,
    movie: Movie,
    actor_user_id: UUID,
) -> None:
    # Full snapshot MUST be captured before delete/cascade.
    loaded = await reload_movie_full(
        session,
        movie.id,
        include_deleted=True,
    )
    before = movie_snapshot(loaded)
    entity_id = loaded.id

    await session.delete(loaded)
    await session.flush()

    await log_audit(
        session,
        actor_user_id=actor_user_id,
        action=AUDIT_HARD_DELETE,
        entity_type="movie",
        entity_id=entity_id,
        before_data=before,
        after_data=None,
        reduce_to_diff=False,
    )
