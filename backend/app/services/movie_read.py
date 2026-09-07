from __future__ import annotations

from uuid import UUID

from sqlalchemy import asc, desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.classification import MovieCountry, MovieGenre
from app.models.movie import Movie
from app.models.movie_person import MoviePerson
from app.models.review import UserReview
from app.models.user_movie import UserMovie
from app.services.movie_loader import movie_full_options


LIST_SORTS = {
    "title": Movie.title,
    "year": Movie.release_year,
    "runtime": Movie.runtime_minutes,
    "created": Movie.created_at,
    "updated": Movie.updated_at,
}


async def list_movies(
    session: AsyncSession,
    *,
    page: int,
    page_size: int,
    q: str | None,
    year_from: int | None,
    year_to: int | None,
    genre_id: UUID | None,
    country_id: UUID | None,
    actor_id: UUID | None,
    review: str,
    rating_min: int | None,
    rating_max: int | None,
    sort: str,
    direction: str,
):
    base = select(Movie).where(Movie.deleted_at.is_(None))
    count_stmt = select(func.count(func.distinct(Movie.id))).where(Movie.deleted_at.is_(None))

    conditions = []
    if q:
        needle = f"%{q.strip()}%"
        conditions.append(or_(Movie.title.ilike(needle), Movie.original_title.ilike(needle)))
    if year_from is not None:
        conditions.append(Movie.release_year >= year_from)
    if year_to is not None:
        conditions.append(Movie.release_year <= year_to)

    for condition in conditions:
        base = base.where(condition)
        count_stmt = count_stmt.where(condition)

    if genre_id is not None:
        base = base.join(MovieGenre).where(MovieGenre.genre_id == genre_id)
        count_stmt = count_stmt.join(MovieGenre).where(MovieGenre.genre_id == genre_id)

    if country_id is not None:
        base = base.join(MovieCountry).where(MovieCountry.country_id == country_id)
        count_stmt = count_stmt.join(MovieCountry).where(MovieCountry.country_id == country_id)

    if actor_id is not None:
        base = base.join(
            MoviePerson,
            MoviePerson.movie_id == Movie.id,
        ).where(
            MoviePerson.person_id == actor_id,
            MoviePerson.credit_type == "cast",
        )
        count_stmt = count_stmt.join(
            MoviePerson,
            MoviePerson.movie_id == Movie.id,
        ).where(
            MoviePerson.person_id == actor_id,
            MoviePerson.credit_type == "cast",
        )

    has_review = (
        select(UserReview.id)
        .where(UserReview.movie_id == Movie.id)
        .exists()
    )

    if review == "has":
        base = base.where(has_review)
        count_stmt = count_stmt.where(has_review)
    elif review == "none":
        base = base.where(~has_review)
        count_stmt = count_stmt.where(~has_review)

    if rating_min is not None or rating_max is not None:
        community_rating = (
            select(func.avg(UserMovie.rating))
            .where(
                UserMovie.movie_id == Movie.id,
                UserMovie.rating.is_not(None),
            )
            .correlate(Movie)
            .scalar_subquery()
        )

        if rating_min is not None:
            base = base.where(community_rating >= rating_min)
            count_stmt = count_stmt.where(community_rating >= rating_min)

        if rating_max is not None:
            base = base.where(community_rating <= rating_max)
            count_stmt = count_stmt.where(community_rating <= rating_max)

    sort_column = LIST_SORTS[sort]
    order = asc(sort_column) if direction == "asc" else desc(sort_column)

    base = (
        base.options(
            selectinload(Movie.genres).selectinload(MovieGenre.genre),
            selectinload(Movie.external_ratings),
            selectinload(Movie.user_states),
        )
        .order_by(order, Movie.id.asc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )

    total = int((await session.scalar(count_stmt)) or 0)
    rows = (await session.execute(base)).scalars().unique().all()
    return rows, total


async def get_movie(
    session: AsyncSession,
    movie_id: UUID,
    *,
    include_deleted: bool = False,
) -> Movie | None:
    stmt = select(Movie).where(Movie.id == movie_id).options(*movie_full_options())
    if not include_deleted:
        stmt = stmt.where(Movie.deleted_at.is_(None))
    return (await session.execute(stmt)).scalar_one_or_none()
