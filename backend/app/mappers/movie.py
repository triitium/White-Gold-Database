from __future__ import annotations

from app.models.movie import Movie
from app.schemas.movie_read import (
    CountryRead,
    ExternalRatingRead,
    GenreRead,
    LanguageRead,
    MovieLinkRead,
    MovieListItem,
    MovieRead,
    PersonCreditRead,
    StudioRead,
)


def calculate_community_rating(movie: Movie) -> tuple[float | None, int]:
    values = [state.rating for state in movie.user_states if state.rating is not None]
    if not values:
        return None, 0
    return sum(values) / len(values), len(values)


def get_external_rating(movie: Movie, source: str, rating_type: str) -> float | None:
    for rating in movie.external_ratings:
        if rating.source == source and rating.rating_type == rating_type:
            return float(rating.value)
    return None


def movie_to_list_item(movie: Movie) -> MovieListItem:
    community, count = calculate_community_rating(movie)
    return MovieListItem(
        id=movie.id,
        title=movie.title,
        original_title=movie.original_title,
        release_year=movie.release_year,
        runtime_minutes=movie.runtime_minutes,
        poster_url=movie.poster_url,
        poster_path=movie.poster_path,
        genres=sorted(item.genre.name for item in movie.genres),
        imdb_rating=get_external_rating(movie, "imdb", "audience"),
        rt_critics_rating=get_external_rating(movie, "rotten_tomatoes", "critics"),
        rt_audience_rating=get_external_rating(movie, "rotten_tomatoes", "audience"),
        metacritic_critics_rating=get_external_rating(movie, "metacritic", "critics"),
        metacritic_audience_rating=get_external_rating(movie, "metacritic", "audience"),
        community_rating=community,
        rating_count=count,
    )


def movie_to_read(movie: Movie) -> MovieRead:
    community, count = calculate_community_rating(movie)
    credits = sorted(
        movie.person_credits,
        key=lambda x: (
            x.credit_type,
            x.billing_order if x.billing_order is not None else 999999,
            x.job or "",
            x.person.name.casefold(),
        ),
    )

    return MovieRead(
        id=movie.id,
        title=movie.title,
        original_title=movie.original_title,
        release_year=movie.release_year,
        release_date=movie.release_date,
        runtime_minutes=movie.runtime_minutes,
        overview=movie.overview,
        editorial_note=movie.editorial_note,
        poster_url=movie.poster_url,
        poster_path=movie.poster_path,
        tmdb_id=movie.tmdb_id,
        imdb_id=movie.imdb_id,
        genres=[GenreRead(id=x.genre.id, name=x.genre.name) for x in movie.genres],
        countries=[
            CountryRead(id=x.country.id, name=x.country.name, iso2=x.country.iso2, iso3=x.country.iso3)
            for x in movie.countries
        ],
        languages=[
            LanguageRead(
                id=x.language.id,
                name=x.language.name,
                iso_code=x.language.iso_code,
                is_original=x.is_original,
            )
            for x in movie.languages
        ],
        studios=[StudioRead(id=x.studio.id, name=x.studio.name) for x in movie.studios],
        credits=[
            PersonCreditRead(
                credit_id=x.id,
                person_id=x.person.id,
                name=x.person.name,
                credit_type=x.credit_type,
                job=x.job,
                character_name=x.character_name,
                billing_order=x.billing_order,
            )
            for x in credits
        ],
        links=[MovieLinkRead(id=x.id, source=x.source, url=x.url, label=x.label) for x in movie.links],
        external_ratings=[
            ExternalRatingRead(
                source=x.source,
                rating_type=x.rating_type,
                value=float(x.value),
                scale=float(x.scale),
                vote_count=x.vote_count,
                source_url=x.source_url,
            )
            for x in movie.external_ratings
        ],
        community_rating=community,
        rating_count=count,
        created_at=movie.created_at,
        updated_at=movie.updated_at,
    )
