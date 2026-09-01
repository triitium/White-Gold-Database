import { FormEvent, useState, type ReactNode } from "react";

import { useCatalog } from "../hooks/useCatalog";
import { api, ApiError } from "../lib/api";
import type {
  CountryOption,
  GenreOption,
  LanguageOption,
  PersonOption,
  StudioOption,
} from "../types";

export function CatalogPage() {
  const catalog = useCatalog();

  return (
    <section className="stack stack--large">
      <header className="page-heading">
        <p className="eyebrow">Shared metadata</p>
        <h1>Catalog</h1>
        <p className="muted">
          All logged-in users may add and edit shared reference data. Every
          change is written to the audit log.
        </p>
      </header>

      <div className="catalog-grid">
        <GenrePanel rows={catalog.genres} reload={catalog.reload} />
        <CountryPanel rows={catalog.countries} reload={catalog.reload} />
        <LanguagePanel rows={catalog.languages} reload={catalog.reload} />
        <StudioPanel rows={catalog.studios} reload={catalog.reload} />
      </div>

      <PeoplePanel />
    </section>
  );
}

function GenrePanel({ rows, reload }: { rows: GenreOption[]; reload: () => Promise<void> }) {
  const [name, setName] = useState("");
  const [error, setError] = useState<string | null>(null);

  async function create(event: FormEvent) {
    event.preventDefault();
    try {
      await api("/catalog/genres", {
        method: "POST",
        csrf: true,
        body: JSON.stringify({ name }),
      });
      setName("");
      await reload();
    } catch (err) {
      setError(errorText(err));
    }
  }

  async function edit(row: GenreOption) {
    const next = window.prompt("Genre name", row.name)?.trim();
    if (!next || next === row.name) return;
    try {
      await api(`/catalog/genres/${row.id}`, {
        method: "PATCH",
        csrf: true,
        body: JSON.stringify({ name: next }),
      });
      await reload();
    } catch (err) {
      setError(errorText(err));
    }
  }

  return (
    <CatalogPanel title="Genres" error={error}>
      <InlineCreate value={name} onChange={setName} onSubmit={create} placeholder="New genre" />
      <CatalogRows>
        {rows.map((row) => (
          <CatalogRow key={row.id} primary={row.name} secondary={row.tmdb_id ? `TMDB ${row.tmdb_id}` : undefined} onEdit={() => void edit(row)} />
        ))}
      </CatalogRows>
    </CatalogPanel>
  );
}

function CountryPanel({ rows, reload }: { rows: CountryOption[]; reload: () => Promise<void> }) {
  const [name, setName] = useState("");
  const [iso2, setIso2] = useState("");
  const [error, setError] = useState<string | null>(null);

  async function create(event: FormEvent) {
    event.preventDefault();
    try {
      await api("/catalog/countries", {
        method: "POST",
        csrf: true,
        body: JSON.stringify({ name, iso2: iso2.trim() || null }),
      });
      setName("");
      setIso2("");
      await reload();
    } catch (err) {
      setError(errorText(err));
    }
  }

  async function edit(row: CountryOption) {
    const nameValue = window.prompt("Country name", row.name);
    if (nameValue == null) return;
    const isoValue = window.prompt("ISO2 (empty = none)", row.iso2 ?? "");
    if (isoValue == null) return;
    try {
      await api(`/catalog/countries/${row.id}`, {
        method: "PATCH",
        csrf: true,
        body: JSON.stringify({
          name: nameValue.trim(),
          iso2: isoValue.trim() || null,
        }),
      });
      await reload();
    } catch (err) {
      setError(errorText(err));
    }
  }

  return (
    <CatalogPanel title="Countries" error={error}>
      <form className="catalog-create-row" onSubmit={create}>
        <input placeholder="New country" value={name} onChange={(e) => setName(e.target.value)} required />
        <input className="short-input" placeholder="ISO2" maxLength={2} value={iso2} onChange={(e) => setIso2(e.target.value)} />
        <button className="button button--small">Add</button>
      </form>
      <CatalogRows>
        {rows.map((row) => (
          <CatalogRow key={row.id} primary={row.name} secondary={[row.iso2, row.iso3].filter(Boolean).join(" / ") || undefined} onEdit={() => void edit(row)} />
        ))}
      </CatalogRows>
    </CatalogPanel>
  );
}

function LanguagePanel({ rows, reload }: { rows: LanguageOption[]; reload: () => Promise<void> }) {
  const [name, setName] = useState("");
  const [code, setCode] = useState("");
  const [error, setError] = useState<string | null>(null);

  async function create(event: FormEvent) {
    event.preventDefault();
    try {
      await api("/catalog/languages", {
        method: "POST",
        csrf: true,
        body: JSON.stringify({ name, iso_code: code }),
      });
      setName("");
      setCode("");
      await reload();
    } catch (err) {
      setError(errorText(err));
    }
  }

  async function edit(row: LanguageOption) {
    const nameValue = window.prompt("Language name", row.name);
    if (nameValue == null) return;
    const codeValue = window.prompt("Language code", row.iso_code);
    if (codeValue == null) return;
    try {
      await api(`/catalog/languages/${row.id}`, {
        method: "PATCH",
        csrf: true,
        body: JSON.stringify({ name: nameValue.trim(), iso_code: codeValue.trim() }),
      });
      await reload();
    } catch (err) {
      setError(errorText(err));
    }
  }

  return (
    <CatalogPanel title="Languages" error={error}>
      <form className="catalog-create-row" onSubmit={create}>
        <input placeholder="New language" value={name} onChange={(e) => setName(e.target.value)} required />
        <input className="short-input" placeholder="Code" value={code} onChange={(e) => setCode(e.target.value)} required />
        <button className="button button--small">Add</button>
      </form>
      <CatalogRows>
        {rows.map((row) => (
          <CatalogRow key={row.id} primary={row.name} secondary={row.iso_code} onEdit={() => void edit(row)} />
        ))}
      </CatalogRows>
    </CatalogPanel>
  );
}

