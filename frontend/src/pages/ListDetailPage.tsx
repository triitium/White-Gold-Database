import { FormEvent, useCallback, useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router";

import { useAuth } from "../auth/AuthContext";
import { Loading } from "../components/Loading";
import { Poster } from "../components/Poster";
import { api, ApiError } from "../lib/api";
import type { PublicMovieList } from "../types";

export function ListDetailPage() {
  const { listId } = useParams();
  const { user } = useAuth();
  const navigate = useNavigate();

  const [movieList, setMovieList] = useState<PublicMovieList | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [savingList, setSavingList] = useState(false);
  const [savingMovieId, setSavingMovieId] = useState<string | null>(null);
  const [notes, setNotes] = useState<Record<string, string>>({});

  const load = useCallback(async () => {
    if (!listId) return;

    setLoading(true);
    setError(null);

    try {
      const result = await api<PublicMovieList>(`/lists/${listId}`);

      setMovieList(result);
      setTitle(result.title);
      setDescription(result.description ?? "");
      setNotes(
        Object.fromEntries(
          result.items.map((item) => [
            item.movie.id,
            item.note ?? "",
          ]),
        ),
      );
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Could not load list");
    } finally {
      setLoading(false);
    }
  }, [listId]);

  useEffect(() => {
    void load();
  }, [load]);

  if (loading && !movieList) {
    return <Loading label="Loading list…" />;
  }

  if (error && !movieList) {
    return <div className="alert alert--error">{error}</div>;
  }

  if (!movieList) return null;

  const currentList = movieList;

  const isOwner =
    user !== null &&
    movieList.created_by !== null &&
    movieList.created_by.id === user.id;

  const canModerate = user?.role === "admin";

  async function saveList(event: FormEvent) {
    event.preventDefault();

    setSavingList(true);
    setError(null);

    try {
      await api(`/lists/${currentList.id}`, {
        method: "PATCH",
        csrf: true,
        body: JSON.stringify({
          title: title.trim(),
          description: description.trim() || null,
        }),
      });

      await load();
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Could not update list");
    } finally {
      setSavingList(false);
    }
  }

  async function deleteList() {
    if (!window.confirm(`Delete "${currentList.title}"?`)) return;

    try {
      const path =
        isOwner
          ? `/lists/${currentList.id}`
          : `/admin/lists/${currentList.id}`;

      await api(path, {
        method: "DELETE",
        csrf: true,
      });

      navigate("/lists");
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Could not delete list");
    }
  }

  async function saveNote(movieId: string) {
    setSavingMovieId(movieId);
    setError(null);

    try {
      await api(`/lists/${currentList.id}/items/${movieId}`, {
        method: "PATCH",
        csrf: true,
        body: JSON.stringify({
          note: notes[movieId]?.trim() || null,
        }),
      });

      await load();
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Could not update note");
    } finally {
      setSavingMovieId(null);
    }
  }

  async function removeMovie(movieId: string) {
    if (!window.confirm("Remove this film from the list?")) return;

    setSavingMovieId(movieId);
    setError(null);

    try {
      await api(`/lists/${currentList.id}/items/${movieId}`, {
        method: "DELETE",
        csrf: true,
      });

      await load();
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Could not remove film");
    } finally {
      setSavingMovieId(null);
    }
  }

  async function move(movieId: string, direction: -1 | 1) {
    const ids = currentList.items.map((item) => item.movie.id);
    const index = ids.indexOf(movieId);
    const target = index + direction;

    if (index < 0 || target < 0 || target >= ids.length) return;

    [ids[index], ids[target]] = [ids[target], ids[index]];

    setSavingMovieId(movieId);
    setError(null);

    try {
      await api(`/lists/${currentList.id}/items/order`, {
        method: "PUT",
        csrf: true,
        body: JSON.stringify({ movie_ids: ids }),
      });

      await load();
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Could not reorder list");
    } finally {
      setSavingMovieId(null);
    }
  }

  return (
    <section className="stack stack--large">
      {error && <div className="alert alert--error">{error}</div>}

      <div className="page-heading page-heading--split">
        <div>
          <p className="eyebrow">Movie list</p>
          <h1>{movieList.title}</h1>
          <p className="muted">
            by {movieList.created_by?.username ?? "Deleted user"} ·{" "}
            {movieList.items.length} film
            {movieList.items.length === 1 ? "" : "s"}
          </p>
        </div>

        {(isOwner || canModerate) && (
          <button
            className="button button--danger-ghost"
            onClick={() => void deleteList()}
          >
            Delete list
          </button>
        )}
      </div>

      {movieList.description && !isOwner && (
        <div className="content-card">
          <p className="prose">{movieList.description}</p>
        </div>
      )}

      {isOwner && (
        <form className="content-card list-edit-form" onSubmit={saveList}>
          <h2>Edit list</h2>

          <label className="field">
            <span>Title</span>
            <input
              value={title}
              maxLength={200}
              onChange={(event) => setTitle(event.target.value)}
            />
          </label>

          <label className="field">
            <span>Description</span>
            <textarea
              rows={3}
              value={description}
              onChange={(event) => setDescription(event.target.value)}
            />
          </label>

          <div>
            <button
              className="button"
              type="submit"
              disabled={savingList || !title.trim()}
            >
              {savingList ? "Saving…" : "Save list"}
            </button>
          </div>
        </form>
      )}

      {movieList.items.length === 0 ? (
        <div className="content-card empty-state">
          This list does not contain any films yet.
        </div>
      ) : (
        <div className="list-items">
          {movieList.items.map((item, index) => (
            <article className="content-card list-item-card" key={item.movie.id}>
              <Link
                to={`/movies/${item.movie.id}`}
                className="list-item-card__poster"
              >
                <Poster
                  src={item.movie.poster_path ?? item.movie.poster_url}
                  alt={item.movie.title}
                  className="poster--list"
                />
              </Link>

              <div className="list-item-card__content">
                <div>
                  <span className="eyebrow">#{index + 1}</span>

                  <h2>
                    <Link to={`/movies/${item.movie.id}`}>
                      {item.movie.title}
                    </Link>
                  </h2>

                  {item.movie.release_year && (
                    <span className="tiny-muted">
                      {item.movie.release_year}
                    </span>
                  )}
                </div>

                {isOwner ? (
                  <label className="field">
                    <span>Note</span>
                    <textarea
                      rows={3}
                      value={notes[item.movie.id] ?? ""}
                      onChange={(event) =>
                        setNotes((current) => ({
                          ...current,
                          [item.movie.id]: event.target.value,
                        }))
                      }
                      placeholder="Optional note about this film"
                    />
                  </label>
                ) : (
                  item.note && <p className="prose">{item.note}</p>
                )}

                {isOwner && (
                  <div className="list-item-card__actions">
                    <button
                      className="button button--ghost button--small"
                      disabled={index === 0 || savingMovieId !== null}
                      onClick={() => void move(item.movie.id, -1)}
                    >
                      ↑
                    </button>

                    <button
                      className="button button--ghost button--small"
                      disabled={
                        index === movieList.items.length - 1 ||
                        savingMovieId !== null
                      }
                      onClick={() => void move(item.movie.id, 1)}
                    >
                      ↓
                    </button>

                    <button
                      className="button button--small"
                      disabled={savingMovieId !== null}
                      onClick={() => void saveNote(item.movie.id)}
                    >
                      {savingMovieId === item.movie.id
                        ? "Saving…"
                        : "Save note"}
                    </button>

                    <button
                      className="button button--danger-ghost button--small"
                      disabled={savingMovieId !== null}
                      onClick={() => void removeMovie(item.movie.id)}
                    >
                      Remove
                    </button>
                  </div>
                )}
              </div>
            </article>
          ))}
        </div>
      )}
    </section>
  );
}
