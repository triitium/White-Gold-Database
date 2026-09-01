from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.review import UserReview
from app.models.user import User
from app.models.user_movie import UserMovie
from app.schemas.review import ReviewCreate, ReviewUpdate
from app.services.user_movie import require_active_movie


async def get_review_by_id(
    session: AsyncSession,
    review_id: UUID,
) -> UserReview | None:
    return await session.scalar(
        select(UserReview)
        .where(UserReview.id == review_id)
        .options(selectinload(UserReview.user))
    )


async def get_user_review_for_movie(
    session: AsyncSession,
    *,
    user_id: UUID,
    movie_id: UUID,
) -> UserReview | None:
    return await session.scalar(
        select(UserReview)
        .where(
            UserReview.user_id == user_id,
            UserReview.movie_id == movie_id,
        )
        .options(selectinload(UserReview.user))
    )


async def create_review(
    session: AsyncSession,
    *,
    user_id: UUID,
    movie_id: UUID,
    data: ReviewCreate,
) -> UserReview:
    await require_active_movie(session, movie_id)

    existing = await get_user_review_for_movie(
        session,
        user_id=user_id,
        movie_id=movie_id,
    )

    if existing is not None:
        raise ValueError("User already has a review for this movie")

    review = UserReview(
        user_id=user_id,
        movie_id=movie_id,
        title=data.title.strip() if data.title else None,
        body=data.body.strip(),
        contains_spoilers=data.contains_spoilers,
    )

    session.add(review)
    await session.flush()

    return await get_review_by_id(session, review.id)


async def update_review(
    session: AsyncSession,
    *,
    review: UserReview,
    data: ReviewUpdate,
) -> UserReview:
    changes = data.model_dump(exclude_unset=True)

    for field, value in changes.items():
        if field in {"title", "body"} and isinstance(value, str):
            value = value.strip()

        setattr(review, field, value)

    await session.flush()

    return await get_review_by_id(session, review.id)


async def delete_review(
    session: AsyncSession,
    *,
    review: UserReview,
) -> None:
    await session.delete(review)
    await session.flush()


async def rating_for_review(
    session: AsyncSession,
    review: UserReview,
) -> int | None:
    return await session.scalar(
        select(UserMovie.rating).where(
            UserMovie.user_id == review.user_id,
            UserMovie.movie_id == review.movie_id,
        )
    )
