from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.integrations.tmdb import tmdb_client
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
from app.services.audit import AUDIT_CREATE, log_audit
from app.services.movie_loader import reload_movie_full
from app.services.movie_snapshot import movie_snapshot


async def get_existing_movie_by_tmdb_id(
    session: AsyncSession,
    tmdb_id: int,
) -> Movie | None:
    return await session.scalar(
        select(Movie).where(Movie.tmdb_id == tmdb_id)
    )


async def import_movie_from_tmdb(
    session: AsyncSession,
    *,
    tmdb_id: int,
    created_by_id: UUID,
) -> Movie:
    existing = await get_existing_movie_by_tmdb_id(session, tmdb_id)

    if existing is not None:
        raise ValueError(
            "A movie with this TMDB ID already exists"
            if existing.deleted_at is None
            else "This TMDB movie already exists in the recycle bin"
        )

    preview = await tmdb_client.movie_preview(tmdb_id)

    movie = Movie(
        title=preview.title,
        original_title=preview.original_title,
        release_year=preview.release_year,
        release_date=preview.release_date,
        runtime_minutes=preview.runtime_minutes,
        overview=preview.overview,
        poster_url=preview.poster_url,
        tmdb_id=preview.tmdb_id,
        imdb_id=preview.imdb_id,
        created_by_id=created_by_id,
    )
    session.add(movie)
    await session.flush()

    for incoming in preview.genres:
        genre = await session.scalar(
            select(Genre).where(Genre.tmdb_id == incoming.tmdb_id)
        )
        if genre is None:
            genre = Genre(
                name=incoming.name,
                tmdb_id=incoming.tmdb_id,
            )
            session.add(genre)
            await session.flush()

        session.add(
            MovieGenre(
                movie_id=movie.id,
                genre_id=genre.id,
            )
        )

    for incoming in preview.countries:
        country = None

        if incoming.iso2:
            country = await session.scalar(
                select(Country).where(Country.iso2 == incoming.iso2)
            )

        if country is None:
            country = await session.scalar(
                select(Country).where(Country.name == incoming.name)
            )

        if country is None:
            country = Country(
                name=incoming.name,
                iso2=incoming.iso2,
                iso3=None,
            )
            session.add(country)
            await session.flush()

        session.add(
            MovieCountry(
                movie_id=movie.id,
                country_id=country.id,
            )
        )

    for incoming in preview.languages:
        language = await session.scalar(
            select(Language).where(
                Language.iso_code == incoming.iso_code
            )
        )

        if language is None:
            language = Language(
                iso_code=incoming.iso_code,
                name=incoming.name or incoming.iso_code,
            )
            session.add(language)
            await session.flush()

        session.add(
            MovieLanguage(
                movie_id=movie.id,
                language_id=language.id,
                is_original=incoming.is_original,
            )
        )

    for incoming in preview.studios:
        studio = await session.scalar(
            select(Studio).where(Studio.tmdb_id == incoming.tmdb_id)
        )

        if studio is None:
            studio = Studio(
                name=incoming.name,
                tmdb_id=incoming.tmdb_id,
            )
            session.add(studio)
            await session.flush()

        session.add(
            MovieStudio(
                movie_id=movie.id,
                studio_id=studio.id,
            )
        )

    for incoming in preview.credits:
        person = await session.scalar(
            select(Person).where(
                Person.tmdb_id == incoming.tmdb_person_id
            )
        )

        if person is None:
            person = Person(
                name=incoming.name,
                tmdb_id=incoming.tmdb_person_id,
            )
            session.add(person)
            await session.flush()

        session.add(
            MoviePerson(
                movie_id=movie.id,
                person_id=person.id,
                credit_type=incoming.credit_type,
                job=incoming.job,
                character_name=incoming.character_name,
                billing_order=incoming.billing_order,
                tmdb_credit_id=incoming.tmdb_credit_id,
            )
        )

    await session.flush()

    movie = await reload_movie_full(
        session,
        movie.id,
        include_deleted=True,
    )
    snapshot = movie_snapshot(movie)

    await log_audit(
        session,
        actor_user_id=created_by_id,
        action=AUDIT_CREATE,
        entity_type="movie",
        entity_id=movie.id,
        before_data=None,
        after_data=snapshot,
        reduce_to_diff=False,
    )

    return movie
