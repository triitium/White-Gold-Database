from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from app.api.deps import CsrfProtected, CurrentUser, SessionDep
from app.models.classification import Country, Genre, Language, Studio
from app.models.person import Person
from app.schemas.catalog import (
    CountryCreate,
    CountryOption,
    CountryUpdate,
    GenreCreate,
    GenreOption,
    GenreUpdate,
    LanguageCreate,
    LanguageOption,
    LanguageUpdate,
    PersonCreate,
    PersonOption,
    PersonUpdate,
    StudioCreate,
    StudioOption,
    StudioUpdate,
)
from app.services.catalog import create_reference, update_reference


router = APIRouter(prefix="/catalog", tags=["catalog"])


def _clean_code(value: str | None) -> str | None:
    return value.strip().upper() if value else None


async def _commit_or_conflict(session: SessionDep):
    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Reference data conflicts with an existing unique value",
        ) from exc


@router.get("/genres", response_model=list[GenreOption])
async def list_genres(
    session: SessionDep,
    current_user: CurrentUser,
    q: Annotated[str | None, Query(max_length=100)] = None,
):
    stmt = select(Genre)
    if q:
        stmt = stmt.where(Genre.name.ilike(f"%{q.strip()}%"))
    rows = (await session.scalars(stmt.order_by(func.lower(Genre.name)))).all()
    return [GenreOption(id=x.id, name=x.name, tmdb_id=x.tmdb_id) for x in rows]


@router.post("/genres", response_model=GenreOption, status_code=201)
async def create_genre(data: GenreCreate, session: SessionDep, current_user: CurrentUser, _csrf: CsrfProtected):
    try:
        obj = await create_reference(
            session,
            model=Genre,
            values={"name": data.name.strip(), "tmdb_id": data.tmdb_id},
            fields=("name", "tmdb_id"),
            entity_type="genre",
            actor_user_id=current_user.id,
        )
        await _commit_or_conflict(session)
        return GenreOption(id=obj.id, name=obj.name, tmdb_id=obj.tmdb_id)
    except IntegrityError as exc:
        await session.rollback()
        raise HTTPException(409, "Genre already exists") from exc


@router.patch("/genres/{entity_id}", response_model=GenreOption)
async def update_genre(entity_id: UUID, data: GenreUpdate, session: SessionDep, current_user: CurrentUser, _csrf: CsrfProtected):
    obj = await session.get(Genre, entity_id)
    if obj is None:
        raise HTTPException(404, "Genre not found")
    try:
        obj = await update_reference(
            session,
            obj=obj,
            changes=data.model_dump(exclude_unset=True),
            fields=("name", "tmdb_id"),
            entity_type="genre",
            actor_user_id=current_user.id,
        )
        await _commit_or_conflict(session)
        return GenreOption(id=obj.id, name=obj.name, tmdb_id=obj.tmdb_id)
    except IntegrityError as exc:
        await session.rollback()
        raise HTTPException(409, "Genre conflicts with existing data") from exc


@router.get("/countries", response_model=list[CountryOption])
async def list_countries(session: SessionDep, current_user: CurrentUser, q: Annotated[str | None, Query(max_length=100)] = None):
    stmt = select(Country)
    if q:
        stmt = stmt.where(Country.name.ilike(f"%{q.strip()}%"))
    rows = (await session.scalars(stmt.order_by(func.lower(Country.name)))).all()
    return [CountryOption(id=x.id, name=x.name, iso2=x.iso2, iso3=x.iso3) for x in rows]


@router.post("/countries", response_model=CountryOption, status_code=201)
async def create_country(data: CountryCreate, session: SessionDep, current_user: CurrentUser, _csrf: CsrfProtected):
    try:
        obj = await create_reference(
            session,
            model=Country,
            values={"name": data.name.strip(), "iso2": _clean_code(data.iso2), "iso3": _clean_code(data.iso3)},
            fields=("name", "iso2", "iso3"),
            entity_type="country",
            actor_user_id=current_user.id,
        )
        await _commit_or_conflict(session)
        return CountryOption(id=obj.id, name=obj.name, iso2=obj.iso2, iso3=obj.iso3)
    except IntegrityError as exc:
        await session.rollback()
        raise HTTPException(409, "Country conflicts with existing data") from exc


