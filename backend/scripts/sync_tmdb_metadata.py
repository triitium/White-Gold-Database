from __future__ import annotations

import argparse
import asyncio
import csv
import json
import os
import re
import unicodedata

from collections import Counter
from datetime import date
from pathlib import Path
from typing import Any

import httpx
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.db.session import async_session_factory
from app.models.classification import (
    Country,
    Genre,
    Language,
    MovieCountry,
    MovieGenre,
    MovieLanguage,
    MovieStudio,
    Studio,
)
from app.models.movie import Movie
from app.models.movie_person import MoviePerson
from app.models.person import Person
from app.services.audit import log_audit


TMDB_API = "https://api.themoviedb.org/3"
SUFFIXES = {"jr", "sr", "ii", "iii", "iv", "v"}

MUTATION_KEYS = {
    "genres_add",
    "genres_repoint",
    "genre_ids_linked",
    "countries_add",
    "countries_repoint",
    "country_codes_linked",
    "languages_add",
    "languages_remove",
    "languages_original_update",
    "studios_add",
    "studios_remove",
    "studio_ids_linked",
    "people_ids_linked",
    "people_created",
    "cast_add",
    "cast_repoint",
    "cast_update",
    "imdb_fill",
    "poster_update",
    "original_title_fill",
    "release_date_fill",
    "release_year_fill",
    "runtime_fill",
    "overview_fill",
}


def normalize(value: str | None) -> str:
    if not value:
        return ""

    value = unicodedata.normalize("NFKD", value)
    value = "".join(
        c for c in value
        if not unicodedata.combining(c)
    )
    value = value.casefold()

    return " ".join(re.findall(r"[a-z0-9]+", value))


def name_key(value: str | None) -> str:
    return (value or "").strip().casefold()


def strip_suffix(value: str | None) -> str:
    parts = normalize(value).split()

    if parts and parts[-1] in SUFFIXES:
        parts = parts[:-1]

    return " ".join(parts)


def names_compatible(a: str | None, b: str | None) -> bool:
    if normalize(a) == normalize(b):
        return True

    sa = strip_suffix(a)
    sb = strip_suffix(b)

    return bool(sa and sb and sa == sb)


def parse_date(value: str | None) -> date | None:
    if not value:
        return None

    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def add_multi(
    mapping: dict[str, list[Any]],
    key: str,
    value: Any,
) -> None:
    if key:
        mapping.setdefault(key, []).append(value)


class Caches:
    pass


async def load_caches(session) -> Caches:
    cache = Caches()

    genres = list(
        (await session.scalars(select(Genre))).all()
    )
    countries = list(
        (await session.scalars(select(Country))).all()
    )
    languages = list(
        (await session.scalars(select(Language))).all()
    )
    studios = list(
        (await session.scalars(select(Studio))).all()
    )
    people = list(
        (await session.scalars(select(Person))).all()
    )

    cache.genres_tmdb = {
        x.tmdb_id: x
        for x in genres
        if x.tmdb_id is not None
    }
    cache.genres_name = {}
    for x in genres:
        add_multi(
            cache.genres_name,
            name_key(x.name),
            x,
        )

    cache.countries_iso2 = {
        x.iso2.upper(): x
        for x in countries
        if x.iso2
    }
    cache.countries_name = {}
    for x in countries:
        add_multi(
            cache.countries_name,
            name_key(x.name),
            x,
        )

    cache.languages_iso = {
        x.iso_code.lower(): x
        for x in languages
    }
    cache.languages_name = {}
    for x in languages:
        add_multi(
            cache.languages_name,
            name_key(x.name),
            x,
        )

    cache.studios_tmdb = {
        x.tmdb_id: x
        for x in studios
        if x.tmdb_id is not None
    }
    cache.studios_name = {}
    for x in studios:
        add_multi(
            cache.studios_name,
            name_key(x.name),
            x,
        )

    cache.people_tmdb = {
        x.tmdb_id: x
        for x in people
        if x.tmdb_id is not None
    }
    cache.people_exact = {}
    cache.people_normalized = {}

    for x in people:
        add_multi(
            cache.people_exact,
            name_key(x.name),
            x,
        )
        add_multi(
            cache.people_normalized,
            normalize(x.name),
            x,
        )

    imdb_rows = (
        await session.execute(
            select(Movie.id, Movie.imdb_id)
            .where(Movie.imdb_id.is_not(None))
        )
    ).all()

    cache.imdb_owner = {
        imdb_id: movie_id
        for movie_id, imdb_id in imdb_rows
    }

    return cache


