from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.movie import Movie
from app.models.movie_list import MovieList, MovieListItem
from app.schemas.movie_list import (
    MovieListCreate,
    MovieListItemCreate,
    MovieListItemUpdate,
    MovieListUpdate,
)
from app.services.audit import (
    AUDIT_CREATE,
    AUDIT_SOFT_DELETE,
    AUDIT_UPDATE,
    log_audit,
)


def _clean_required(value: str) -> str:
    value = value.strip()
    if not value:
        raise ValueError("Title must not be empty")
    return value


def _clean_optional(value: str | None) -> str | None:
    if value is None:
        return None

    value = value.strip()
    return value or None


def _touch(movie_list: MovieList) -> None:
    movie_list.updated_at = datetime.now(timezone.utc)


def _list_snapshot(movie_list: MovieList) -> dict:
    return {
        "id": str(movie_list.id),
        "title": movie_list.title,
        "description": movie_list.description,
        "created_by_id": (
            str(movie_list.created_by_id)
            if movie_list.created_by_id is not None
            else None
        ),
        "deleted_at": (
            movie_list.deleted_at.isoformat()
            if movie_list.deleted_at is not None
            else None
        ),
    }


def _item_snapshot(item: MovieListItem) -> dict:
    return {
        "movie_id": str(item.movie_id),
        "position": item.position,
        "note": item.note,
    }


