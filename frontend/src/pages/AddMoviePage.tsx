import { FormEvent, useState } from "react";
import { Link, useNavigate } from "react-router";

import { CreditEditor } from "../components/movie/CreditEditor";
import { LanguageSelector } from "../components/movie/LanguageSelector";
import { ReferenceMultiSelect } from "../components/movie/ReferenceMultiSelect";
import { Poster } from "../components/Poster";
import { useCatalog } from "../hooks/useCatalog";
import { api, ApiError } from "../lib/api";
import type {
  EditableCredit,
  MovieCreatePayload,
  TmdbSearchItem,
  TmdbSearchResponse,
} from "../types";

type Mode = "tmdb" | "manual";

export function AddMoviePage() {
  const [mode, setMode] = useState<Mode>("tmdb");

  return (
    <section className="stack stack--large">
      <header className="page-heading">
        <p className="eyebrow">Catalogue</p>
        <h1>Add movie</h1>
        <p className="muted">
          Search TMDB for the fast path, or create a film manually for student
          films and obscure titles.
        </p>
      </header>

      <div className="segmented-control">
        <button
          className={mode === "tmdb" ? "active" : ""}
          onClick={() => setMode("tmdb")}
        >
          Search TMDB
        </button>
        <button
          className={mode === "manual" ? "active" : ""}
          onClick={() => setMode("manual")}
        >
          Manual entry
        </button>
      </div>

      {mode === "tmdb" ? <TmdbAdd /> : <ManualAdd />}
    </section>
  );
}

function TmdbAdd() {
  const navigate = useNavigate();
  const [query, setQuery] = useState("");
  const [year, setYear] = useState("");
  const [results, setResults] = useState<TmdbSearchItem[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [searching, setSearching] = useState(false);
  const [importing, setImporting] = useState<number | null>(null);

  async function search(event: FormEvent) {
    event.preventDefault();
    setSearching(true);
    setError(null);

    try {
      const params = new URLSearchParams({ q: query });
      if (year) params.set("year", year);
      const response = await api<TmdbSearchResponse>(
        `/tmdb/search?${params.toString()}`,
      );
      setResults(response.results);
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "TMDB search failed");
    } finally {
      setSearching(false);
    }
  }

  async function importMovie(tmdbId: number) {
    setImporting(tmdbId);
    setError(null);
    try {
      const result = await api<{ id: string }>(
        `/tmdb/movies/${tmdbId}/import`,
        { method: "POST", csrf: true },
      );
      navigate(`/movies/${result.id}`);
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Import failed");
    } finally {
      setImporting(null);
    }
  }

  return (
    <div className="stack">
      <form className="filter-bar" onSubmit={search}>
        <label className="field field--search">
          <span>Title</span>
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="The Grand Budapest Hotel"
            required
          />
        </label>

        <label className="field field--compact">
          <span>Year</span>
          <input
            type="number"
            min="1880"
            max="2200"
            value={year}
            onChange={(e) => setYear(e.target.value)}
          />
        </label>

        <button className="button" disabled={searching}>
          {searching ? "Searching…" : "Search"}
        </button>
      </form>

      {error && <div className="alert alert--error">{error}</div>}

      <div className="tmdb-results">
        {results.map((movie) => (
          <article className="tmdb-result" key={movie.tmdb_id}>
            <Poster
              src={movie.poster_url}
              alt={movie.title}
              className="poster--search"
            />
            <div className="tmdb-result__body">
              <div>
                <h3>{movie.title}</h3>
                <p className="muted">
                  {movie.release_year ?? "Unknown year"}
                  {movie.original_title &&
                    movie.original_title !== movie.title &&
                    ` · ${movie.original_title}`}
                </p>
              </div>
              {movie.overview && (
                <p className="tmdb-result__overview">{movie.overview}</p>
              )}
            </div>
            <button
              className="button"
              disabled={importing === movie.tmdb_id}
              onClick={() => void importMovie(movie.tmdb_id)}
            >
              {importing === movie.tmdb_id ? "Importing…" : "Use this movie"}
            </button>
          </article>
        ))}
      </div>
    </div>
  );
}

