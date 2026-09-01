from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.movie import Movie
from app.models.user_movie import UserMovie
from app.schemas.user_movie import UserMovieUpdate


async def require_active_movie(
    session: AsyncSession,
    movie_id: UUID,
) -> Movie:
    movie = await session.scalar(
        select(Movie).where(
            Movie.id == movie_id,
            Movie.deleted_at.is_(None),
        )
    )

    if movie is None:
        raise ValueError("Movie not found")

    return movie


async def get_user_movie(
    session: AsyncSession,
    *,
    user_id: UUID,
    movie_id: UUID,
) -> UserMovie | None:
    return await session.scalar(
        select(UserMovie).where(
            UserMovie.user_id == user_id,
            UserMovie.movie_id == movie_id,
        )
    )


async def update_user_movie(
    session: AsyncSession,
    *,
    user_id: UUID,
    movie_id: UUID,
    data: UserMovieUpdate,
) -> UserMovie:
    await require_active_movie(session, movie_id)

    state = await get_user_movie(
        session,
        user_id=user_id,
        movie_id=movie_id,
    )

    if state is None:
        state = UserMovie(
            user_id=user_id,
            movie_id=movie_id,
            rating=None,
            watched=False,
            favorite=False,
        )
        session.add(state)

    changes = data.model_dump(exclude_unset=True)

    for field, value in changes.items():
        setattr(state, field, value)

    await session.flush()
    return state


async def clear_user_movie(
    session: AsyncSession,
    *,
    user_id: UUID,
    movie_id: UUID,
) -> None:
    state = await get_user_movie(
        session,
        user_id=user_id,
        movie_id=movie_id,
    )

    if state is None:
        return

    await session.delete(state)
    await session.flush()