async def list_movie_lists(
    session: AsyncSession,
    *,
    page: int,
    page_size: int,
) -> tuple[list[MovieList], int]:
    condition = MovieList.deleted_at.is_(None)

    total = int(
        (
            await session.scalar(
                select(func.count(MovieList.id)).where(condition)
            )
        )
        or 0
    )

    rows = (
        await session.scalars(
            select(MovieList)
            .where(condition)
            .options(
                selectinload(MovieList.created_by),
                selectinload(MovieList.items),
            )
            .order_by(
                MovieList.updated_at.desc(),
                MovieList.id.desc(),
            )
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
    ).all()

    return list(rows), total


async def list_my_movie_lists(
    session: AsyncSession,
    *,
    user_id: UUID,
) -> list[MovieList]:
    rows = (
        await session.scalars(
            select(MovieList)
            .where(
                MovieList.created_by_id == user_id,
                MovieList.deleted_at.is_(None),
            )
            .options(
                selectinload(MovieList.created_by),
                selectinload(MovieList.items),
            )
            .order_by(
                MovieList.updated_at.desc(),
                MovieList.id.desc(),
            )
        )
    ).all()

    return list(rows)


async def get_movie_list(
    session: AsyncSession,
    list_id: UUID,
) -> MovieList | None:
    return (
        await session.execute(
            select(MovieList)
            .where(
                MovieList.id == list_id,
                MovieList.deleted_at.is_(None),
            )
            .options(
                selectinload(MovieList.created_by),
                selectinload(MovieList.items).selectinload(
                    MovieListItem.movie
                ),
            )
            .execution_options(populate_existing=True)
        )
    ).scalar_one_or_none()


def require_owner(
    movie_list: MovieList,
    *,
    user_id: UUID,
) -> None:
    if movie_list.created_by_id != user_id:
        raise PermissionError(
            "You may only modify your own list"
        )


async def create_movie_list(
    session: AsyncSession,
    *,
    data: MovieListCreate,
    user_id: UUID,
) -> MovieList:
    movie_list = MovieList(
        title=_clean_required(data.title),
        description=_clean_optional(data.description),
        created_by_id=user_id,
    )

    session.add(movie_list)
    await session.flush()

    await log_audit(
        session,
        actor_user_id=user_id,
        action=AUDIT_CREATE,
        entity_type="movie_list",
        entity_id=movie_list.id,
        before_data=None,
        after_data=_list_snapshot(movie_list),
    )

    return movie_list


async def update_movie_list(
    session: AsyncSession,
    *,
    movie_list: MovieList,
    data: MovieListUpdate,
    user_id: UUID,
) -> MovieList:
    require_owner(movie_list, user_id=user_id)

    before = _list_snapshot(movie_list)

    if "title" in data.model_fields_set:
        if data.title is None:
            raise ValueError("Title must not be empty")
        movie_list.title = _clean_required(data.title)

    if "description" in data.model_fields_set:
        movie_list.description = _clean_optional(
            data.description
        )

    _touch(movie_list)
    await session.flush()

    await log_audit(
        session,
        actor_user_id=user_id,
        action=AUDIT_UPDATE,
        entity_type="movie_list",
        entity_id=movie_list.id,
        before_data=before,
        after_data=_list_snapshot(movie_list),
    )

    return movie_list


async def soft_delete_movie_list(
    session: AsyncSession,
    *,
    movie_list: MovieList,
    actor_user_id: UUID,
    require_actor_owner: bool = True,
    action: str = AUDIT_SOFT_DELETE,
) -> None:
    if require_actor_owner:
        require_owner(
            movie_list,
            user_id=actor_user_id,
        )

    before = _list_snapshot(movie_list)

    movie_list.deleted_at = datetime.now(timezone.utc)
    _touch(movie_list)

    await session.flush()

    await log_audit(
        session,
        actor_user_id=actor_user_id,
        action=action,
        entity_type="movie_list",
        entity_id=movie_list.id,
        before_data=before,
        after_data=_list_snapshot(movie_list),
    )


async def add_movie_list_item(
    session: AsyncSession,
    *,
    movie_list: MovieList,
    data: MovieListItemCreate,
    user_id: UUID,
) -> MovieListItem:
    require_owner(movie_list, user_id=user_id)

    movie = await session.scalar(
        select(Movie).where(
            Movie.id == data.movie_id,
            Movie.deleted_at.is_(None),
        )
    )
    if movie is None:
        raise LookupError("Movie not found")

    existing = await session.scalar(
        select(MovieListItem).where(
            MovieListItem.list_id == movie_list.id,
            MovieListItem.movie_id == data.movie_id,
        )
    )
    if existing is not None:
        raise ValueError("Movie is already in this list")

    max_position = await session.scalar(
        select(func.max(MovieListItem.position)).where(
            MovieListItem.list_id == movie_list.id
        )
    )

    item = MovieListItem(
        list_id=movie_list.id,
        movie_id=data.movie_id,
        position=(
            0
            if max_position is None
            else int(max_position) + 1
        ),
        note=_clean_optional(data.note),
    )

    session.add(item)
    _touch(movie_list)
    await session.flush()

    await log_audit(
        session,
        actor_user_id=user_id,
        action="LIST_ITEM_ADD",
        entity_type="movie_list",
        entity_id=movie_list.id,
        before_data=None,
        after_data=_item_snapshot(item),
        reduce_to_diff=False,
    )

    return item


async def update_movie_list_item(
    session: AsyncSession,
    *,
    movie_list: MovieList,
    movie_id: UUID,
    data: MovieListItemUpdate,
    user_id: UUID,
) -> MovieListItem:
    require_owner(movie_list, user_id=user_id)

    item = await session.scalar(
        select(MovieListItem).where(
            MovieListItem.list_id == movie_list.id,
            MovieListItem.movie_id == movie_id,
        )
    )
    if item is None:
        raise LookupError("List item not found")

    before = _item_snapshot(item)

    if "note" in data.model_fields_set:
        item.note = _clean_optional(data.note)

    _touch(movie_list)
    await session.flush()

    await log_audit(
        session,
        actor_user_id=user_id,
        action="LIST_ITEM_UPDATE",
        entity_type="movie_list",
        entity_id=movie_list.id,
        before_data=before,
        after_data=_item_snapshot(item),
    )

    return item


async def remove_movie_list_item(
    session: AsyncSession,
    *,
    movie_list: MovieList,
    movie_id: UUID,
    user_id: UUID,
) -> None:
    require_owner(movie_list, user_id=user_id)

    item = await session.scalar(
        select(MovieListItem).where(
            MovieListItem.list_id == movie_list.id,
            MovieListItem.movie_id == movie_id,
        )
    )
    if item is None:
        raise LookupError("List item not found")

    before = _item_snapshot(item)

    await session.delete(item)
    _touch(movie_list)
    await session.flush()

    await log_audit(
        session,
        actor_user_id=user_id,
        action="LIST_ITEM_REMOVE",
        entity_type="movie_list",
        entity_id=movie_list.id,
        before_data=before,
        after_data=None,
        reduce_to_diff=False,
    )


async def reorder_movie_list(
    session: AsyncSession,
    *,
    movie_list: MovieList,
    movie_ids: list[UUID],
    user_id: UUID,
) -> None:
    require_owner(movie_list, user_id=user_id)

    entries = (
        await session.scalars(
            select(MovieListItem).where(
                MovieListItem.list_id == movie_list.id
            )
        )
    ).all()

    current_ids = [entry.movie_id for entry in entries]

    if len(movie_ids) != len(set(movie_ids)):
        raise ValueError(
            "movie_ids must not contain duplicates"
        )

    if set(movie_ids) != set(current_ids):
        raise ValueError(
            "movie_ids must contain every movie in the list exactly once"
        )

    before = {
        "order": [
            str(entry.movie_id)
            for entry in sorted(
                entries,
                key=lambda entry: (
                    entry.position,
                    str(entry.movie_id),
                ),
            )
        ]
    }

    by_movie_id = {
        entry.movie_id: entry
        for entry in entries
    }

    for position, movie_id in enumerate(movie_ids):
        by_movie_id[movie_id].position = position

    _touch(movie_list)
    await session.flush()

    await log_audit(
        session,
        actor_user_id=user_id,
        action="LIST_REORDER",
        entity_type="movie_list",
        entity_id=movie_list.id,
        before_data=before,
        after_data={
            "order": [
                str(movie_id)
                for movie_id in movie_ids
            ]
        },
    )
