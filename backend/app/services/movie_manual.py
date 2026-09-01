from __future__ import annotations

from collections.abc import Iterable
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.classification import Country, Genre, Language, MovieCountry, MovieGenre, MovieLanguage, MovieStudio, Studio
from app.models.movie import Movie
from app.models.movie_link import MovieLink
from app.models.movie_person import MoviePerson
from app.models.person import Person
from app.schemas.movie import MovieCreate, MovieUpdate
from app.services.audit import AUDIT_CREATE, log_audit
from app.services.movie_loader import reload_movie_full
from app.services.movie_mutations import finish_movie_update, snapshot_before_change
from app.services.movie_snapshot import movie_snapshot


class MovieReferenceError(ValueError):
    pass


def _duplicates(values: Iterable[UUID]) -> set[UUID]:
    seen: set[UUID] = set()
    duplicates: set[UUID] = set()
    for value in values:
        if value in seen:
            duplicates.add(value)
        seen.add(value)
    return duplicates


async def _require_ids(session: AsyncSession, model, ids: list[UUID], *, label: str) -> None:
    if not ids:
        return
    duplicate_ids = _duplicates(ids)
    if duplicate_ids:
        raise MovieReferenceError(f"Duplicate {label} IDs: " + ", ".join(sorted(str(x) for x in duplicate_ids)))
    found = set((await session.scalars(select(model.id).where(model.id.in_(ids)))).all())
    missing = set(ids) - found
    if missing:
        raise MovieReferenceError(f"Unknown {label} IDs: " + ", ".join(sorted(str(x) for x in missing)))


async def _validate_create_references(session: AsyncSession, data: MovieCreate) -> None:
    await _require_ids(session, Genre, data.genre_ids, label="genre")
    await _require_ids(session, Country, data.country_ids, label="country")
    await _require_ids(session, Studio, data.studio_ids, label="studio")
    await _require_ids(session, Language, [x.language_id for x in data.languages], label="language")
    await _require_ids(session, Person, [x.person_id for x in data.person_credits], label="person")


async def _validate_update_references(session: AsyncSession, data: MovieUpdate) -> None:
    if data.genre_ids is not None:
        await _require_ids(session, Genre, data.genre_ids, label="genre")
    if data.country_ids is not None:
        await _require_ids(session, Country, data.country_ids, label="country")
    if data.studio_ids is not None:
        await _require_ids(session, Studio, data.studio_ids, label="studio")
    if data.languages is not None:
        await _require_ids(session, Language, [x.language_id for x in data.languages], label="language")
    if data.person_credits is not None:
        await _require_ids(session, Person, [x.person_id for x in data.person_credits], label="person")


async def _add_relations_from_create(session: AsyncSession, *, movie_id: UUID, data: MovieCreate) -> None:
    session.add_all([MovieGenre(movie_id=movie_id, genre_id=x) for x in data.genre_ids])
    session.add_all([MovieCountry(movie_id=movie_id, country_id=x) for x in data.country_ids])
    session.add_all([MovieLanguage(movie_id=movie_id, language_id=x.language_id, is_original=x.is_original) for x in data.languages])
    session.add_all([MovieStudio(movie_id=movie_id, studio_id=x) for x in data.studio_ids])
    session.add_all([MoviePerson(movie_id=movie_id, person_id=x.person_id, credit_type=x.credit_type, job=x.job, character_name=x.character_name, billing_order=x.billing_order, tmdb_credit_id=x.tmdb_credit_id) for x in data.person_credits])
    session.add_all([MovieLink(movie_id=movie_id, source=x.source.strip(), url=x.url.strip(), label=x.label.strip() if x.label else None) for x in data.links])


async def create_movie(session: AsyncSession, *, data: MovieCreate, actor_user_id: UUID) -> Movie:
    await _validate_create_references(session, data)
    movie = Movie(
        title=data.title.strip(),
        original_title=data.original_title.strip() if data.original_title else None,
        release_year=data.release_year,
        release_date=data.release_date,
        runtime_minutes=data.runtime_minutes,
        overview=data.overview,
        editorial_note=data.editorial_note,
        poster_url=data.poster_url,
        poster_path=data.poster_path,
        tmdb_id=data.tmdb_id,
        imdb_id=data.imdb_id,
        created_by_id=actor_user_id,
    )
    session.add(movie)
    await session.flush()
    await _add_relations_from_create(session, movie_id=movie.id, data=data)
    await session.flush()
    movie = await reload_movie_full(session, movie.id, include_deleted=True)
    snapshot = movie_snapshot(movie)
    await log_audit(session, actor_user_id=actor_user_id, action=AUDIT_CREATE, entity_type="movie", entity_id=movie.id, before_data=None, after_data=snapshot, reduce_to_diff=False)
    return movie


def _apply_scalar_updates(movie: Movie, data: MovieUpdate) -> None:
    changes = data.model_dump(exclude_unset=True, exclude={"genre_ids", "country_ids", "languages", "studio_ids", "person_credits", "links"})
    for field, value in changes.items():
        if field in {"title", "original_title"} and isinstance(value, str):
            value = value.strip()
        setattr(movie, field, value)


async def _replace(session: AsyncSession, model, movie_id: UUID, rows: list) -> None:
    await session.execute(delete(model).where(model.movie_id == movie_id))
    session.add_all(rows)


async def update_movie(session: AsyncSession, *, movie: Movie, data: MovieUpdate, actor_user_id: UUID) -> Movie:
    before_snapshot = await snapshot_before_change(session, movie)
    await _validate_update_references(session, data)
    _apply_scalar_updates(movie, data)

    if data.genre_ids is not None:
        await _replace(session, MovieGenre, movie.id, [MovieGenre(movie_id=movie.id, genre_id=x) for x in data.genre_ids])
    if data.country_ids is not None:
        await _replace(session, MovieCountry, movie.id, [MovieCountry(movie_id=movie.id, country_id=x) for x in data.country_ids])
    if data.languages is not None:
        await _replace(session, MovieLanguage, movie.id, [MovieLanguage(movie_id=movie.id, language_id=x.language_id, is_original=x.is_original) for x in data.languages])
    if data.studio_ids is not None:
        await _replace(session, MovieStudio, movie.id, [MovieStudio(movie_id=movie.id, studio_id=x) for x in data.studio_ids])
    if data.person_credits is not None:
        await _replace(session, MoviePerson, movie.id, [MoviePerson(movie_id=movie.id, person_id=x.person_id, credit_type=x.credit_type, job=x.job, character_name=x.character_name, billing_order=x.billing_order, tmdb_credit_id=x.tmdb_credit_id) for x in data.person_credits])
    if data.links is not None:
        await _replace(session, MovieLink, movie.id, [MovieLink(movie_id=movie.id, source=x.source.strip(), url=x.url.strip(), label=x.label.strip() if x.label else None) for x in data.links])

    return await finish_movie_update(session, movie_id=movie.id, actor_user_id=actor_user_id, before_snapshot=before_snapshot)
