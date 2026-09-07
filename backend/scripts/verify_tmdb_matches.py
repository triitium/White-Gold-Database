from __future__ import annotations

import argparse
import asyncio
import csv
import json
import os
import re
import unicodedata

from collections import Counter, defaultdict
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any

import httpx
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine


TMDB_API = "https://api.themoviedb.org/3"
SUFFIXES = {"jr", "sr", "ii", "iii", "iv", "v"}


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


def strip_suffix(value: str | None) -> str:
    parts = normalize(value).split()

    if parts and parts[-1] in SUFFIXES:
        parts = parts[:-1]

    return " ".join(parts)


def names_compatible(a: str | None, b: str | None) -> bool:
    na = normalize(a)
    nb = normalize(b)

    if na and na == nb:
        return True

    sa = strip_suffix(a)
    sb = strip_suffix(b)

    return bool(sa and sb and sa == sb)


def release_year(data: dict[str, Any]) -> int | None:
    value = data.get("release_date") or ""

    if len(value) >= 4 and value[:4].isdigit():
        return int(value[:4])

    return None


def title_similarity(
    movie: dict[str, Any],
    remote: dict[str, Any],
) -> float:
    local_names = [
        normalize(movie.get("title")),
        normalize(movie.get("original_title")),
    ]

    remote_names = [
        normalize(remote.get("title")),
        normalize(remote.get("original_title")),
    ]

    local_names = [x for x in local_names if x]
    remote_names = [x for x in remote_names if x]

    if not local_names or not remote_names:
        return 0.0

    best = 0.0

    for local in local_names:
        for candidate in remote_names:
            score = SequenceMatcher(
                None,
                local,
                candidate,
            ).ratio()

            local_tokens = local.split()
            candidate_tokens = candidate.split()

            shorter, longer = (
                (local_tokens, candidate_tokens)
                if len(local_tokens) <= len(candidate_tokens)
                else (candidate_tokens, local_tokens)
            )

            contained = (
                len(shorter) >= 2
                and any(
                    longer[i:i + len(shorter)] == shorter
                    for i in range(
                        len(longer) - len(shorter) + 1
                    )
                )
            )

            if contained:
                score = max(score, 0.92)

            best = max(best, score)

    return best


def cast_overlap(
    local_cast: list[str],
    remote: dict[str, Any],
) -> tuple[int, list[str]]:
    remote_names = [
        member.get("name") or ""
        for member in remote.get("credits", {}).get("cast", [])
    ]

    matched: list[str] = []

    for local_name in local_cast:
        if any(
            names_compatible(local_name, remote_name)
            for remote_name in remote_names
        ):
            matched.append(local_name)

    return len(matched), matched


def year_distance(
    local_year: int | None,
    remote_year: int | None,
) -> int | None:
    if local_year is None or remote_year is None:
        return None

    return abs(local_year - remote_year)


def candidate_score(
    movie: dict[str, Any],
    local_cast: list[str],
    remote: dict[str, Any],
) -> dict[str, Any]:
    similarity = title_similarity(movie, remote)

    remote_year = release_year(remote)
    distance = year_distance(
        movie.get("release_year"),
        remote_year,
    )

    overlap, matched_names = cast_overlap(
        local_cast,
        remote,
    )

    score = similarity * 55.0

    if distance is None:
        score += 8.0
    elif distance == 0:
        score += 20.0
    elif distance == 1:
        score += 14.0
    elif distance == 2:
        score += 6.0

    if local_cast:
        score += 25.0 * (overlap / len(local_cast))
    else:
        score += 15.0

    return {
        "tmdb_id": remote.get("id"),
        "title": remote.get("title"),
        "original_title": remote.get("original_title"),
        "release_year": remote_year,
        "title_similarity": round(similarity, 4),
        "year_distance": distance,
        "cast_overlap": overlap,
        "cast_total": len(local_cast),
        "matched_cast": matched_names,
        "score": round(score, 2),
    }


def strong_candidate(
    result: dict[str, Any],
) -> bool:
    title_good = result["title_similarity"] >= 0.90

    distance = result["year_distance"]
    year_good = distance is None or distance <= 1

    cast_total = result["cast_total"]

    if cast_total == 0:
        cast_good = True
    elif cast_total == 1:
        cast_good = result["cast_overlap"] >= 1
    else:
        cast_good = result["cast_overlap"] >= min(
            2,
            cast_total,
        )

    return title_good and year_good and cast_good


