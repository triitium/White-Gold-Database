import { FormEvent, useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router";

import { CreditEditor } from "../components/movie/CreditEditor";
import { LanguageSelector } from "../components/movie/LanguageSelector";
import { ReferenceMultiSelect } from "../components/movie/ReferenceMultiSelect";
import { Loading } from "../components/Loading";
import { useCatalog } from "../hooks/useCatalog";
import { api, ApiError } from "../lib/api";
import type { EditableCredit, MovieRead } from "../types";

export function MovieEditPage() {
  const { movieId } = useParams();
  const navigate = useNavigate();
  const catalog = useCatalog();
  const [movie, setMovie] = useState<MovieRead | null>(null);
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
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!movieId) return;
    api<MovieRead>(`/movies/${movieId}`)
      .then((data) => {
        setMovie(data);
        setForm({
          title: data.title,
          originalTitle: data.original_title ?? "",
          releaseYear: data.release_year?.toString() ?? "",
          releaseDate: data.release_date ?? "",
          runtime: data.runtime_minutes?.toString() ?? "",
          overview: data.overview ?? "",
          editorialNote: data.editorial_note ?? "",
          posterUrl: data.poster_url ?? "",
          imdbId: data.imdb_id ?? "",
        });
        setGenreIds(data.genres.map((x) => x.id));
        setCountryIds(data.countries.map((x) => x.id));
        setStudioIds(data.studios.map((x) => x.id));
        setLanguages(
          data.languages.map((x) => ({
            language_id: x.id,
            is_original: x.is_original,
          })),
        );
        setCredits(
          data.credits.map((x) => ({
            key: x.credit_id,
            person_id: x.person_id,
            person_name: x.name,
            credit_type: x.credit_type,
            job: x.job ?? "",
            character_name: x.character_name ?? "",
            billing_order: x.billing_order,
          })),
        );
        setLinksText(
          data.links
            .map((x) => `${x.source}|${x.label ?? ""}|${x.url}`)
            .join("\n"),
        );
      })
      .catch((err) =>
        setError(err instanceof ApiError ? err.detail : "Could not load movie"),
      )
      .finally(() => setLoading(false));
  }, [movieId]);

  function update(key: keyof typeof form, value: string) {
    setForm((current) => ({ ...current, [key]: value }));
  }

  async function submit(event: FormEvent) {
    event.preventDefault();
    if (!movieId) return;
    setSaving(true);
    setError(null);

    try {
      await api(`/movies/${movieId}`, {
        method: "PATCH",
        csrf: true,
        body: JSON.stringify({
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
          studio_ids: studioIds,
          languages,
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
        }),
      });
      navigate(`/movies/${movieId}`);
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Update failed");
    } finally {
      setSaving(false);
    }
  }

  if (loading) return <Loading label="Loading editor…" />;
  if (!movie)
    return <div className="alert alert--error">{error ?? "Movie not found"}</div>;

  return (
    <section className="stack stack--large">
      <header className="page-heading">
        <p className="eyebrow">Edit movie</p>
        <h1>{movie.title}</h1>
        <p className="muted">
          Shared movie metadata. Changes are written to the audit history.
        </p>
      </header>

      <form className="manual-form content-card" onSubmit={submit}>
        {error && <div className="alert alert--error">{error}</div>}
        <div className="form-grid">
          <label className="field field--span-2">
            <span>Title *</span>
            <input value={form.title} onChange={(e) => update("title", e.target.value)} required />
          </label>
          <label className="field field--span-2">
            <span>Original title</span>
            <input value={form.originalTitle} onChange={(e) => update("originalTitle", e.target.value)} />
          </label>
          <label className="field">
            <span>Release year</span>
            <input type="number" min="1880" max="2200" value={form.releaseYear} onChange={(e) => update("releaseYear", e.target.value)} />
          </label>
          <label className="field">
            <span>Release date</span>
            <input type="date" value={form.releaseDate} onChange={(e) => update("releaseDate", e.target.value)} />
          </label>
          <label className="field">
            <span>Runtime</span>
            <input type="number" min="1" value={form.runtime} onChange={(e) => update("runtime", e.target.value)} />
          </label>
          <label className="field">
            <span>IMDb ID</span>
            <input value={form.imdbId} onChange={(e) => update("imdbId", e.target.value)} />
          </label>
          <label className="field field--span-4">
            <span>Poster URL</span>
            <input type="url" value={form.posterUrl} onChange={(e) => update("posterUrl", e.target.value)} />
          </label>
          <label className="field field--span-4">
            <span>Synopsis</span>
            <textarea rows={6} value={form.overview} onChange={(e) => update("overview", e.target.value)} />
          </label>
          <label className="field field--span-4">
            <span>Editorial note</span>
            <textarea rows={5} value={form.editorialNote} onChange={(e) => update("editorialNote", e.target.value)} />
          </label>

          <div className="field field--span-4 relation-heading">
            <span>Classification</span>
            <small className="field-help">
              Missing reference data? <Link to="/catalog" target="_blank" rel="noreferrer">Open Catalog manager</Link>
            </small>
          </div>
          <ReferenceMultiSelect label="Genres" options={catalog.genres} value={genreIds} onChange={setGenreIds} />
          <ReferenceMultiSelect label="Countries" options={catalog.countries} value={countryIds} onChange={setCountryIds} />
          <ReferenceMultiSelect label="Studios" options={catalog.studios} value={studioIds} onChange={setStudioIds} />
          <div className="field">
            <span>Catalog status</span>
            <div className="catalog-status">{catalog.loading ? "Loading…" : "Reference data loaded"}</div>
          </div>
          <div className="field--span-4">
            <LanguageSelector options={catalog.languages} value={languages} onChange={setLanguages} />
          </div>
          <CreditEditor value={credits} onChange={setCredits} />
          <label className="field field--span-4">
            <span>Links — one per line: source|label|URL</span>
            <textarea rows={5} value={linksText} onChange={(e) => setLinksText(e.target.value)} />
          </label>
        </div>

        <div className="hero-actions">
          <button className="button" disabled={saving || catalog.loading}>
            {saving ? "Saving…" : "Save changes"}
          </button>
          <Link className="button button--ghost" to={`/movies/${movieId}`}>
            Cancel
          </Link>
        </div>
      </form>
    </section>
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