@router.patch("/countries/{entity_id}", response_model=CountryOption)
async def update_country(entity_id: UUID, data: CountryUpdate, session: SessionDep, current_user: CurrentUser, _csrf: CsrfProtected):
    obj = await session.get(Country, entity_id)
    if obj is None:
        raise HTTPException(404, "Country not found")
    changes = data.model_dump(exclude_unset=True)
    if "iso2" in changes:
        changes["iso2"] = _clean_code(changes["iso2"])
    if "iso3" in changes:
        changes["iso3"] = _clean_code(changes["iso3"])
    try:
        obj = await update_reference(
            session, obj=obj, changes=changes,
            fields=("name", "iso2", "iso3"), entity_type="country", actor_user_id=current_user.id,
        )
        await _commit_or_conflict(session)
        return CountryOption(id=obj.id, name=obj.name, iso2=obj.iso2, iso3=obj.iso3)
    except IntegrityError as exc:
        await session.rollback()
        raise HTTPException(409, "Country conflicts with existing data") from exc


@router.get("/languages", response_model=list[LanguageOption])
async def list_languages(session: SessionDep, current_user: CurrentUser, q: Annotated[str | None, Query(max_length=100)] = None):
    stmt = select(Language)
    if q:
        stmt = stmt.where(Language.name.ilike(f"%{q.strip()}%"))
    rows = (await session.scalars(stmt.order_by(func.lower(Language.name)))).all()
    return [LanguageOption(id=x.id, name=x.name, iso_code=x.iso_code) for x in rows]


@router.post("/languages", response_model=LanguageOption, status_code=201)
async def create_language(data: LanguageCreate, session: SessionDep, current_user: CurrentUser, _csrf: CsrfProtected):
    try:
        obj = await create_reference(
            session, model=Language,
            values={"name": data.name.strip(), "iso_code": data.iso_code.strip().lower()},
            fields=("name", "iso_code"), entity_type="language", actor_user_id=current_user.id,
        )
        await _commit_or_conflict(session)
        return LanguageOption(id=obj.id, name=obj.name, iso_code=obj.iso_code)
    except IntegrityError as exc:
        await session.rollback()
        raise HTTPException(409, "Language conflicts with existing data") from exc


@router.patch("/languages/{entity_id}", response_model=LanguageOption)
async def update_language(entity_id: UUID, data: LanguageUpdate, session: SessionDep, current_user: CurrentUser, _csrf: CsrfProtected):
    obj = await session.get(Language, entity_id)
    if obj is None:
        raise HTTPException(404, "Language not found")
    changes = data.model_dump(exclude_unset=True)
    if "iso_code" in changes and changes["iso_code"] is not None:
        changes["iso_code"] = changes["iso_code"].strip().lower()
    try:
        obj = await update_reference(
            session, obj=obj, changes=changes,
            fields=("name", "iso_code"), entity_type="language", actor_user_id=current_user.id,
        )
        await _commit_or_conflict(session)
        return LanguageOption(id=obj.id, name=obj.name, iso_code=obj.iso_code)
    except IntegrityError as exc:
        await session.rollback()
        raise HTTPException(409, "Language conflicts with existing data") from exc


@router.get("/studios", response_model=list[StudioOption])
async def list_studios(session: SessionDep, current_user: CurrentUser, q: Annotated[str | None, Query(max_length=100)] = None):
    stmt = select(Studio)
    if q:
        stmt = stmt.where(Studio.name.ilike(f"%{q.strip()}%"))
    rows = (await session.scalars(stmt.order_by(func.lower(Studio.name)).limit(200))).all()
    return [StudioOption(id=x.id, name=x.name, tmdb_id=x.tmdb_id) for x in rows]