def resolve_genre(
    session,
    cache: Caches,
    incoming: dict[str, Any],
    stats: Counter,
) -> Genre:
    tmdb_id = int(incoming["id"])
    name = incoming["name"]

    existing = cache.genres_tmdb.get(tmdb_id)

    if existing is not None:
        return existing

    candidates = cache.genres_name.get(
        name_key(name),
        [],
    )

    unlinked = [
        x for x in candidates
        if x.tmdb_id is None
    ]

    if len(unlinked) == 1:
        genre = unlinked[0]
        genre.tmdb_id = tmdb_id
        cache.genres_tmdb[tmdb_id] = genre
        stats["genre_ids_linked"] += 1
        return genre

    if len(unlinked) > 1:
        raise RuntimeError(
            f"Ambiguous Genre name: {name!r}"
        )

    if candidates:
        raise RuntimeError(
            f"Genre {name!r} already belongs to "
            "another TMDB ID"
        )

    genre = Genre(
        name=name,
        tmdb_id=tmdb_id,
    )
    session.add(genre)

    cache.genres_tmdb[tmdb_id] = genre
    add_multi(
        cache.genres_name,
        name_key(name),
        genre,
    )

    return genre


def resolve_country(
    session,
    cache: Caches,
    incoming: dict[str, Any],
    stats: Counter,
) -> Country:
    iso2 = incoming.get("iso_3166_1")
    name = incoming["name"]

    if iso2:
        existing = cache.countries_iso2.get(
            iso2.upper()
        )

        if existing is not None:
            return existing

    candidates = cache.countries_name.get(
        name_key(name),
        [],
    )

    unlinked = [
        x for x in candidates
        if x.iso2 is None
    ]

    if len(unlinked) == 1 and iso2:
        country = unlinked[0]
        country.iso2 = iso2.upper()

        cache.countries_iso2[
            iso2.upper()
        ] = country

        stats["country_codes_linked"] += 1
        return country

    if len(unlinked) > 1:
        raise RuntimeError(
            f"Ambiguous Country name: {name!r}"
        )

    if candidates:
        raise RuntimeError(
            f"Country {name!r} already has "
            "another ISO2 code"
        )

    country = Country(
        name=name,
        iso2=iso2.upper() if iso2 else None,
        iso3=None,
    )
    session.add(country)

    if iso2:
        cache.countries_iso2[
            iso2.upper()
        ] = country

    add_multi(
        cache.countries_name,
        name_key(name),
        country,
    )

    return country


def resolve_language(
    session,
    cache: Caches,
    incoming: dict[str, Any],
) -> Language:
    iso_code = incoming["iso_639_1"].lower()
    name = (
        incoming.get("english_name")
        or incoming.get("name")
        or iso_code
    )

    existing = cache.languages_iso.get(
        iso_code
    )

    if existing is not None:
        return existing

    candidates = cache.languages_name.get(
        name_key(name),
        [],
    )

    if candidates:
        raise RuntimeError(
            f"Language {name!r} exists with "
            "another ISO code"
        )

    language = Language(
        iso_code=iso_code,
        name=name,
    )
    session.add(language)

    cache.languages_iso[iso_code] = language
    add_multi(
        cache.languages_name,
        name_key(name),
        language,
    )

    return language


