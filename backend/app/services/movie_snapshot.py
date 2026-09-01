from __future__ import annotations

from typing import Any

from app.models.movie import Movie


def _uuid(value) -> str | None:
    return str(value) if value is not None else None


def _date(value) -> str | None:
    return value.isoformat() if value is not None else None


def _external_rating_key(source: str, rating_type: str) -> str:
    return f"{source}:{rating_type}"


def movie_snapshot(movie: Movie) -> dict[str, Any]:
    """
    Return a JSON-serializable, human-oriented snapshot of a Movie.

    IMPORTANT:
    The caller must eager-load all relationships used below before calling
    this function when using AsyncSession.
    """

    genres = sorted(
        {
            item.genre.name
            for item in movie.genres
        }
    )

    countries = sorted(
        [
            {
                "id": _uuid(item.country.id),
                "name": item.country.name,
                "iso2": item.country.iso2,
                "iso3": item.country.iso3,
            }
            for item in movie.countries
        ],
        key=lambda x: (
            x["name"].lower(),
            x["id"] or "",
        ),
    )

    languages = sorted(
        [
            {
                "id": _uuid(item.language.id),
                "name": item.language.name,
                "iso_code": item.language.iso_code,
                "is_original": item.is_original,
            }
            for item in movie.languages
        ],
        key=lambda x: (
            not x["is_original"],
            x["name"].lower(),
            x["id"] or "",
        ),
    )

    studios = sorted(
        [
            {
                "id": _uuid(item.studio.id),
                "name": item.studio.name,
            }
            for item in movie.studios
        ],
        key=lambda x: (
            x["name"].lower(),
            x["id"] or "",
        ),
    )

    credits = sorted(
        [
            {
                "credit_id": _uuid(credit.id),
                "person_id": _uuid(credit.person.id),
                "name": credit.person.name,
                "credit_type": credit.credit_type,
                "job": credit.job,
                "character_name": credit.character_name,
                "billing_order": credit.billing_order,
                "tmdb_credit_id": credit.tmdb_credit_id,
            }
            for credit in movie.person_credits
        ],
        key=lambda x: (
            x["credit_type"],
            x["billing_order"] if x["billing_order"] is not None else 999999,
            x["job"] or "",
            x["name"].lower(),
            x["credit_id"] or "",
        ),
    )

    links = sorted(
        [
            {
                "id": _uuid(link.id),
                "source": link.source,
                "url": link.url,
                "label": link.label,
            }
            for link in movie.links
        ],
        key=lambda x: (
            x["source"],
            x["url"],
            x["id"] or "",
        ),
    )

    external_ratings = {
        _external_rating_key(
            rating.source,
            rating.rating_type,
        ): {
            "value": float(rating.value),
            "scale": float(rating.scale),
            "vote_count": rating.vote_count,
            "source_url": rating.source_url,
            "retrieved_at": _date(rating.retrieved_at),
        }
        for rating in movie.external_ratings
    }

    return {
        "id": _uuid(movie.id),
        "title": movie.title,
        "original_title": movie.original_title,

        "release_year": movie.release_year,
        "release_date": _date(movie.release_date),
        "runtime_minutes": movie.runtime_minutes,

        "overview": movie.overview,
        "editorial_note": movie.editorial_note,

        "poster_url": movie.poster_url,
        "poster_path": movie.poster_path,

        "tmdb_id": movie.tmdb_id,
        "imdb_id": movie.imdb_id,

        "created_by_id": _uuid(movie.created_by_id),
        "deleted_at": _date(movie.deleted_at),
        "deleted_by_id": _uuid(movie.deleted_by_id),

        "genres": genres,
        "countries": countries,
        "languages": languages,
        "studios": studios,
        "credits": credits,
        "links": links,
        "external_ratings": external_ratings,
    }
