from __future__ import annotations

from app.models.movie_list import MovieList
from app.schemas.movie_list import (
    MovieListEntryRead,
    MovieListMovieRead,
    MovieListOwnerRead,
    MovieListRead,
    MovieListSummaryRead,
)


def _owner(movie_list: MovieList) -> MovieListOwnerRead | None:
    if movie_list.created_by is None:
        return None

    return MovieListOwnerRead(
        id=movie_list.created_by.id,
        username=movie_list.created_by.username,
    )


def movie_list_to_summary(movie_list: MovieList) -> MovieListSummaryRead:
    return MovieListSummaryRead(
        id=movie_list.id,
        title=movie_list.title,
        description=movie_list.description,
        created_by=_owner(movie_list),
        item_count=len(movie_list.items),
        created_at=movie_list.created_at,
        updated_at=movie_list.updated_at,
    )


def movie_list_to_read(movie_list: MovieList) -> MovieListRead:
    items = sorted(
        movie_list.items,
        key=lambda item: (item.position, str(item.movie_id)),
    )

    return MovieListRead(
        id=movie_list.id,
        title=movie_list.title,
        description=movie_list.description,
        created_by=_owner(movie_list),
        items=[
            MovieListEntryRead(
                movie=MovieListMovieRead(
                    id=item.movie.id,
                    title=item.movie.title,
                    original_title=item.movie.original_title,
                    release_year=item.movie.release_year,
                    poster_url=item.movie.poster_url,
                    poster_path=item.movie.poster_path,
                ),
                position=item.position,
                note=item.note,
            )
            for item in items
        ],
        created_at=movie_list.created_at,
        updated_at=movie_list.updated_at,
    )