def resolve_studio(
    session,
    cache: Caches,
    incoming: dict[str, Any],
    stats: Counter,
) -> Studio:
    tmdb_id = int(incoming["id"])
    name = incoming["name"]

    existing = cache.studios_tmdb.get(
        tmdb_id
    )

    if existing is not None:
        return existing

    candidates = [
        x
        for x in cache.studios_name.get(
            name_key(name),
            [],
        )
        if x.tmdb_id is None
    ]

    if len(candidates) == 1:
        studio = candidates[0]
        studio.tmdb_id = tmdb_id

        cache.studios_tmdb[
            tmdb_id
        ] = studio

        stats["studio_ids_linked"] += 1
        return studio

    studio = Studio(
        name=name,
        tmdb_id=tmdb_id,
    )
    session.add(studio)

    cache.studios_tmdb[tmdb_id] = studio

    add_multi(
        cache.studios_name,
        name_key(name),
        studio,
    )

    return studio


def resolve_person(
    session,
    cache: Caches,
    incoming: dict[str, Any],
    stats: Counter,
) -> Person:
    tmdb_id = int(incoming["id"])
    name = incoming["name"]

    existing = cache.people_tmdb.get(
        tmdb_id
    )

    if existing is not None:
        return existing

    exact_candidates = [
        x
        for x in cache.people_exact.get(
            name_key(name),
            [],
        )
        if x.tmdb_id is None
    ]

    if len(exact_candidates) == 1:
        person = exact_candidates[0]
        person.tmdb_id = tmdb_id

        cache.people_tmdb[
            tmdb_id
        ] = person

        stats["people_ids_linked"] += 1
        return person

    normalized_candidates = [
        x
        for x in cache.people_normalized.get(
            normalize(name),
            [],
        )
        if x.tmdb_id is None
    ]

    if len(normalized_candidates) == 1:
        person = normalized_candidates[0]
        person.tmdb_id = tmdb_id

        cache.people_tmdb[
            tmdb_id
        ] = person

        stats["people_ids_linked"] += 1
        return person

    person = Person(
        name=name,
        tmdb_id=tmdb_id,
    )
    session.add(person)

    cache.people_tmdb[tmdb_id] = person

    add_multi(
        cache.people_exact,
        name_key(name),
        person,
    )
    add_multi(
        cache.people_normalized,
        normalize(name),
        person,
    )

    stats["people_created"] += 1

    return person


def scalar_state(movie: Movie) -> dict[str, Any]:
    return {
        "imdb_id": movie.imdb_id,
        "poster_path": movie.poster_path,
        "original_title": movie.original_title,
        "release_date": (
            movie.release_date.isoformat()
            if movie.release_date
            else None
        ),
        "release_year": movie.release_year,
        "runtime_minutes": movie.runtime_minutes,
        "overview": movie.overview,
    }


