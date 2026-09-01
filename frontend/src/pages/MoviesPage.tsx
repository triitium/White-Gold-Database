import { FormEvent, useEffect, useMemo, useState } from "react";
import { Link, useSearchParams } from "react-router";

import { BrickRating } from "../components/BrickRating";
import { Loading } from "../components/Loading";
import { Poster } from "../components/Poster";
import { ScoreBadge } from "../components/ScoreBadge";
import { api, ApiError } from "../lib/api";
import { formatRuntime } from "../lib/format";
import type { MovieListItem, Page } from "../types";

const PAGE_SIZE = 25;

type GenreOption = {
  id: string;
  name: string;
};

export function MoviesPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [data, setData] = useState<Page<MovieListItem> | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [genres, setGenres] = useState<GenreOption[]>([]);

  const page = Math.max(1, Number(searchParams.get("page") ?? "1"));
  const query = searchParams.get("q") ?? "";
  const yearFrom = searchParams.get("year_from") ?? "";
  const yearTo = searchParams.get("year_to") ?? "";
  const sort = searchParams.get("sort") ?? "title";
  const direction = searchParams.get("direction") ?? "asc";
  const genreId = searchParams.get("genre_id") ?? "";

  const [draftQuery, setDraftQuery] = useState(query);
  const [draftYearFrom, setDraftYearFrom] = useState(yearFrom);
  const [draftYearTo, setDraftYearTo] = useState(yearTo);
  const [draftGenreId, setDraftGenreId] = useState(genreId);

  const requestPath = useMemo(() => {
    const params = new URLSearchParams();

    params.set("page", String(page));
    params.set("page_size", String(PAGE_SIZE));
    params.set("sort", sort);
    params.set("direction", direction);

    if (query) params.set("q", query);
    if (yearFrom) params.set("year_from", yearFrom);
    if (yearTo) params.set("year_to", yearTo);
    if (genreId) params.set("genre_id", genreId);

    return `/movies?${params.toString()}`;
  }, [page, query, yearFrom, yearTo, genreId, sort, direction]);

  useEffect(() => {
    let cancelled = false;

    api<GenreOption[]>("/movies/filter-options/genres")
      .then((rows) => {
        if (!cancelled) setGenres(rows);
      })
      .catch(() => {
        if (!cancelled) setGenres([]);
      });

    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    let cancelled = false;

    setLoading(true);
    setError(null);

    api<Page<MovieListItem>>(requestPath)
      .then((result) => {
        if (!cancelled) setData(result);
      })
      .catch((err) => {
        if (!cancelled) {
          setError(
            err instanceof ApiError
              ? err.detail
              : "Could not load movies",
          );
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [requestPath]);

  function applyFilters(event: FormEvent) {
    event.preventDefault();

    const next = new URLSearchParams(searchParams);
    next.delete("page");

    setOrDelete(next, "q", draftQuery.trim());
    setOrDelete(next, "year_from", draftYearFrom);
    setOrDelete(next, "year_to", draftYearTo);
    setOrDelete(next, "genre_id", draftGenreId);

    setSearchParams(next);
  }

  function changeSort(value: string) {
    const next = new URLSearchParams(searchParams);
    next.set("sort", value);
    next.set("page", "1");
    setSearchParams(next);
  }

  function toggleDirection() {
    const next = new URLSearchParams(searchParams);
    next.set(
      "direction",
      direction === "asc" ? "desc" : "asc",
    );
    next.set("page", "1");
    setSearchParams(next);
  }

  function gotoPage(nextPage: number) {
    const next = new URLSearchParams(searchParams);
    next.set("page", String(nextPage));
    setSearchParams(next);
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  return (
    <section className="stack stack--large">
      <header className="page-heading page-heading--split">
        <div>
          <p className="eyebrow">Database</p>
          <h1>Movies</h1>
          <p className="muted">
            {data
              ? `${data.total.toLocaleString()} films`
              : "Browse the catalogue"}
          </p>
        </div>
      </header>

      <form className="filter-bar" onSubmit={applyFilters}>
        <label className="field field--search">
          <span>Search</span>
          <input
            placeholder="Title or original title"
            value={draftQuery}
            onChange={(e) => setDraftQuery(e.target.value)}
          />
        </label>

        <label className="field field--compact">
          <span>Year from</span>
          <input
            type="number"
            min="1880"
            max="2200"
            value={draftYearFrom}
            onChange={(e) => setDraftYearFrom(e.target.value)}
          />
        </label>

        <label className="field field--compact">
          <span>Year to</span>
          <input
            type="number"
            min="1880"
            max="2200"
            value={draftYearTo}
            onChange={(e) => setDraftYearTo(e.target.value)}
          />
        </label>

        <label className="field field--compact">
          <span>Genre</span>
          <select
            value={draftGenreId}
            onChange={(e) => setDraftGenreId(e.target.value)}
          >
            <option value="">All genres</option>
            {genres.map((genre) => (
              <option value={genre.id} key={genre.id}>
                {genre.name}
              </option>
            ))}
          </select>
        </label>

        <label className="field field--compact">
          <span>Sort</span>
          <select value={sort} onChange={(e) => changeSort(e.target.value)}>
            <option value="title">Title</option>
            <option value="year">Year</option>
            <option value="runtime">Runtime</option>
            <option value="created">Added</option>
            <option value="updated">Updated</option>
          </select>
        </label>

        <button
          type="button"
          className="button button--ghost filter-direction"
          onClick={toggleDirection}
          aria-label={`Sort ${direction === "asc" ? "descending" : "ascending"}`}
        >
          {direction === "asc" ? "↑" : "↓"}
        </button>

        <button className="button">Apply</button>
      </form>

      {error && <div className="alert alert--error">{error}</div>}

      {loading && !data ? (
        <Loading label="Loading movies…" />
      ) : (
        <>
          <div className="movie-table-shell">
            <table className="movie-table">
              <thead>
                <tr>
                  <th>Movie</th>
                  <th>Year</th>
                  <th>Runtime</th>
                  <th>IMDb</th>
                  <th>RT C</th>
                  <th>RT A</th>
                  <th>MC</th>
                  <th>Our rating</th>
                </tr>
              </thead>
              <tbody>
                {data?.items.map((movie) => (
                  <MovieRow movie={movie} key={movie.id} />
                ))}
              </tbody>
            </table>

            {data?.items.length === 0 && (
              <div className="empty-state">
                No films match these filters.
              </div>
            )}
          </div>

          {data && (
            <div className="pagination">
              <button
                className="button button--ghost"
                disabled={!data.has_previous}
                onClick={() => gotoPage(data.page - 1)}
              >
                Previous
              </button>

              <span>
                Page <strong>{data.page}</strong>
                {data.pages > 0 && <> of {data.pages}</>}
              </span>

              <button
                className="button button--ghost"
                disabled={!data.has_next}
                onClick={() => gotoPage(data.page + 1)}
              >
                Next
              </button>
            </div>
          )}
        </>
      )}
    </section>
  );
}

function MovieRow({ movie }: { movie: MovieListItem }) {
  return (
    <tr>
      <td>
        <Link className="movie-cell" to={`/movies/${movie.id}`}>
          <Poster
            src={movie.poster_path ?? movie.poster_url}
            alt={movie.title}
            className="poster--table"
          />
          <span className="movie-cell__text">
            <strong>{movie.title}</strong>
            {movie.original_title &&
              movie.original_title !== movie.title && (
                <span>{movie.original_title}</span>
              )}
            {movie.genres.length > 0 && (
              <span className="genre-line">
                {movie.genres.join(" · ")}
              </span>
            )}
          </span>
        </Link>
      </td>
      <td>{movie.release_year ?? "—"}</td>
      <td>{formatRuntime(movie.runtime_minutes)}</td>
      <td>
        <ScoreBadge label="IMDb" value={movie.imdb_rating} />
      </td>
      <td>
        <ScoreBadge
          label="RT Critics"
          value={movie.rt_critics_rating}
          suffix="%"
        />
      </td>
      <td>
        <ScoreBadge
          label="RT Audience"
          value={movie.rt_audience_rating}
          suffix="%"
        />
      </td>
      <td>
        <ScoreBadge
          label="Metacritic"
          value={movie.metacritic_critics_rating}
        />
      </td>
      <td>
        <BrickRating
          rating={
            movie.community_rating == null
              ? null
              : Math.round(movie.community_rating)
          }
          compact
        />
        {movie.rating_count > 0 && (
          <span className="tiny-muted">
            {movie.rating_count} rating{movie.rating_count === 1 ? "" : "s"}
          </span>
        )}
      </td>
    </tr>
  );
}

function setOrDelete(
  params: URLSearchParams,
  key: string,
  value: string,
) {
  if (value) {
    params.set(key, value);
  } else {
    params.delete(key);
  }
}
