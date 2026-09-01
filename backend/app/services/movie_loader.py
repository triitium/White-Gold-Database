from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.classification import (
    MovieCountry,
    MovieGenre,
    MovieLanguage,
    MovieStudio,
)
from app.models.movie import Movie
from app.models.movie_person import MoviePerson


def movie_full_options():
    return (
        selectinload(Movie.genres)
        .selectinload(MovieGenre.genre),

        selectinload(Movie.countries)
        .selectinload(MovieCountry.country),

        selectinload(Movie.languages)
        .selectinload(MovieLanguage.language),

        selectinload(Movie.studios)
        .selectinload(MovieStudio.studio),

        selectinload(Movie.person_credits)
        .selectinload(MoviePerson.person),

        selectinload(Movie.links),
        selectinload(Movie.external_ratings),
        selectinload(Movie.user_states),
        selectinload(Movie.reviews),
    )


async def get_movie_full(
    session: AsyncSession,
    movie_id: UUID,
    *,
    include_deleted: bool = False,
) -> Movie | None:
    stmt = (
        select(Movie)
        .where(Movie.id == movie_id)
        .options(*movie_full_options())
    )

    if not include_deleted:
        stmt = stmt.where(Movie.deleted_at.is_(None))

    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def reload_movie_full(
    session: AsyncSession,
    movie_id: UUID,
    *,
    include_deleted: bool = True,
) -> Movie:
    """
    Expire current ORM state, then reload the full Movie graph.

    Use after relation changes and before snapshotting.
    """
    session.expire_all()

    movie = await get_movie_full(
        session,
        movie_id,
        include_deleted=include_deleted,
    )

    if movie is None:
        raise RuntimeError(
            f"Movie {movie_id} disappeared while reloading"
        )

    return movie