function ManualAdd() {
  const navigate = useNavigate();
  const catalog = useCatalog();
  const [form, setForm] = useState({
    title: "",
    originalTitle: "",
    releaseYear: "",
    releaseDate: "",
    runtime: "",
    overview: "",
    editorialNote: "",
    posterUrl: "",
    imdbId: "",
  });
  const [genreIds, setGenreIds] = useState<string[]>([]);
  const [countryIds, setCountryIds] = useState<string[]>([]);
  const [studioIds, setStudioIds] = useState<string[]>([]);
  const [languages, setLanguages] = useState<
    { language_id: string; is_original: boolean }[]
  >([]);
  const [credits, setCredits] = useState<EditableCredit[]>([]);
  const [linksText, setLinksText] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  function update(key: keyof typeof form, value: string) {
    setForm((current) => ({ ...current, [key]: value }));
  }

  async function submit(event: FormEvent) {
    event.preventDefault();
    setSaving(true);
    setError(null);

    const payload: MovieCreatePayload = {
      title: form.title.trim(),
      original_title: form.originalTitle.trim() || null,
      release_year: form.releaseYear ? Number(form.releaseYear) : null,
      release_date: form.releaseDate || null,
      runtime_minutes: form.runtime ? Number(form.runtime) : null,
      overview: form.overview.trim() || null,
      editorial_note: form.editorialNote.trim() || null,
      poster_url: form.posterUrl.trim() || null,
      imdb_id: form.imdbId.trim() || null,
      genre_ids: genreIds,
      country_ids: countryIds,
      languages,
      studio_ids: studioIds,
      person_credits: credits.map((credit) => ({
        person_id: credit.person_id,
        credit_type: credit.credit_type,
        job: credit.credit_type === "crew" ? credit.job.trim() || null : null,
        character_name:
          credit.credit_type === "cast"
            ? credit.character_name.trim() || null
            : null,
        billing_order: credit.billing_order,
        tmdb_credit_id: credit.tmdb_credit_id ?? null,
      })),
      links: parseLinks(linksText),
    };

    try {
      const movie = await api<{ id: string }>("/movies", {
        method: "POST",
        csrf: true,
        body: JSON.stringify(payload),
      });
      navigate(`/movies/${movie.id}`);
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Could not create movie");
    } finally {
      setSaving(false);
    }
  }

  return (
    <form className="manual-form content-card" onSubmit={submit}>
      {error && <div className="alert alert--error">{error}</div>}

      <div className="form-grid">
        <label className="field field--span-2">
          <span>Title *</span>
          <input
            value={form.title}
            onChange={(e) => update("title", e.target.value)}
            required
          />
        </label>

        <label className="field field--span-2">
          <span>Original title</span>
          <input
            value={form.originalTitle}
            onChange={(e) => update("originalTitle", e.target.value)}
          />
        </label>

        <label className="field">
          <span>Release year</span>
          <input
            type="number"
            min="1880"
            max="2200"
            value={form.releaseYear}
            onChange={(e) => update("releaseYear", e.target.value)}
          />
        </label>

        <label className="field">
          <span>Exact release date</span>
          <input
            type="date"
            value={form.releaseDate}
            onChange={(e) => update("releaseDate", e.target.value)}
          />
        </label>

        <label className="field">
          <span>Runtime (minutes)</span>
          <input
            type="number"
            min="1"
            value={form.runtime}
            onChange={(e) => update("runtime", e.target.value)}
          />
        </label>

        <label className="field">
          <span>IMDb ID</span>
          <input
            placeholder="tt1234567"
            value={form.imdbId}
            onChange={(e) => update("imdbId", e.target.value)}
          />
        </label>

        <label className="field field--span-4">
          <span>Poster URL</span>
          <input
            type="url"
            value={form.posterUrl}
            onChange={(e) => update("posterUrl", e.target.value)}
          />
        </label>

        <label className="field field--span-4">
          <span>Synopsis</span>
          <textarea
            rows={6}
            value={form.overview}
            onChange={(e) => update("overview", e.target.value)}
          />
        </label>

        <label className="field field--span-4">
          <span>Editorial note</span>
          <textarea
            rows={5}
            value={form.editorialNote}
            onChange={(e) => update("editorialNote", e.target.value)}
          />
        </label>

        <div className="field field--span-4 relation-heading">
          <span>Classification</span>
          <small className="field-help">
            Missing reference data?{" "}
            <Link to="/catalog" target="_blank" rel="noreferrer">
              Open Catalog manager
            </Link>
          </small>
        </div>

        <ReferenceMultiSelect
          label="Genres"
          options={catalog.genres}
          value={genreIds}
          onChange={setGenreIds}
        />
        <ReferenceMultiSelect
          label="Countries"
          options={catalog.countries}
          value={countryIds}
          onChange={setCountryIds}
        />
        <ReferenceMultiSelect
          label="Studios"
          options={catalog.studios}
          value={studioIds}
          onChange={setStudioIds}
        />
        <div className="field">
          <span>Catalog status</span>
          <div className="catalog-status">
            {catalog.loading ? "Loading…" : "Reference data loaded"}
          </div>
        </div>

        <div className="field--span-4">
          <LanguageSelector
            options={catalog.languages}
            value={languages}
            onChange={setLanguages}
          />
        </div>

        <CreditEditor value={credits} onChange={setCredits} />

        <label className="field field--span-4">
          <span>Links — one per line: source|label|URL</span>
          <textarea
            rows={5}
            value={linksText}
            onChange={(e) => setLinksText(e.target.value)}
            placeholder={"justwatch||https://…\ntrailer|Official trailer|https://…"}
          />
        </label>
      </div>

      <button className="button" disabled={saving || catalog.loading}>
        {saving ? "Creating…" : "Create movie"}
      </button>
    </form>
  );
}

function parseLinks(text: string) {
  return text
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean)
    .map((line) => {
      const [source, label, ...urlParts] = line.split("|");
      return {
        source: source.trim(),
        label: label.trim() || null,
        url: urlParts.join("|").trim(),
      };
    })
    .filter((link) => link.source && link.url);
}