async def tmdb_get(
    client: httpx.AsyncClient,
    path: str,
    *,
    params: dict[str, Any] | None = None,
) -> dict[str, Any]:
    for attempt in range(5):
        response = await client.get(
            path,
            params=params,
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

        if response.status_code >= 500 and attempt < 4:
            await asyncio.sleep(2 ** attempt)
            continue

        response.raise_for_status()
        return response.json()

    raise RuntimeError(
        f"TMDB request failed after retries: {path}"
    )


async def movie_details(
    client: httpx.AsyncClient,
    tmdb_id: int,
    language: str,
) -> dict[str, Any]:
    return await tmdb_get(
        client,
        f"{TMDB_API}/movie/{tmdb_id}",
        params={
            "language": language,
            "append_to_response": "credits",
        },
    )


async def search_movies(
    client: httpx.AsyncClient,
    query: str,
    year: int | None,
    language: str,
) -> list[dict[str, Any]]:
    params: dict[str, Any] = {
        "query": query,
        "language": language,
        "include_adult": "false",
    }

    if year is not None:
        params["primary_release_year"] = year

    payload = await tmdb_get(
        client,
        f"{TMDB_API}/search/movie",
        params=params,
    )

    return payload.get("results", [])


def preliminary_score(
    movie: dict[str, Any],
    candidate: dict[str, Any],
) -> float:
    score = title_similarity(
        movie,
        candidate,
    )

    distance = year_distance(
        movie.get("release_year"),
        release_year(candidate),
    )

    if distance == 0:
        score += 0.25
    elif distance == 1:
        score += 0.10

    return score


async def find_alternatives(
    client: httpx.AsyncClient,
    movie: dict[str, Any],
    local_cast: list[str],
    language: str,
    current_tmdb_id: int,
) -> list[dict[str, Any]]:
    queries: list[str] = []

    for value in (
        movie.get("title"),
        movie.get("original_title"),
    ):
        if not value:
            continue

        if normalize(value) not in {
            normalize(x)
            for x in queries
        }:
            queries.append(value)

    candidates: dict[int, dict[str, Any]] = {}

    for query in queries:
        try:
            results = await search_movies(
                client,
                query,
                movie.get("release_year"),
                language,
            )
        except Exception:
            continue

        for candidate in results:
            candidate_id = candidate.get("id")

            if (
                candidate_id is None
                or candidate_id == current_tmdb_id
            ):
                continue

            candidates[candidate_id] = candidate

    ranked = sorted(
        candidates.values(),
        key=lambda candidate: preliminary_score(
            movie,
            candidate,
        ),
        reverse=True,
    )

    detailed: list[dict[str, Any]] = []

    for candidate in ranked[:5]:
        try:
            details = await movie_details(
                client,
                candidate["id"],
                language,
            )
        except Exception:
            continue

        detailed.append(
            candidate_score(
                movie,
                local_cast,
                details,
            )
        )

    detailed.sort(
        key=lambda x: x["score"],
        reverse=True,
    )

    return detailed


async def verify_one(
    semaphore: asyncio.Semaphore,
    client: httpx.AsyncClient,
    movie: dict[str, Any],
    local_cast: list[str],
    language: str,
) -> dict[str, Any]:
    async with semaphore:
        try:
            current_remote = await movie_details(
                client,
                movie["tmdb_id"],
                language,
            )
        except Exception as exc:
            return {
                **movie,
                "status": "ERROR",
                "reason": f"current_tmdb_lookup_failed: {exc}",
            }

        current = candidate_score(
            movie,
            local_cast,
            current_remote,
        )

        if strong_candidate(current):
            return {
                **movie,
                "status": "OK",
                "reason": "current_match_strong",
                "current": current,
                "alternative": None,
            }

        alternatives = await find_alternatives(
            client,
            movie,
            local_cast,
            language,
            movie["tmdb_id"],
        )

        alternative = (
            alternatives[0]
            if alternatives
            else None
        )

        status = "REVIEW"
        reason = "current_match_weak"

        if alternative is not None:
            better_by = (
                alternative["score"]
                - current["score"]
            )

            cast_improvement = (
                alternative["cast_overlap"]
                > current["cast_overlap"]
            )

            if (
                strong_candidate(alternative)
                and better_by >= 12.0
                and (
                    cast_improvement
                    or current["cast_total"] == 0
                )
            ):
                status = "SUSPECT"
                reason = "alternative_matches_significantly_better"

        return {
            **movie,
            "status": status,
            "reason": reason,
            "current": current,
            "alternative": alternative,
        }


async def load_database(engine):
    async with engine.connect() as conn:
        movies = [
            dict(row)
            for row in (
                await conn.execute(
                    text("""
                        SELECT
                            id,
                            title,
                            original_title,
                            release_year,
                            tmdb_id
                        FROM movies
                        WHERE deleted_at IS NULL
                          AND tmdb_id IS NOT NULL
                        ORDER BY title, release_year NULLS LAST
                    """)
                )
            ).mappings()
        ]

        cast_rows = [
            dict(row)
            for row in (
                await conn.execute(
                    text("""
                        SELECT
                            mp.movie_id,
                            p.name,
                            mp.billing_order
                        FROM movie_people mp
                        JOIN people p
                          ON p.id = mp.person_id
                        WHERE mp.credit_type = 'cast'
                        ORDER BY
                            mp.movie_id,
                            mp.billing_order NULLS LAST,
                            p.name
                    """)
                )
            ).mappings()
        ]

    cast_by_movie: dict[Any, list[str]] = defaultdict(list)

    for row in cast_rows:
        cast_by_movie[row["movie_id"]].append(
            row["name"]
        )

    return movies, cast_by_movie


def csv_row(result: dict[str, Any]) -> dict[str, Any]:
    current = result.get("current") or {}
    alternative = result.get("alternative") or {}

    return {
        "status": result["status"],
        "reason": result["reason"],
        "movie_id": result["id"],
        "title": result["title"],
        "original_title": result.get("original_title"),
        "release_year": result.get("release_year"),
        "current_tmdb_id": result["tmdb_id"],
        "current_tmdb_title": current.get("title"),
        "current_tmdb_original_title": current.get(
            "original_title"
        ),
        "current_tmdb_year": current.get(
            "release_year"
        ),
        "current_title_similarity": current.get(
            "title_similarity"
        ),
        "current_year_distance": current.get(
            "year_distance"
        ),
        "current_cast_overlap": current.get(
            "cast_overlap"
        ),
        "local_cast_total": current.get(
            "cast_total"
        ),
        "current_matched_cast": " | ".join(
            current.get("matched_cast") or []
        ),
        "current_score": current.get("score"),
        "suggested_tmdb_id": alternative.get(
            "tmdb_id"
        ),
        "suggested_title": alternative.get("title"),
        "suggested_original_title": alternative.get(
            "original_title"
        ),
        "suggested_year": alternative.get(
            "release_year"
        ),
        "suggested_title_similarity": alternative.get(
            "title_similarity"
        ),
        "suggested_year_distance": alternative.get(
            "year_distance"
        ),
        "suggested_cast_overlap": alternative.get(
            "cast_overlap"
        ),
        "suggested_matched_cast": " | ".join(
            alternative.get("matched_cast") or []
        ),
        "suggested_score": alternative.get("score"),
    }


async def main_async(args):
    database_url = os.environ.get("DATABASE_URL")
    token = os.environ.get("TMDB_READ_ACCESS_TOKEN")
    language = os.environ.get(
        "TMDB_LANGUAGE",
        "de-DE",
    )

    if not database_url:
        raise SystemExit(
            "DATABASE_URL is not configured"
        )

    if not token:
        raise SystemExit(
            "TMDB_READ_ACCESS_TOKEN is not configured"
        )

    engine = create_async_engine(database_url)

    try:
        movies, cast_by_movie = await load_database(
            engine
        )

        if args.tmdb_id is not None:
            movies = [
                movie
                for movie in movies
                if movie["tmdb_id"] == args.tmdb_id
            ]

        if args.limit is not None:
            movies = movies[:args.limit]

        if not movies:
            raise SystemExit(
                "No matching movies found"
            )

        semaphore = asyncio.Semaphore(
            args.concurrency
        )

        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
        }

        async with httpx.AsyncClient(
            headers=headers,
            timeout=30.0,
        ) as client:
            results = await asyncio.gather(
                *[
                    verify_one(
                        semaphore,
                        client,
                        movie,
                        cast_by_movie.get(
                            movie["id"],
                            [],
                        ),
                        language,
                    )
                    for movie in movies
                ]
            )

        stats = Counter(
            result["status"]
            for result in results
        )

        args.report_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        rows = [
            csv_row(result)
            for result in results
        ]

        with (
            args.report_dir
            / "tmdb_verification.csv"
        ).open(
            "w",
            newline="",
            encoding="utf-8",
        ) as handle:
            writer = csv.DictWriter(
                handle,
                fieldnames=list(rows[0].keys()),
            )
            writer.writeheader()
            writer.writerows(rows)

        summary = {
            "mode": "READ ONLY",
            "tmdb_language": language,
            "movies_checked": len(results),
            "ok": stats["OK"],
            "review": stats["REVIEW"],
            "suspect": stats["SUSPECT"],
            "error": stats["ERROR"],
        }

        (
            args.report_dir
            / "summary.json"
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

        print(
            f"\nReport: {args.report_dir}"
        )

    finally:
        await engine.dispose()


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Read-only verification of existing "
            "WGDB TMDB movie IDs."
        )
    )

    parser.add_argument(
        "--limit",
        type=int,
    )

    parser.add_argument(
        "--tmdb-id",
        type=int,
    )

    parser.add_argument(
        "--concurrency",
        type=int,
        default=4,
    )

    parser.add_argument(
        "--report-dir",
        type=Path,
        default=Path("/report"),
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

    asyncio.run(main_async(args))


if __name__ == "__main__":
    main()
