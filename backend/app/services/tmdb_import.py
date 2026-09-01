from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, select
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


async def _unique_name_match(
    session: AsyncSession,
    model,
    name: str,
):
    """
    Resolve lookup-table entries whose name is supposed to be unique.

    Prefer an exact match. If that does not exist, accept exactly one
    case-insensitive match.
    """
    exact = await session.scalar(
        select(model).where(model.name == name)
    )
    if exact is not None:
        return exact

    rows = (
        await session.scalars(
            select(model)
            .where(func.lower(model.name) == name.lower())
            .limit(2)
        )
    ).all()

    if len(rows) == 1:
        return rows[0]

    if len(rows) > 1:
        raise ValueError(
            f'Ambiguous existing {model.__name__} entries for "{name}"'
        )

    return None


async def _single_name_match(
    session: AsyncSession,
    model,
    name: str,
):
    """
    Name fallback for entities where duplicate names are allowed.

    Only reuse an existing object if exactly one matching row exists.
    """
    rows = (
        await session.scalars(
            select(model)
            .where(func.lower(model.name) == name.lower())
            .limit(2)
        )
    ).all()

    return rows[0] if len(rows) == 1 else None


async def _resolve_genre(session: AsyncSession, incoming):
    genre = await session.scalar(
        select(Genre).where(Genre.tmdb_id == incoming.tmdb_id)
    )

    if genre is not None:
        return genre

    genre = await _unique_name_match(
        session,
        Genre,
        incoming.name,
    )

    if genre is not None:
        if genre.tmdb_id is None:
            genre.tmdb_id = incoming.tmdb_id
            await session.flush()
            return genre

        if genre.tmdb_id != incoming.tmdb_id:
            raise ValueError(
                f'Genre "{incoming.name}" is already linked to '
                f"TMDB {genre.tmdb_id}, not {incoming.tmdb_id}"
            )

        return genre

    genre = Genre(
        name=incoming.name,
        tmdb_id=incoming.tmdb_id,
    )
    session.add(genre)
    await session.flush()
    return genre


async def _resolve_country(session: AsyncSession, incoming):
    country = None

    if incoming.iso2:
        country = await session.scalar(
            select(Country).where(Country.iso2 == incoming.iso2)
        )

    if country is None:
        country = await _unique_name_match(
            session,
            Country,
            incoming.name,
        )

    if country is not None:
        if country.iso2 is None and incoming.iso2:
            country.iso2 = incoming.iso2
            await session.flush()

        return country

    country = Country(
        name=incoming.name,
        iso2=incoming.iso2,
        iso3=None,
    )
    session.add(country)
    await session.flush()
    return country


async def _resolve_language(session: AsyncSession, incoming):
    language = await session.scalar(
        select(Language).where(
            Language.iso_code == incoming.iso_code
        )
    )

    if language is not None:
        return language

    language = await _unique_name_match(
        session,
        Language,
        incoming.name or incoming.iso_code,
    )

    if language is not None:
        return language

    language = Language(
        iso_code=incoming.iso_code,
        name=incoming.name or incoming.iso_code,
    )
    session.add(language)
    await session.flush()
    return language


async def _resolve_studio(session: AsyncSession, incoming):
    studio = await session.scalar(
        select(Studio).where(
            Studio.tmdb_id == incoming.tmdb_id
        )
    )

    if studio is not None:
        return studio

    studio = await _single_name_match(
        session,
        Studio,
        incoming.name,
    )

    if studio is not None and studio.tmdb_id is None:
        studio.tmdb_id = incoming.tmdb_id
        await session.flush()
        return studio

    # Studio names are not unique. If the name match is ambiguous or
    # belongs to another TMDB ID, create the TMDB entity separately.
    studio = Studio(
        name=incoming.name,
        tmdb_id=incoming.tmdb_id,
    )
    session.add(studio)
    await session.flush()
    return studio


async def _resolve_person(session: AsyncSession, incoming):
    person = await session.scalar(
        select(Person).where(
            Person.tmdb_id == incoming.tmdb_person_id
        )
    )

    if person is not None:
        return person

    person = await _single_name_match(
        session,
        Person,
        incoming.name,
    )

    if person is not None and person.tmdb_id is None:
        person.tmdb_id = incoming.tmdb_person_id
        await session.flush()
        return person

    # Names are not reliable identifiers for people. Only reuse a
    # name-only legacy entry when it is unique and has no TMDB ID.
    person = Person(
        name=incoming.name,
        tmdb_id=incoming.tmdb_person_id,
    )
    session.add(person)
    await session.flush()
    return person


async def import_movie_from_tmdb(
    session: AsyncSession,
    *,
    tmdb_id: int,
    created_by_id: UUID,
) -> Movie:
    existing = await get_existing_movie_by_tmdb_id(
        session,
        tmdb_id,
    )

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
        genre = await _resolve_genre(session, incoming)

        session.add(
            MovieGenre(
                movie_id=movie.id,
                genre_id=genre.id,
            )
        )

    for incoming in preview.countries:
        country = await _resolve_country(session, incoming)

        session.add(
            MovieCountry(
                movie_id=movie.id,
                country_id=country.id,
            )
        )

    for incoming in preview.languages:
        language = await _resolve_language(session, incoming)

        session.add(
            MovieLanguage(
                movie_id=movie.id,
                language_id=language.id,
                is_original=incoming.is_original,
            )
        )

    for incoming in preview.studios:
        studio = await _resolve_studio(session, incoming)

        session.add(
            MovieStudio(
                movie_id=movie.id,
                studio_id=studio.id,
            )
        )

    for incoming in preview.credits:
        person = await _resolve_person(session, incoming)

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