function StudioPanel({ rows, reload }: { rows: StudioOption[]; reload: () => Promise<void> }) {
  const [name, setName] = useState("");
  const [error, setError] = useState<string | null>(null);

  async function create(event: FormEvent) {
    event.preventDefault();
    try {
      await api("/catalog/studios", {
        method: "POST",
        csrf: true,
        body: JSON.stringify({ name }),
      });
      setName("");
      await reload();
    } catch (err) {
      setError(errorText(err));
    }
  }

  async function edit(row: StudioOption) {
    const next = window.prompt("Studio name", row.name)?.trim();
    if (!next || next === row.name) return;
    try {
      await api(`/catalog/studios/${row.id}`, {
        method: "PATCH",
        csrf: true,
        body: JSON.stringify({ name: next }),
      });
      await reload();
    } catch (err) {
      setError(errorText(err));
    }
  }

  return (
    <CatalogPanel title="Studios" error={error}>
      <InlineCreate value={name} onChange={setName} onSubmit={create} placeholder="New studio" />
      <CatalogRows>
        {rows.map((row) => (
          <CatalogRow key={row.id} primary={row.name} secondary={row.tmdb_id ? `TMDB ${row.tmdb_id}` : undefined} onEdit={() => void edit(row)} />
        ))}
      </CatalogRows>
    </CatalogPanel>
  );
}

function PeoplePanel() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<PersonOption[]>([]);
  const [error, setError] = useState<string | null>(null);

  async function search(event?: FormEvent) {
    event?.preventDefault();
    if (!query.trim()) return;
    try {
      setResults(await api<PersonOption[]>(`/catalog/people?q=${encodeURIComponent(query.trim())}&limit=100`));
    } catch (err) {
      setError(errorText(err));
    }
  }

  async function create() {
    const name = query.trim();
    if (!name) return;
    try {
      await api("/catalog/people", {
        method: "POST",
        csrf: true,
        body: JSON.stringify({ name }),
      });
      await search();
    } catch (err) {
      setError(errorText(err));
    }
  }

  async function edit(person: PersonOption) {
    const name = window.prompt("Person name", person.name);
    if (name == null) return;
    const imdb = window.prompt("IMDb ID (optional)", person.imdb_id ?? "");
    if (imdb == null) return;
    try {
      await api(`/catalog/people/${person.id}`, {
        method: "PATCH",
        csrf: true,
        body: JSON.stringify({ name: name.trim(), imdb_id: imdb.trim() || null }),
      });
      await search();
    } catch (err) {
      setError(errorText(err));
    }
  }

  return (
    <CatalogPanel title="People" error={error} wide>
      <form className="catalog-create-row" onSubmit={search}>
        <input placeholder="Search person" value={query} onChange={(e) => setQuery(e.target.value)} />
        <button className="button button--small">Search</button>
        <button type="button" className="button button--ghost button--small" onClick={() => void create()}>
          Create exact name
        </button>
      </form>
      <CatalogRows>
        {results.map((row) => (
          <CatalogRow
            key={row.id}
            primary={row.name}
            secondary={[row.birth_date?.slice(0, 4), row.imdb_id, row.tmdb_id ? `TMDB ${row.tmdb_id}` : null].filter(Boolean).join(" · ") || undefined}
            onEdit={() => void edit(row)}
          />
        ))}
      </CatalogRows>
    </CatalogPanel>
  );
}

function CatalogPanel({
  title,
  children,
  error,
  wide = false,
}: {
  title: string;
  children: ReactNode;
  error: string | null;
  wide?: boolean;
}) {
  return (
    <section className={`content-card catalog-panel ${wide ? "catalog-panel--wide" : ""}`}>
      <h2>{title}</h2>
      {error && <div className="alert alert--error">{error}</div>}
      {children}
    </section>
  );
}

function InlineCreate({
  value,
  onChange,
  onSubmit,
  placeholder,
}: {
  value: string;
  onChange: (value: string) => void;
  onSubmit: (event: FormEvent) => void;
  placeholder: string;
}) {
  return (
    <form className="catalog-create-row" onSubmit={onSubmit}>
      <input placeholder={placeholder} value={value} onChange={(e) => onChange(e.target.value)} required />
      <button className="button button--small">Add</button>
    </form>
  );
}

function CatalogRows({ children }: { children: ReactNode }) {
  return <div className="catalog-rows">{children}</div>;
}

function CatalogRow({
  primary,
  secondary,
  onEdit,
}: {
  primary: string;
  secondary?: string;
  onEdit: () => void;
}) {
  return (
    <div className="catalog-row">
      <div>
        <strong>{primary}</strong>
        {secondary && <span>{secondary}</span>}
      </div>
      <button type="button" className="text-button" onClick={onEdit}>
        Edit
      </button>
    </div>
  );
}

function errorText(err: unknown) {
  return err instanceof ApiError ? err.detail : "Request failed";
}
