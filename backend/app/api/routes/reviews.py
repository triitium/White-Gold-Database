from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.api.deps import AdminUser, CsrfProtected, CurrentUser, SessionDep
from app.mappers.review import review_to_read
from app.models.review import UserReview
from app.models.user_movie import UserMovie
from app.schemas.review import ReviewCreate, ReviewUpdate, UserReviewRead
from app.services import review as review_service
from app.services.audit import log_audit
from app.services.user_movie import require_active_movie


router = APIRouter(prefix="/movies", tags=["reviews"])


@router.get("/{movie_id}/reviews", response_model=list[UserReviewRead])
async def list_movie_reviews(movie_id: UUID, session: SessionDep) -> list[UserReviewRead]:
    try:
        await require_active_movie(session, movie_id)
    except ValueError as exc:
        raise HTTPException(404, str(exc)) from exc

    reviews = (
        await session.scalars(
            select(UserReview)
            .where(UserReview.movie_id == movie_id)
            .options(selectinload(UserReview.user))
            .order_by(UserReview.created_at.desc())
        )
    ).all()

    rating_rows = (
        await session.execute(
            select(UserMovie.user_id, UserMovie.rating).where(UserMovie.movie_id == movie_id)
        )
    ).all()
    ratings = {user_id: rating for user_id, rating in rating_rows}

    return [review_to_read(review, rating=ratings.get(review.user_id)) for review in reviews]


@router.post("/{movie_id}/reviews", response_model=UserReviewRead, status_code=status.HTTP_201_CREATED)
async def create_review(
    movie_id: UUID,
    data: ReviewCreate,
    session: SessionDep,
    current_user: CurrentUser,
    _csrf: CsrfProtected,
) -> UserReviewRead:
    try:
        review = await review_service.create_review(
            session,
            user_id=current_user.id,
            movie_id=movie_id,
            data=data,
        )
        await session.commit()
        rating = await review_service.rating_for_review(session, review)
        return review_to_read(review, rating=rating)
    except ValueError as exc:
        await session.rollback()
        message = str(exc)
        raise HTTPException(
            status_code=(status.HTTP_409_CONFLICT if "already has a review" in message else status.HTTP_404_NOT_FOUND),
            detail=message,
        ) from exc


@router.patch("/{movie_id}/reviews/{review_id}", response_model=UserReviewRead)
async def update_review(
    movie_id: UUID,
    review_id: UUID,
    data: ReviewUpdate,
    session: SessionDep,
    current_user: CurrentUser,
    _csrf: CsrfProtected,
) -> UserReviewRead:
    review = await review_service.get_review_by_id(session, review_id)
    if review is None or review.movie_id != movie_id:
        raise HTTPException(404, "Review not found")
    if review.user_id != current_user.id:
        raise HTTPException(403, "You may only edit your own review")

    review = await review_service.update_review(session, review=review, data=data)
    await session.commit()
    rating = await review_service.rating_for_review(session, review)
    return review_to_read(review, rating=rating)


@router.delete("/{movie_id}/reviews/{review_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_own_review(
    movie_id: UUID,
    review_id: UUID,
    session: SessionDep,
    current_user: CurrentUser,
    _csrf: CsrfProtected,
) -> None:
    review = await review_service.get_review_by_id(session, review_id)
    if review is None or review.movie_id != movie_id:
        raise HTTPException(404, "Review not found")
    if review.user_id != current_user.id:
        raise HTTPException(403, "You may only delete your own review")
    await review_service.delete_review(session, review=review)
    await session.commit()


admin_router = APIRouter(prefix="/admin/reviews", tags=["admin", "reviews"])


@admin_router.delete("/{review_id}", status_code=status.HTTP_204_NO_CONTENT)
async def admin_delete_review(
    review_id: UUID,
    session: SessionDep,
    admin: AdminUser,
    _csrf: CsrfProtected,
) -> None:
    review = await review_service.get_review_by_id(session, review_id)
    if review is None:
        raise HTTPException(404, "Review not found")

    before = {
        "id": str(review.id),
        "movie_id": str(review.movie_id),
        "user_id": str(review.user_id),
        "username": review.user.username,
        "title": review.title,
        "body": review.body,
        "contains_spoilers": review.contains_spoilers,
    }
    entity_id = review.id
    await review_service.delete_review(session, review=review)
    await log_audit(
        session,
        actor_user_id=admin.id,
        action="MODERATION_DELETE",
        entity_type="review",
        entity_id=entity_id,
        before_data=before,
        after_data=None,
        reduce_to_diff=False,
    )
    await session.commit()
