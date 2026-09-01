from __future__ import annotations

import argparse
import asyncio
import csv
import json
import os
import re
import unicodedata

from collections import Counter
from datetime import datetime, timezone
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any
from uuid import uuid7

import httpx

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine


TMDB_API = "https://api.themoviedb.org/3"
TMDB_IMAGE_BASE = "https://image.tmdb.org/t/p/w500"


def normalize(value: str | None) -> str:
    if not value:
        return ""

    value = unicodedata.normalize("NFKD", value)
    value = "".join(c for c in value if not unicodedata.combining(c))
    value = value.casefold()

    return " ".join(re.findall(r"[a-z0-9]+", value))


def movie_year(candidate: dict[str, Any]) -> int | None:
    release_date = candidate.get("release_date") or ""

    if len(release_date) >= 4 and release_date[:4].isdigit():
        return int(release_date[:4])

    return None


async def tmdb_get(
    client: httpx.AsyncClient,
    path: str,
    *,
    params: dict[str, Any] | None = None,
) -> dict[str, Any]:
    for attempt in range(5):
        response = await client.get(path, params=params)

        if response.status_code == 429:
            delay = float(response.headers.get("Retry-After", "2"))
            await asyncio.sleep(delay)
            continue

        if response.status_code >= 500 and attempt < 4:
            await asyncio.sleep(2 ** attempt)
            continue

        response.raise_for_status()
        return response.json()

    raise RuntimeError(f"TMDB request failed after retries: {path}")


async def search_movie(
    client: httpx.AsyncClient,
    query: str,
    language: str,
    release_year: int | None,
) -> list[dict[str, Any]]:
    params: dict[str, Any] = {
        "query": query,
        "language": language,
        "include_adult": "false",
    }

    # Do not use region=DE here. TMDB would then return regional
    # German release dates, including later re-releases.
    # For matching our database we want the primary release year.
    if release_year is not None:
        params["primary_release_year"] = release_year

    payload = await tmdb_get(
        client,
        f"{TMDB_API}/search/movie",
        params=params,
    )

    return payload.get("results", [])


def best_review_candidate(
    movie: dict[str, Any],
    candidates: list[dict[str, Any]],
) -> dict[str, Any] | None:
    local_names = [
        normalize(movie["title"]),
        normalize(movie["original_title"]),
    ]
    local_names = [x for x in local_names if x]

    ranked: list[tuple[float, dict[str, Any]]] = []

    for candidate in candidates:
        remote_names = [
            normalize(candidate.get("title")),
            normalize(candidate.get("original_title")),
        ]
        remote_names = [x for x in remote_names if x]

        if not remote_names:
            continue

        similarity = max(
            SequenceMatcher(None, a, b).ratio()
            for a in local_names
            for b in remote_names
        )

        candidate_year = movie_year(candidate)

        if (
            movie["release_year"] is not None
            and candidate_year is not None
            and movie["release_year"] == candidate_year
        ):
            similarity += 0.10

        ranked.append((similarity, candidate))

    if not ranked:
        return None

    ranked.sort(key=lambda item: item[0], reverse=True)
    return ranked[0][1]