async def sync_movie(
    session,
    cache: Caches,
    movie: Movie,
    remote: dict[str, Any],
) -> tuple[Counter, dict[str, Any], dict[str, Any]]:
    stats = Counter()

    before_scalars = scalar_state(movie)

    remote_imdb = (
        remote.get("external_ids", {})
        .get("imdb_id")
        or remote.get("imdb_id")
        or None
    )

    if remote_imdb:
        if movie.imdb_id is None:
            owner = cache.imdb_owner.get(
                remote_imdb
            )

            if (
                owner is not None
                and owner != movie.id
            ):
                stats["imdb_conflict"] += 1
            else:
                movie.imdb_id = remote_imdb
                cache.imdb_owner[
                    remote_imdb
                ] = movie.id
                stats["imdb_fill"] += 1

        elif movie.imdb_id != remote_imdb:
            stats["imdb_conflict"] += 1

    remote_poster = (
        remote.get("poster_path") or None
    )

    if (
        remote_poster
        and not movie.poster_path
    ):
        movie.poster_path = remote_poster
        stats["poster_update"] += 1

    if (
        not movie.original_title
        and remote.get("original_title")
    ):
        movie.original_title = (
            remote["original_title"]
        )
        stats["original_title_fill"] += 1

    remote_release_date = parse_date(
        remote.get("release_date")
    )

    if (
        movie.release_date is None
        and remote_release_date is not None
    ):
        movie.release_date = remote_release_date
        stats["release_date_fill"] += 1

    if (
        movie.release_year is None
        and remote_release_date is not None
    ):
        movie.release_year = (
            remote_release_date.year
        )
        stats["release_year_fill"] += 1

    runtime = remote.get("runtime")

    if (
        movie.runtime_minutes is None
        and isinstance(runtime, int)
        and runtime > 0
    ):
        movie.runtime_minutes = runtime
        stats["runtime_fill"] += 1

    if (
        not movie.overview
        and remote.get("overview")
    ):
        movie.overview = remote["overview"]
        stats["overview_fill"] += 1

    genre_links = list(movie.genres)

    for incoming in remote.get(
        "genres",
        [],
    ):
        genre = resolve_genre(
            session,
            cache,
            incoming,
            stats,
        )

        existing_link = next(
            (
                link
                for link in genre_links
                if link.genre is genre
            ),
            None,
        )

        if existing_link is not None:
            continue

        legacy_link = next(
            (
                link
                for link in genre_links
                if link.genre.tmdb_id is None
                and name_key(link.genre.name)
                == name_key(incoming["name"])
            ),
            None,
        )

        if legacy_link is not None:
            legacy_link.genre = genre
            stats["genres_repoint"] += 1
            continue

        new_link = MovieGenre(
            movie=movie,
            genre=genre,
        )
        session.add(new_link)
        genre_links.append(new_link)

        stats["genres_add"] += 1

    country_links = list(movie.countries)

    for incoming in remote.get(
        "production_countries",
        [],
    ):
        country = resolve_country(
            session,
            cache,
            incoming,
            stats,
        )

        existing_link = next(
            (
                link
                for link in country_links
                if link.country is country
            ),
            None,
        )

        if existing_link is not None:
            continue

        legacy_link = next(
            (
                link
                for link in country_links
                if link.country.iso2 is None
                and name_key(link.country.name)
                == name_key(incoming["name"])
            ),
            None,
        )

        if legacy_link is not None:
            legacy_link.country = country
            stats["countries_repoint"] += 1
            continue

        new_link = MovieCountry(
            movie=movie,
            country=country,
        )
        session.add(new_link)
        country_links.append(new_link)

        stats["countries_add"] += 1

    remote_languages = [
        x
        for x in remote.get(
            "spoken_languages",
            [],
        )
        if x.get("iso_639_1")
    ]

    if remote_languages:
        original_language = (
            remote.get("original_language")
        )

        desired_languages = {}

        for incoming in remote_languages:
            language = resolve_language(
                session,
                cache,
                incoming,
            )

            desired_languages[
                id(language)
            ] = (
                language,
                incoming["iso_639_1"]
                == original_language,
            )

        language_links = list(
            movie.languages
        )
        matched_links: set[int] = set()

        for language, is_original in (
            desired_languages.values()
        ):
            link = next(
                (
                    x
                    for x in language_links
                    if x.language is language
                ),
                None,
            )

            if link is None:
                link = MovieLanguage(
                    movie=movie,
                    language=language,
                    is_original=is_original,
                )
                session.add(link)
                stats["languages_add"] += 1
            else:
                matched_links.add(id(link))

                if (
                    bool(link.is_original)
                    != bool(is_original)
                ):
                    link.is_original = (
                        is_original
                    )
                    stats[
                        "languages_original_update"
                    ] += 1

        for link in language_links:
            if id(link) not in matched_links:
                await session.delete(link)
                stats["languages_remove"] += 1

    remote_studios = remote.get(
        "production_companies",
        [],
    )

    if remote_studios:
        desired_studios = {}

        for incoming in remote_studios:
            studio = resolve_studio(
                session,
                cache,
                incoming,
                stats,
            )

            desired_studios[id(studio)] = studio

        studio_links = list(movie.studios)
        matched_links: set[int] = set()

        for studio in desired_studios.values():
            link = next(
                (
                    x
                    for x in studio_links
                    if x.studio is studio
                ),
                None,
            )

            if link is None:
                link = MovieStudio(
                    movie=movie,
                    studio=studio,
                )
                session.add(link)
                stats["studios_add"] += 1
            else:
                matched_links.add(id(link))

        for link in studio_links:
            if id(link) not in matched_links:
                await session.delete(link)
                stats["studios_remove"] += 1

    current_cast = [
        credit
        for credit in movie.person_credits
        if credit.credit_type == "cast"
    ]

    remote_cast = list(
        remote.get("credits", {})
        .get("cast", [])
    )

    stats["cast_before"] = len(
        current_cast
    )
    stats["cast_tmdb_total"] = len(
        remote_cast
    )

    matched_credits: set[int] = set()

    for incoming in remote_cast:
        person = resolve_person(
            session,
            cache,
            incoming,
            stats,
        )

        tmdb_person_id = int(
            incoming["id"]
        )
        tmdb_credit_id = (
            incoming.get("credit_id")
            or None
        )
        billing_order = incoming.get(
            "order"
        )
        character_name = (
            incoming.get("character")
            or None
        )

        available = [
            credit
            for credit in current_cast
            if id(credit)
            not in matched_credits
        ]

        credit = None

        if tmdb_credit_id:
            credit = next(
                (
                    x
                    for x in available
                    if x.tmdb_credit_id
                    == tmdb_credit_id
                ),
                None,
            )

        if credit is None:
            credit = next(
                (
                    x
                    for x in available
                    if x.person.tmdb_id
                    == tmdb_person_id
                ),
                None,
            )

        if credit is None:
            credit = next(
                (
                    x
                    for x in available
                    if x.person is person
                ),
                None,
            )

        if credit is None:
            candidates = [
                x
                for x in available
                if x.billing_order
                == billing_order
                and names_compatible(
                    x.person.name,
                    incoming["name"],
                )
            ]

            if len(candidates) == 1:
                credit = candidates[0]

        if credit is None:
            new_credit = MoviePerson(
                movie=movie,
                person=person,
                credit_type="cast",
                job=None,
                character_name=character_name,
                billing_order=billing_order,
                tmdb_credit_id=tmdb_credit_id,
            )
            session.add(new_credit)

            stats["cast_add"] += 1
            continue

        matched_credits.add(id(credit))

        if credit.person is not person:
            credit.person = person
            stats["cast_repoint"] += 1

        metadata_changed = False

        if credit.job is not None:
            credit.job = None
            metadata_changed = True

        if (
            credit.character_name
            != character_name
        ):
            credit.character_name = (
                character_name
            )
            metadata_changed = True

        if (
            credit.billing_order
            != billing_order
        ):
            credit.billing_order = (
                billing_order
            )
            metadata_changed = True

        if (
            credit.tmdb_credit_id
            != tmdb_credit_id
        ):
            credit.tmdb_credit_id = (
                tmdb_credit_id
            )
            metadata_changed = True

        if metadata_changed:
            stats["cast_update"] += 1

    stats["legacy_cast_kept"] = sum(
        1
        for credit in current_cast
        if id(credit)
        not in matched_credits
    )

    stats["changes_total"] = sum(
        stats[key]
        for key in MUTATION_KEYS
    )

    after_scalars = scalar_state(movie)

    return (
        stats,
        before_scalars,
        after_scalars,
    )


