from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from app.api.deps import CsrfProtected, CurrentUser, SessionDep
from app.schemas.user_movie import UserMovieRead, UserMovieUpdate
from app.services import user_movie as user_movie_service


router = APIRouter(prefix="/movies", tags=["user-movies"])


@router.get("/{movie_id}/me", response_model=UserMovieRead | None)
async def get_my_movie_state(
    movie_id: UUID,
    session: SessionDep,
    current_user: CurrentUser,
):
    try:
        await user_movie_service.require_active_movie(session, movie_id)
    except ValueError as exc:
        raise HTTPException(404, str(exc)) from exc

    state = await user_movie_service.get_user_movie(
        session,
        user_id=current_user.id,
        movie_id=movie_id,
    )
    if state is None:
        return None
    return UserMovieRead.model_validate(state, from_attributes=True)


@router.patch("/{movie_id}/me", response_model=UserMovieRead)
async def update_my_movie_state(
    movie_id: UUID,
    data: UserMovieUpdate,
    session: SessionDep,
    current_user: CurrentUser,
    _csrf: CsrfProtected,
):
    try:
        state = await user_movie_service.update_user_movie(
            session,
            user_id=current_user.id,
            movie_id=movie_id,
            data=data,
        )
        await session.commit()
        return UserMovieRead.model_validate(state, from_attributes=True)
    except ValueError as exc:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.delete("/{movie_id}/me", status_code=status.HTTP_204_NO_CONTENT)
async def clear_my_movie_state(
    movie_id: UUID,
    session: SessionDep,
    current_user: CurrentUser,
    _csrf: CsrfProtected,
) -> None:
    try:
        await user_movie_service.require_active_movie(session, movie_id)
        await user_movie_service.clear_user_movie(
            session,
            user_id=current_user.id,
            movie_id=movie_id,
        )
        await session.commit()
    except ValueError as exc:
        await session.rollback()
        raise HTTPException(404, str(exc)) from exc