async def match_movie(
    semaphore: asyncio.Semaphore,
    client: httpx.AsyncClient,
    movie: dict[str, Any],
    language: str,
) -> dict[str, Any]:
    async with semaphore:
        # Existing TMDB ID is authoritative.
        if movie["tmdb_id"] is not None:
            try:
                candidate = await tmdb_get(
                    client,
                    f"{TMDB_API}/movie/{movie['tmdb_id']}",
                    params={"language": language},
                )
            except Exception as exc:
                return {
                    **movie,
                    "status": "error",
                    "reason": f"existing_tmdb_id_lookup_failed: {exc}",
                }

            poster_path = candidate.get("poster_path")

            return {
                **movie,
                "status": "matched",
                "reason": "existing_tmdb_id",
                "matched_tmdb_id": candidate["id"],
                "matched_title": candidate.get("title"),
                "matched_original_title": candidate.get("original_title"),
                "matched_year": movie_year(candidate),
                "matched_poster_path": poster_path,
                "matched_poster_url": (
                    f"{TMDB_IMAGE_BASE}{poster_path}"
                    if poster_path
                    else None
                ),
            }

        queries: list[str] = []

        for value in (movie["title"], movie["original_title"]):
            if value and normalize(value) not in {
                normalize(existing) for existing in queries
            }:
                queries.append(value)

        candidates_by_id: dict[int, dict[str, Any]] = {}

        try:
            for query in queries:
                for candidate in await search_movie(
                    client,
                    query,
                    language,
                    movie["release_year"],
                ):
                    candidates_by_id[candidate["id"]] = candidate

        except Exception as exc:
            return {
                **movie,
                "status": "error",
                "reason": f"tmdb_search_failed: {exc}",
            }

        candidates = list(candidates_by_id.values())

        local_names = {
            normalize(movie["title"]),
            normalize(movie["original_title"]),
        }
        local_names.discard("")

        exact: list[dict[str, Any]] = []

        for candidate in candidates:
            remote_names = {
                normalize(candidate.get("title")),
                normalize(candidate.get("original_title")),
            }
            remote_names.discard("")

            same_name = bool(local_names & remote_names)
            same_year = (
                movie["release_year"] is not None
                and movie_year(candidate) == movie["release_year"]
            )

            if same_name and same_year:
                exact.append(candidate)

        if len(exact) == 1:
            candidate = exact[0]
            poster_path = candidate.get("poster_path")

            return {
                **movie,
                "status": "matched",
                "reason": "exact_title_and_year",
                "matched_tmdb_id": candidate["id"],
                "matched_title": candidate.get("title"),
                "matched_original_title": candidate.get("original_title"),
                "matched_year": movie_year(candidate),
                "matched_poster_path": poster_path,
                "matched_poster_url": (
                    f"{TMDB_IMAGE_BASE}{poster_path}"
                    if poster_path
                    else None
                ),
            }

        if len(exact) > 1:
            candidate = best_review_candidate(movie, exact)

            return {
                **movie,
                "status": "review",
                "reason": "multiple_exact_candidates",
                "matched_tmdb_id": candidate.get("id") if candidate else None,
                "matched_title": candidate.get("title") if candidate else None,
                "matched_original_title": (
                    candidate.get("original_title") if candidate else None
                ),
                "matched_year": movie_year(candidate) if candidate else None,
            }

        candidate = best_review_candidate(movie, candidates)

        if candidate is None:
            return {
                **movie,
                "status": "unmatched",
                "reason": "no_tmdb_candidate",
            }

        return {
            **movie,
            "status": "review",
            "reason": "no_exact_title_year_match",
            "matched_tmdb_id": candidate.get("id"),
            "matched_title": candidate.get("title"),
            "matched_original_title": candidate.get("original_title"),
            "matched_year": movie_year(candidate),
            "matched_poster_path": candidate.get("poster_path"),
        }