async def tmdb_get(
    client: httpx.AsyncClient,
    tmdb_id: int,
    language: str,
) -> dict[str, Any]:
    for attempt in range(5):
        response = await client.get(
            f"/movie/{tmdb_id}",
            params={
                "language": language,
                "append_to_response": (
                    "credits,external_ids"
                ),
            },
        )

        if response.status_code == 429:
            await asyncio.sleep(
                float(
                    response.headers.get(
                        "Retry-After",
                        "2",
                    )
                )
            )
            continue

        if (
            response.status_code >= 500
            and attempt < 4
        ):
            await asyncio.sleep(
                2 ** attempt
            )
            continue

        response.raise_for_status()
        return response.json()

    raise RuntimeError(
        f"TMDB {tmdb_id}: retries exhausted"
    )


async def select_movies(args) -> list[dict[str, Any]]:
    async with async_session_factory() as session:
        stmt = (
            select(
                Movie.id,
                Movie.title,
                Movie.release_year,
                Movie.tmdb_id,
            )
            .where(
                Movie.deleted_at.is_(None),
                Movie.tmdb_id.is_not(None),
            )
            .order_by(
                Movie.title,
                Movie.release_year,
            )
        )

        if args.tmdb_id is not None:
            stmt = stmt.where(
                Movie.tmdb_id
                == args.tmdb_id
            )

        if args.limit is not None:
            stmt = stmt.limit(args.limit)

        rows = (
            await session.execute(stmt)
        ).all()

    return [
        {
            "id": row.id,
            "title": row.title,
            "release_year": (
                row.release_year
            ),
            "tmdb_id": row.tmdb_id,
        }
        for row in rows
    ]


