from __future__ import annotations

from app.models.review import UserReview
from app.schemas.review import ReviewAuthorRead, UserReviewRead


def review_to_read(
    review: UserReview,
    *,
    rating: int | None,
) -> UserReviewRead:
    return UserReviewRead(
        id=review.id,
        movie_id=review.movie_id,
        user=ReviewAuthorRead(
            id=review.user.id,
            username=review.user.username,
        ),
        title=review.title,
        body=review.body,
        contains_spoilers=review.contains_spoilers,
        rating=rating,
        created_at=review.created_at,
        updated_at=review.updated_at,
    )
