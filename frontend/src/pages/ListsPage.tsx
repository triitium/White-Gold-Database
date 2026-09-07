import { FormEvent, useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router";

import { useAuth } from "../auth/AuthContext";
import { Loading } from "../components/Loading";
import { api, ApiError } from "../lib/api";
import type { Page, PublicMovieList, PublicMovieListSummary } from "../types";

const PAGE_SIZE = 24;

export function ListsPage() {
  const { user } = useAuth();
  const [searchParams, setSearchParams] = useSearchParams();

  const page = Math.max(1, Number(searchParams.get("page") ?? "1"));

  const [data, setData] = useState<Page<PublicMovieListSummary> | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [creating, setCreating] = useState(false);

  async function load() {
    setLoading(true);
    setError(null);

    try {
      const result = await api<Page<PublicMovieListSummary>>(
        `/lists?page=${page}&page_size=${PAGE_SIZE}`,
      );
      setData(result);
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Could not load lists");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void load();
  }, [page]);

  async function createList(event: FormEvent) {
    event.preventDefault();

    const cleanTitle = title.trim();

    if (!cleanTitle) return;

    setCreating(true);
    setError(null);

    try {
      const created = await api<PublicMovieList>("/lists", {
        method: "POST",
        csrf: true,
        body: JSON.stringify({
          title: cleanTitle,
          description: description.trim() || null,
        }),
      });

      window.location.assign(`/lists/${created.id}`);
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Could not create list");
    } finally {
      setCreating(false);
    }
  }

  function changePage(nextPage: number) {
    const next = new URLSearchParams(searchParams);

    if (nextPage <= 1) {
      next.delete("page");
    } else {
      next.set("page", String(nextPage));
    }

    setSearchParams(next);
  }

  return (
    <section className="stack stack--large">
      <div className="page-heading">
        <p className="eyebrow">Community</p>
        <h1>Lists</h1>
        <p className="muted">
          Public movie lists curated by WGDB users.
        </p>
      </div>

      {error && <div className="alert alert--error">{error}</div>}

      {user && (
        <form className="content-card list-create-form" onSubmit={createList}>
          <div>
            <p className="eyebrow">Create</p>
            <h2>New list</h2>
          </div>

          <label className="field">
            <span>Title</span>
            <input
              value={title}
              maxLength={200}
              onChange={(event) => setTitle(event.target.value)}
              placeholder="My favourite films"
            />
          </label>

          <label className="field">
            <span>Description</span>
            <textarea
              rows={3}
              value={description}
              onChange={(event) => setDescription(event.target.value)}
              placeholder="Optional description"
            />
          </label>

          <div>
            <button
              type="submit"
              className="button"
              disabled={creating || !title.trim()}
            >
              {creating ? "Creating…" : "Create list"}
            </button>
          </div>
        </form>
      )}

      {loading && !data ? (
        <Loading label="Loading lists…" />
      ) : data && data.items.length > 0 ? (
        <>
          <div className="list-grid">
            {data.items.map((movieList) => (
              <Link
                key={movieList.id}
                to={`/lists/${movieList.id}`}
                className="content-card list-card"
              >
                <div className="list-card__header">
                  <div>
                    <h2>{movieList.title}</h2>
                    <span className="tiny-muted">
                      by {movieList.created_by?.username ?? "Deleted user"}
                    </span>
                  </div>

                  <span className="list-count">
                    {movieList.item_count} film
                    {movieList.item_count === 1 ? "" : "s"}
                  </span>
                </div>

                {movieList.description && (
                  <p className="prose list-card__description">
                    {movieList.description}
                  </p>
                )}
              </Link>
            ))}
          </div>

          {data.pages > 1 && (
            <div className="pagination">
              <button
                className="button button--ghost button--small"
                disabled={!data.has_previous}
                onClick={() => changePage(page - 1)}
              >
                Previous
              </button>

              <span>
                Page {data.page} of {data.pages}
              </span>

              <button
                className="button button--ghost button--small"
                disabled={!data.has_next}
                onClick={() => changePage(page + 1)}
              >
                Next
              </button>
            </div>
          )}
        </>
      ) : (
        <div className="content-card empty-state">
          No public lists yet.
        </div>
      )}
    </section>
  );
}