async def fetch_remote(
    movies: list[dict[str, Any]],
    token: str,
    language: str,
    concurrency: int,
) -> dict[Any, dict[str, Any]]:
    semaphore = asyncio.Semaphore(
        concurrency
    )

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
    }

    async with httpx.AsyncClient(
        base_url=TMDB_API,
        headers=headers,
        timeout=30.0,
    ) as client:

        async def fetch_one(movie):
            async with semaphore:
                return (
                    movie["id"],
                    await tmdb_get(
                        client,
                        movie["tmdb_id"],
                        language,
                    ),
                )

        results = await asyncio.gather(
            *[
                fetch_one(movie)
                for movie in movies
            ]
        )

    return dict(results)


async def load_movies_for_sync(
    session,
    ids,
) -> dict[Any, Movie]:
    stmt = (
        select(Movie)
        .where(Movie.id.in_(ids))
        .options(
            selectinload(
                Movie.genres
            ).selectinload(
                MovieGenre.genre
            ),
            selectinload(
                Movie.countries
            ).selectinload(
                MovieCountry.country
            ),
            selectinload(
                Movie.languages
            ).selectinload(
                MovieLanguage.language
            ),
            selectinload(
                Movie.studios
            ).selectinload(
                MovieStudio.studio
            ),
            selectinload(
                Movie.person_credits
            ).selectinload(
                MoviePerson.person
            ),
        )
        .with_for_update()
    )

    movies = list(
        (
            await session.scalars(stmt)
        ).unique().all()
    )

    return {
        movie.id: movie
        for movie in movies
    }


async def apply_sync(
    args,
    selected,
    remote_by_movie,
):
    rows = []
    total = Counter()

    async with async_session_factory() as session:
        transaction = await session.begin()

        try:
            cache = await load_caches(
                session
            )

            movies = await load_movies_for_sync(
                session,
                [x["id"] for x in selected],
            )

            for selected_movie in selected:
                movie = movies[
                    selected_movie["id"]
                ]
                remote = remote_by_movie[
                    movie.id
                ]

                (
                    stats,
                    before_scalars,
                    after_scalars,
                ) = await sync_movie(
                    session,
                    cache,
                    movie,
                    remote,
                )

                await session.flush()

                if (
                    args.commit
                    and stats[
                        "changes_total"
                    ] > 0
                ):
                    await log_audit(
                        session,
                        actor_user_id=None,
                        action="TMDB_SYNC",
                        entity_type="movie",
                        entity_id=movie.id,
                        before_data={
                            "tmdb_id": (
                                movie.tmdb_id
                            ),
                            "scalars": (
                                before_scalars
                            ),
                        },
                        after_data={
                            "tmdb_id": (
                                movie.tmdb_id
                            ),
                            "scalars": (
                                after_scalars
                            ),
                            "changes": {
                                key: value
                                for key, value
                                in stats.items()
                                if value
                            },
                        },
                        reduce_to_diff=False,
                    )

                if stats[
                    "changes_total"
                ]:
                    total[
                        "changed_movies"
                    ] += 1
                    status = "changed"
                else:
                    total[
                        "unchanged_movies"
                    ] += 1
                    status = "unchanged"

                total["processed"] += 1

                for key, value in (
                    stats.items()
                ):
                    total[key] += value

                rows.append({
                    "status": status,
                    "movie_id": str(
                        movie.id
                    ),
                    "title": movie.title,
                    "release_year": (
                        movie.release_year
                    ),
                    "tmdb_id": (
                        movie.tmdb_id
                    ),
                    "tmdb_title": (
                        remote.get("title")
                    ),
                    "tmdb_imdb_id": (
                        remote.get(
                            "external_ids",
                            {},
                        ).get(
                            "imdb_id"
                        )
                    ),
                    "poster_before": (
                        before_scalars[
                            "poster_path"
                        ]
                    ),
                    "poster_after": (
                        after_scalars[
                            "poster_path"
                        ]
                    ),
                    "imdb_before": (
                        before_scalars[
                            "imdb_id"
                        ]
                    ),
                    "imdb_after": (
                        after_scalars[
                            "imdb_id"
                        ]
                    ),
                    **dict(stats),
                })

            if args.commit:
                await transaction.commit()
            else:
                await transaction.rollback()

        except Exception:
            if transaction.is_active:
                await transaction.rollback()
            raise

    return rows, total


