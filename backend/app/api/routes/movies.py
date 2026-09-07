from __future__ import annotations

from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError

from app.api.deps import AdminUser, CsrfProtected, CurrentUser, SessionDep
from app.mappers.movie import movie_to_list_item, movie_to_read
from app.schemas.common import Page
from app.schemas.movie import MovieCreate, MovieUpdate
from app.schemas.movie_read import MovieListItem, MovieRead
from app.services import movie_manual
from app.services.movie_read import get_movie, list_movies
from app.services.movie_mutations import hard_delete_movie, restore_movie, soft_delete_movie


router = APIRouter(prefix="/movies", tags=["movies"])


@router.get("", response_model=Page[MovieListItem])
async def get_movies(
    session: SessionDep,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 25,
    q: Annotated[str | None, Query(max_length=200)] = None,
    year_from: Annotated[int | None, Query(ge=1880, le=2200)] = None,
    year_to: Annotated[int | None, Query(ge=1880, le=2200)] = None,
    genre_id: UUID | None = None,
    country_id: UUID | None = None,
    actor_id: UUID | None = None,
    review: Literal["all", "has", "none"] = "all",
    rating_min: Annotated[int | None, Query(ge=0, le=100)] = None,
    rating_max: Annotated[int | None, Query(ge=0, le=100)] = None,
    sort: Literal["title", "year", "runtime", "created", "updated"] = "title",
    direction: Literal["asc", "desc"] = "asc",
):
    if year_from is not None and year_to is not None and year_from > year_to:
        raise HTTPException(422, "year_from must be <= year_to")

    if rating_min is not None and rating_max is not None and rating_min > rating_max:
        raise HTTPException(422, "rating_min must be <= rating_max")

    rows, total = await list_movies(
        session,
        page=page,
        page_size=page_size,
        q=q,
        year_from=year_from,
        year_to=year_to,
        genre_id=genre_id,
        country_id=country_id,
        actor_id=actor_id,
        review=review,
        rating_min=rating_min,
        rating_max=rating_max,
        sort=sort,
        direction=direction,
    )
    return Page[MovieListItem].create(
        items=[movie_to_list_item(x) for x in rows],
        page=page,
        page_size=page_size,
        total=total,
    )



@router.get("/filter-options/genres")
async def get_movie_genre_options(session: SessionDep):
    """Public genre options for the movie catalogue filter."""
    from sqlalchemy import func, select

    from app.models.classification import Genre

    rows = (
        await session.scalars(
            select(Genre).order_by(func.lower(Genre.name))
        )
    ).all()

    return [
        {
            "id": str(genre.id),
            "name": genre.name,
        }
        for genre in rows
    ]


@router.get("/filter-options/actors")
async def get_movie_actor_options(
    session: SessionDep,
    q: Annotated[str, Query(min_length=1, max_length=100)],
    limit: Annotated[int, Query(ge=1, le=50)] = 20,
):
    """Search actors that have at least one cast credit."""
    from sqlalchemy import case, func, select

    from app.models.movie_person import MoviePerson
    from app.models.person import Person

    needle = q.strip()
    if not needle:
        return []

    has_cast_credit = (
        select(MoviePerson.id)
        .where(
            MoviePerson.person_id == Person.id,
            MoviePerson.credit_type == "cast",
        )
        .exists()
    )

    name_lower = func.lower(Person.name)
    needle_lower = needle.lower()

    rank = case(
        (name_lower == needle_lower, 0),
        (name_lower.like(f"{needle_lower}%"), 1),
        else_=2,
    )

    rows = (
        await session.execute(
            select(Person.id, Person.name)
            .where(
                Person.name.ilike(f"%{needle}%"),
                has_cast_credit,
            )
            .order_by(rank, name_lower, Person.id)
            .limit(limit)
        )
    ).all()

    return [
        {
            "id": str(person_id),
            "name": name,
        }
        for person_id, name in rows
    ]


