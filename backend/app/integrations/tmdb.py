from __future__ import annotations

from datetime import date
from typing import Any

import httpx

from app.core.config import settings
from app.schemas.tmdb import (
    TmdbCountryPreview,
    TmdbCreditPreview,
    TmdbGenrePreview,
    TmdbLanguagePreview,
    TmdbMoviePreview,
    TmdbMovieSearchItem,
    TmdbMovieSearchResponse,
    TmdbStudioPreview,
)


TMDB_BASE_URL = "https://api.themoviedb.org/3"
TMDB_IMAGE_BASE = "https://image.tmdb.org/t/p/w500"


class TmdbError(RuntimeError):
    pass


def _date(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def _poster_url(path: str | None) -> str | None:
    return f"{TMDB_IMAGE_BASE}{path}" if path else None


class TmdbClient:
    def _headers(self) -> dict[str, str]:
        if not settings.tmdb_read_access_token:
            raise TmdbError("TMDB_READ_ACCESS_TOKEN is not configured")
        return {
            "Authorization": f"Bearer {settings.tmdb_read_access_token}",
            "Accept": "application/json",
        }

    async def _get(self, path: str, *, params: dict[str, Any] | None = None) -> dict[str, Any]:
        async with httpx.AsyncClient(
            base_url=TMDB_BASE_URL,
            headers=self._headers(),
            timeout=15.0,
        ) as client:
            response = await client.get(path, params=params)

        if response.status_code == 404:
            raise TmdbError("TMDB item not found")
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise TmdbError(f"TMDB request failed with HTTP {response.status_code}") from exc
        return response.json()

    async def search_movies(self, query: str, *, page: int = 1, year: int | None = None) -> TmdbMovieSearchResponse:
        params: dict[str, Any] = {
            "query": query,
            "page": page,
            "include_adult": "false",
            "language": settings.tmdb_language,
        }
        if year is not None:
            params["year"] = year
        data = await self._get("/search/movie", params=params)
        results = []
        for item in data.get("results", []):
            release_date = _date(item.get("release_date"))
            results.append(TmdbMovieSearchItem(
                tmdb_id=item["id"],
                title=item["title"],
                original_title=item.get("original_title"),
                release_date=release_date,
                release_year=release_date.year if release_date else None,
                overview=item.get("overview") or None,
                poster_url=_poster_url(item.get("poster_path")),
            ))
        return TmdbMovieSearchResponse(
            page=int(data.get("page", page)),
            total_pages=int(data.get("total_pages", 0)),
            total_results=int(data.get("total_results", 0)),
            results=results,
        )

    async def movie_preview(self, tmdb_id: int) -> TmdbMoviePreview:
        data = await self._get(
            f"/movie/{tmdb_id}",
            params={"language": settings.tmdb_language, "append_to_response": "credits,external_ids"},
        )
        release_date = _date(data.get("release_date"))
        original_language = data.get("original_language")
        credits = []
        for member in data.get("credits", {}).get("cast", []):
            credits.append(TmdbCreditPreview(
                tmdb_person_id=member["id"], name=member["name"], credit_type="cast",
                character_name=member.get("character") or None,
                billing_order=member.get("order"), tmdb_credit_id=member.get("credit_id"),
            ))
        for member in data.get("credits", {}).get("crew", []):
            credits.append(TmdbCreditPreview(
                tmdb_person_id=member["id"], name=member["name"], credit_type="crew",
                job=member.get("job") or None, tmdb_credit_id=member.get("credit_id"),
            ))
        return TmdbMoviePreview(
            tmdb_id=data["id"],
            imdb_id=data.get("external_ids", {}).get("imdb_id") or data.get("imdb_id") or None,
            title=data["title"],
            original_title=data.get("original_title") or None,
            release_date=release_date,
            release_year=release_date.year if release_date else None,
            runtime_minutes=data.get("runtime"),
            overview=data.get("overview") or None,
            poster_url=_poster_url(data.get("poster_path")),
            genres=[TmdbGenrePreview(tmdb_id=g["id"], name=g["name"]) for g in data.get("genres", [])],
            countries=[TmdbCountryPreview(iso2=c.get("iso_3166_1"), name=c["name"]) for c in data.get("production_countries", [])],
            languages=[
                TmdbLanguagePreview(
                    iso_code=l["iso_639_1"],
                    name=l.get("english_name") or l.get("name"),
                    is_original=l["iso_639_1"] == original_language,
                )
                for l in data.get("spoken_languages", []) if l.get("iso_639_1")
            ],
            studios=[TmdbStudioPreview(tmdb_id=s["id"], name=s["name"]) for s in data.get("production_companies", [])],
            credits=credits,
        )


tmdb_client = TmdbClient()
