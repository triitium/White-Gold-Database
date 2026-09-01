from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status

from app.api.deps import CsrfProtected, CurrentUser, SessionDep
from app.integrations.tmdb import TmdbError, tmdb_client
from app.schemas.tmdb import TmdbMoviePreview, TmdbMovieSearchResponse
from app.services import tmdb_import as tmdb_import_service


router = APIRouter(
    prefix="/tmdb",
    tags=["tmdb"],
)


@router.get(
    "/search",
    response_model=TmdbMovieSearchResponse,
)
async def search_tmdb_movies(
    current_user: CurrentUser,
    q: Annotated[str, Query(min_length=1, max_length=200)],
    page: Annotated[int, Query(ge=1, le=500)] = 1,
    year: Annotated[int | None, Query(ge=1880, le=2200)] = None,
) -> TmdbMovieSearchResponse:
    try:
        return await tmdb_client.search_movies(
            q,
            page=page,
            year=year,
        )
    except TmdbError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc


@router.get(
    "/movies/{tmdb_id}/preview",
    response_model=TmdbMoviePreview,
)
async def preview_tmdb_movie(
    tmdb_id: int,
    current_user: CurrentUser,
) -> TmdbMoviePreview:
    try:
        return await tmdb_client.movie_preview(tmdb_id)
    except TmdbError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc


@router.post(
    "/movies/{tmdb_id}/import",
    status_code=status.HTTP_201_CREATED,
)
async def import_tmdb_movie(
    tmdb_id: int,
    session: SessionDep,
    current_user: CurrentUser,
    _csrf: CsrfProtected,
) -> dict[str, str]:
    try:
        movie = await tmdb_import_service.import_movie_from_tmdb(
            session,
            tmdb_id=tmdb_id,
            created_by_id=current_user.id,
        )

        # Movie + all reference relations + CREATE AuditLog are committed
        # atomically here.
        await session.commit()

        return {
            "id": str(movie.id),
        }

    except ValueError as exc:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    except TmdbError as exc:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc

    except Exception:
        await session.rollback()
        raise