@router.get("/filter-options/actors/{actor_id}")
async def get_movie_actor_option(
    actor_id: UUID,
    session: SessionDep,
):
    """Return one actor option for restoring a selected catalogue filter."""
    from sqlalchemy import select

    from app.models.movie_person import MoviePerson
    from app.models.person import Person

    has_cast_credit = (
        select(MoviePerson.id)
        .where(
            MoviePerson.person_id == Person.id,
            MoviePerson.credit_type == "cast",
        )
        .exists()
    )

    row = (
        await session.execute(
            select(Person.id, Person.name).where(
                Person.id == actor_id,
                has_cast_credit,
            )
        )
    ).one_or_none()

    if row is None:
        raise HTTPException(404, "Actor not found")

    person_id, name = row
    return {
        "id": str(person_id),
        "name": name,
    }


@router.get("/{movie_id}", response_model=MovieRead)
async def get_movie_detail(movie_id: UUID, session: SessionDep):
    movie = await get_movie(session, movie_id)
    if movie is None:
        raise HTTPException(404, "Movie not found")
    return movie_to_read(movie)


@router.post("", response_model=MovieRead, status_code=status.HTTP_201_CREATED)
async def create_movie(
    data: MovieCreate,
    session: SessionDep,
    current_user: CurrentUser,
    _csrf: CsrfProtected,
):
    try:
        movie = await movie_manual.create_movie(
            session,
            data=data,
            actor_user_id=current_user.id,
        )
        await session.commit()
        movie = await get_movie(session, movie.id, include_deleted=True)
        return movie_to_read(movie)
    except movie_manual.MovieReferenceError as exc:
        await session.rollback()
        raise HTTPException(422, str(exc)) from exc
    except IntegrityError as exc:
        await session.rollback()
        raise HTTPException(409, "Movie conflicts with an existing unique value") from exc


@router.patch("/{movie_id}", response_model=MovieRead)
async def update_movie(
    movie_id: UUID,
    data: MovieUpdate,
    session: SessionDep,
    current_user: CurrentUser,
    _csrf: CsrfProtected,
):
    movie = await get_movie(session, movie_id)
    if movie is None:
        raise HTTPException(404, "Movie not found")
    try:
        movie = await movie_manual.update_movie(
            session,
            movie=movie,
            data=data,
            actor_user_id=current_user.id,
        )
        await session.commit()
        movie = await get_movie(session, movie_id, include_deleted=True)
        return movie_to_read(movie)
    except movie_manual.MovieReferenceError as exc:
        await session.rollback()
        raise HTTPException(422, str(exc)) from exc
    except IntegrityError as exc:
        await session.rollback()
        raise HTTPException(409, "Movie conflicts with an existing unique value") from exc


@router.delete("/{movie_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_movie(
    movie_id: UUID,
    session: SessionDep,
    current_user: CurrentUser,
    _csrf: CsrfProtected,
):
    movie = await get_movie(session, movie_id)
    if movie is None:
        raise HTTPException(404, "Movie not found")
    await soft_delete_movie(session, movie=movie, actor_user_id=current_user.id)
    await session.commit()


@router.post("/{movie_id}/restore", response_model=MovieRead)
async def restore_movie_route(
    movie_id: UUID,
    session: SessionDep,
    admin: AdminUser,
    _csrf: CsrfProtected,
):
    movie = await get_movie(session, movie_id, include_deleted=True)
    if movie is None:
        raise HTTPException(404, "Movie not found")
    if movie.deleted_at is None:
        raise HTTPException(409, "Movie is not deleted")
    movie = await restore_movie(session, movie=movie, actor_user_id=admin.id)
    await session.commit()
    movie = await get_movie(session, movie_id, include_deleted=True)
    return movie_to_read(movie)


@router.delete("/{movie_id}/permanent", status_code=status.HTTP_204_NO_CONTENT)
async def permanent_delete_movie(
    movie_id: UUID,
    session: SessionDep,
    admin: AdminUser,
    _csrf: CsrfProtected,
):
    movie = await get_movie(session, movie_id, include_deleted=True)
    if movie is None:
        raise HTTPException(404, "Movie not found")
    if movie.deleted_at is None:
        raise HTTPException(409, "Movie must be soft-deleted first")
    await hard_delete_movie(session, movie=movie, actor_user_id=admin.id)
    await session.commit()