async def main_async(args: argparse.Namespace) -> int:
    database_url = os.environ["DATABASE_URL"]
    token = os.environ["TMDB_READ_ACCESS_TOKEN"]

    if not token:
        raise RuntimeError("TMDB_READ_ACCESS_TOKEN is empty")

    engine = create_async_engine(database_url)

    async with engine.connect() as connection:
        result = await connection.execute(
            text(
                """
                SELECT
                    id::text AS id,
                    title,
                    original_title,
                    release_year,
                    tmdb_id,
                    poster_path,
                    poster_url
                FROM movies
                WHERE deleted_at IS NULL
                ORDER BY release_year NULLS LAST, title
                """
            )
        )

        movies = [dict(row._mapping) for row in result]

    if args.limit is not None:
        movies = movies[: args.limit]

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
        "User-Agent": "WGDB-TMDB-Enrichment/1.0",
    }

    semaphore = asyncio.Semaphore(args.concurrency)

    async with httpx.AsyncClient(
        headers=headers,
        timeout=30.0,
    ) as client:
        results = await asyncio.gather(
            *[
                match_movie(
                    semaphore,
                    client,
                    movie,
                    args.language,
                )
                for movie in movies
            ]
        )

    # Prevent two local movies from receiving the same TMDB ID.
    tmdb_to_results: dict[int, list[dict[str, Any]]] = {}

    for result in results:
        if result["status"] != "matched":
            continue

        tmdb_id = result.get("matched_tmdb_id")

        if tmdb_id is not None:
            tmdb_to_results.setdefault(tmdb_id, []).append(result)

    for tmdb_id, rows in tmdb_to_results.items():
        if len(rows) > 1:
            for row in rows:
                row["status"] = "review"
                row["reason"] = f"tmdb_id_collision:{tmdb_id}"

    # Check TMDB IDs already assigned to another movie in the DB.
    async with engine.connect() as connection:
        result = await connection.execute(
            text(
                """
                SELECT id::text AS id, tmdb_id
                FROM movies
                WHERE tmdb_id IS NOT NULL
                """
            )
        )

        existing_tmdb = {
            row.tmdb_id: row.id
            for row in result
        }

    for row in results:
        if row["status"] != "matched":
            continue

        tmdb_id = row.get("matched_tmdb_id")
        owner = existing_tmdb.get(tmdb_id)

        if owner is not None and owner != row["id"]:
            row["status"] = "review"
            row["reason"] = f"tmdb_id_already_used_by:{owner}"

    counts = Counter(row["status"] for row in results)

    report_path = Path(args.report)
    report_path.parent.mkdir(parents=True, exist_ok=True)

    fields = [
        "status",
        "reason",
        "id",
        "title",
        "original_title",
        "release_year",
        "tmdb_id",
        "poster_path",
        "poster_url",
        "matched_tmdb_id",
        "matched_title",
        "matched_original_title",
        "matched_year",
        "matched_poster_path",
        "matched_poster_url",
    ]

    with report_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=fields,
            extrasaction="ignore",
        )
        writer.writeheader()
        writer.writerows(results)

    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "mode": "COMMIT" if args.commit else "DRY RUN",
        "movies_processed": len(results),
        "matched": counts["matched"],
        "review": counts["review"],
        "unmatched": counts["unmatched"],
        "error": counts["error"],
    }

    summary_path = report_path.with_suffix(".summary.json")
    summary_path.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(json.dumps(summary, indent=2))

    if not args.commit:
        print("\nDRY RUN: no database writes performed.")
        await engine.dispose()
        return 0

    updated = 0
    posters_added = 0

    async with engine.begin() as connection:
        for row in results:
            if row["status"] != "matched":
                continue

            new_path = row.get("matched_poster_path")
            new_url = row.get("matched_poster_url")

            set_poster = bool(new_path) and (
                args.overwrite_posters
                or not row.get("poster_path")
                or not row.get("poster_url")
            )

            tmdb_changed = (
                row.get("tmdb_id")
                != row["matched_tmdb_id"]
            )

            poster_changed = set_poster and (
                row.get("poster_path") != new_path
                or row.get("poster_url") != new_url
            )

            # Makes repeated --commit runs safe and prevents
            # duplicate no-op audit records.
            if not tmdb_changed and not poster_changed:
                continue

            before_data: dict[str, Any] = {}
            after_data: dict[str, Any] = {}

            if tmdb_changed:
                before_data["tmdb_id"] = row.get("tmdb_id")
                after_data["tmdb_id"] = row["matched_tmdb_id"]

            if poster_changed:
                before_data["poster_path"] = row.get("poster_path")
                before_data["poster_url"] = row.get("poster_url")
                after_data["poster_path"] = new_path
                after_data["poster_url"] = new_url

            await connection.execute(
                text(
                    """
                    UPDATE movies
                    SET
                        tmdb_id = :tmdb_id,
                        poster_path = CASE
                            WHEN :set_poster THEN :poster_path
                            ELSE poster_path
                        END,
                        poster_url = CASE
                            WHEN :set_poster THEN :poster_url
                            ELSE poster_url
                        END,
                        updated_at = now()
                    WHERE id = CAST(:movie_id AS uuid)
                    """
                ),
                {
                    "movie_id": row["id"],
                    "tmdb_id": row["matched_tmdb_id"],
                    "set_poster": set_poster,
                    "poster_path": new_path,
                    "poster_url": new_url,
                },
            )

            await connection.execute(
                text(
                    """
                    INSERT INTO audit_logs (
                        id,
                        actor_user_id,
                        action,
                        entity_type,
                        entity_id,
                        before_data,
                        after_data
                    )
                    VALUES (
                        CAST(:audit_id AS uuid),
                        NULL,
                        'TMDB_ENRICHMENT',
                        'movie',
                        CAST(:movie_id AS uuid),
                        CAST(:before_data AS jsonb),
                        CAST(:after_data AS jsonb)
                    )
                    """
                ),
                {
                    "audit_id": str(uuid7()),
                    "movie_id": row["id"],
                    "before_data": json.dumps(
                        before_data,
                        ensure_ascii=False,
                    ),
                    "after_data": json.dumps(
                        after_data,
                        ensure_ascii=False,
                    ),
                },
            )

            updated += 1

            if poster_changed:
                posters_added += 1

    print(f"\nCommitted TMDB matches: {updated}")
    print(f"Posters added/updated:  {posters_added}")

    await engine.dispose()
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Safely enrich WGDB movies with TMDB IDs and posters."
    )

    parser.add_argument("--commit", action="store_true")
    parser.add_argument("--overwrite-posters", action="store_true")
    parser.add_argument("--limit", type=int)
    parser.add_argument("--concurrency", type=int, default=8)
    parser.add_argument("--language", default="de-DE")
    parser.add_argument(
        "--report",
        default="/reports/tmdb_enrichment.csv",
    )

    return parser.parse_args()


def main() -> int:
    return asyncio.run(main_async(parse_args()))


if __name__ == "__main__":
    raise SystemExit(main())