def write_report(
    report_dir: Path,
    rows,
    total,
    *,
    commit: bool,
    language: str,
):
    report_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    csv_path = (
        report_dir / "movies.csv"
    )

    fieldnames = sorted({
        key
        for row in rows
        for key in row
    })

    with csv_path.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=fieldnames,
        )
        writer.writeheader()
        writer.writerows(rows)

    summary = {
        "mode": (
            "COMMIT"
            if commit
            else "DRY RUN"
        ),
        "tmdb_language": language,
        **dict(total),
    }

    (
        report_dir / "summary.json"
    ).write_text(
        json.dumps(
            summary,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    print(
        json.dumps(
            summary,
            indent=2,
            sort_keys=True,
        )
    )

    if not commit:
        print(
            "\nDRY RUN: transaction rolled back; "
            "no persistent database writes."
        )

    print(
        f"\nReport: {report_dir}"
    )


async def main_async(args):
    token = os.environ.get(
        "TMDB_READ_ACCESS_TOKEN"
    )

    if not token:
        raise SystemExit(
            "TMDB_READ_ACCESS_TOKEN "
            "is not configured"
        )

    language = os.environ.get(
        "TMDB_LANGUAGE",
        "de-DE",
    )

    selected = await select_movies(args)

    if not selected:
        raise SystemExit(
            "No matching movies found"
        )

    print(
        f"Fetching TMDB metadata for "
        f"{len(selected)} movie(s)..."
    )

    remote_by_movie = await fetch_remote(
        selected,
        token,
        language,
        args.concurrency,
    )

    rows, total = await apply_sync(
        args,
        selected,
        remote_by_movie,
    )

    write_report(
        args.report_dir,
        rows,
        total,
        commit=args.commit,
        language=language,
    )


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--tmdb-id",
        type=int,
    )

    parser.add_argument(
        "--limit",
        type=int,
    )

    parser.add_argument(
        "--concurrency",
        type=int,
        default=6,
    )

    parser.add_argument(
        "--report-dir",
        type=Path,
        default=Path("/report"),
    )

    parser.add_argument(
        "--commit",
        action="store_true",
    )

    parser.add_argument(
        "--all",
        action="store_true",
        help=(
            "Explicitly authorize a full "
            "database commit."
        ),
    )

    args = parser.parse_args()

    if (
        args.limit is not None
        and args.limit < 1
    ):
        raise SystemExit(
            "--limit must be >= 1"
        )

    if args.concurrency < 1:
        raise SystemExit(
            "--concurrency must be >= 1"
        )

    if (
        args.commit
        and args.tmdb_id is None
        and not args.all
    ):
        raise SystemExit(
            "Refusing bulk commit. Use "
            "--commit --all explicitly."
        )

    if (
        args.tmdb_id is not None
        and args.all
    ):
        raise SystemExit(
            "Use either --tmdb-id or --all, "
            "not both."
        )

    asyncio.run(main_async(args))


if __name__ == "__main__":
    main()