@router.post("/studios", response_model=StudioOption, status_code=201)
async def create_studio(data: StudioCreate, session: SessionDep, current_user: CurrentUser, _csrf: CsrfProtected):
    try:
        obj = await create_reference(
            session, model=Studio, values={"name": data.name.strip(), "tmdb_id": data.tmdb_id},
            fields=("name", "tmdb_id"), entity_type="studio", actor_user_id=current_user.id,
        )
        await _commit_or_conflict(session)
        return StudioOption(id=obj.id, name=obj.name, tmdb_id=obj.tmdb_id)
    except IntegrityError as exc:
        await session.rollback()
        raise HTTPException(409, "Studio conflicts with existing data") from exc


@router.patch("/studios/{entity_id}", response_model=StudioOption)
async def update_studio(entity_id: UUID, data: StudioUpdate, session: SessionDep, current_user: CurrentUser, _csrf: CsrfProtected):
    obj = await session.get(Studio, entity_id)
    if obj is None:
        raise HTTPException(404, "Studio not found")
    try:
        obj = await update_reference(
            session, obj=obj, changes=data.model_dump(exclude_unset=True),
            fields=("name", "tmdb_id"), entity_type="studio", actor_user_id=current_user.id,
        )
        await _commit_or_conflict(session)
        return StudioOption(id=obj.id, name=obj.name, tmdb_id=obj.tmdb_id)
    except IntegrityError as exc:
        await session.rollback()
        raise HTTPException(409, "Studio conflicts with existing data") from exc


@router.get("/people", response_model=list[PersonOption])
async def list_people(
    session: SessionDep,
    current_user: CurrentUser,
    q: Annotated[str, Query(min_length=1, max_length=150)],
    limit: Annotated[int, Query(ge=1, le=100)] = 30,
):
    rows = (await session.scalars(
        select(Person).where(Person.name.ilike(f"%{q.strip()}%")).order_by(func.lower(Person.name)).limit(limit)
    )).all()
    return [PersonOption(
        id=x.id, name=x.name, birth_date=x.birth_date, death_date=x.death_date,
        biography=x.biography, profile_url=x.profile_url, profile_path=x.profile_path,
        tmdb_id=x.tmdb_id, imdb_id=x.imdb_id,
    ) for x in rows]


@router.post("/people", response_model=PersonOption, status_code=201)
async def create_person(data: PersonCreate, session: SessionDep, current_user: CurrentUser, _csrf: CsrfProtected):
    fields = ("name", "birth_date", "death_date", "biography", "profile_url", "profile_path", "tmdb_id", "imdb_id")
    try:
        values = data.model_dump()
        values["name"] = values["name"].strip()
        obj = await create_reference(
            session, model=Person, values=values, fields=fields,
            entity_type="person", actor_user_id=current_user.id,
        )
        await _commit_or_conflict(session)
        return PersonOption(**{field: getattr(obj, field) for field in ("id",) + fields})
    except IntegrityError as exc:
        await session.rollback()
        raise HTTPException(409, "Person conflicts with existing data") from exc


@router.patch("/people/{entity_id}", response_model=PersonOption)
async def update_person(entity_id: UUID, data: PersonUpdate, session: SessionDep, current_user: CurrentUser, _csrf: CsrfProtected):
    obj = await session.get(Person, entity_id)
    if obj is None:
        raise HTTPException(404, "Person not found")
    fields = ("name", "birth_date", "death_date", "biography", "profile_url", "profile_path", "tmdb_id", "imdb_id")
    try:
        obj = await update_reference(
            session, obj=obj, changes=data.model_dump(exclude_unset=True), fields=fields,
            entity_type="person", actor_user_id=current_user.id,
        )
        await _commit_or_conflict(session)
        return PersonOption(**{field: getattr(obj, field) for field in ("id",) + fields})
    except IntegrityError as exc:
        await session.rollback()
        raise HTTPException(409, "Person conflicts with existing data") from exc
