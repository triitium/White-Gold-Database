import { FormEvent, useCallback, useEffect, useMemo, useState } from "react";
import { Link, useNavigate, useParams } from "react-router";

import { useAuth } from "../auth/AuthContext";
import { BrickRating } from "../components/BrickRating";
import { Loading } from "../components/Loading";
import { Poster } from "../components/Poster";
import { ScoreBadge } from "../components/ScoreBadge";
import { api, ApiError } from "../lib/api";
import { dateLabel, formatRuntime } from "../lib/format";
import type {
  ExternalRatingRead,
  MovieRead,
  Review,
  UserMovieState,
} from "../types";

export function MovieDetailPage() {
  const { movieId } = useParams();
  const { user } = useAuth();
  const navigate = useNavigate();

  const [movie, setMovie] = useState<MovieRead | null>(null);
  const [state, setState] = useState<UserMovieState | null>(null);
  const [reviews, setReviews] = useState<Review[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const reload = useCallback(async () => {
    if (!movieId) return;

    setLoading(true);
    setError(null);

    try {
      const [movieResult, reviewResult] = await Promise.all([
        api<MovieRead>(`/movies/${movieId}`),
        api<Review[]>(`/movies/${movieId}/reviews`),
      ]);

      setMovie(movieResult);
      setReviews(reviewResult);

      if (user) {
        const stateResult = await api<UserMovieState | null>(
          `/movies/${movieId}/me`,
        );
        setState(stateResult);
      } else {
        setState(null);
      }
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.detail
          : "Could not load movie",
      );
    } finally {
      setLoading(false);
    }
  }, [movieId, user]);

  useEffect(() => {
    void reload();
  }, [reload]);

  async function softDelete() {
    if (!movie || !window.confirm(`Delete "${movie.title}"?`)) {
      return;
    }

    try {
      await api(`/movies/${movie.id}`, {
        method: "DELETE",
        csrf: true,
      });
      navigate("/movies");
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Delete failed");
    }
  }

  if (loading && !movie) {
    return <Loading label="Loading film…" />;
  }

  if (error && !movie) {
    return <div className="alert alert--error">{error}</div>;
  }

  if (!movie) {
    return null;
  }

  const cast = movie.credits
    .filter((credit) => credit.credit_type === "cast")
    .sort((a, b) => (a.billing_order ?? 99999) - (b.billing_order ?? 99999));

  const directors = movie.credits.filter(
    (credit) =>
      credit.credit_type === "crew" &&
      credit.job?.toLowerCase() === "director",
  );

  return (
    <section className="stack stack--large">
      {error && <div className="alert alert--error">{error}</div>}

      <div className="movie-hero">
        <Poster
          src={movie.poster_path ?? movie.poster_url}
          alt={movie.title}
          className="poster--hero"
        />

        <div className="movie-hero__content">
          <div>
            <p className="eyebrow">
              {movie.release_year ?? "Film"}
            </p>
            <h1>{movie.title}</h1>
            {movie.original_title &&
              movie.original_title !== movie.title && (
                <p className="movie-original-title">
                  {movie.original_title}
                </p>
              )}
          </div>

          <div className="movie-meta-line">
            {movie.runtime_minutes && (
              <span>{formatRuntime(movie.runtime_minutes)}</span>
            )}
            {movie.release_date && (
              <span>{movie.release_date}</span>
            )}
            {movie.countries.map((country) => (
              <span key={country.id}>{country.name}</span>
            ))}
          </div>

          <div className="tag-row">
            {movie.genres.map((genre) => (
              <span className="tag" key={genre.id}>
                {genre.name}
              </span>
            ))}
          </div>

          {directors.length > 0 && (
            <p>
              <span className="muted">Directed by </span>
              <strong>{directors.map((x) => x.name).join(", ")}</strong>
            </p>
          )}

          <div className="rating-grid">
            <ExternalScores movie={movie} />
            <div className="rating-panel rating-panel--ours">
              <span className="score-badge__label">Our rating</span>
              <BrickRating
                rating={
                  movie.community_rating == null
                    ? null
                    : Math.round(movie.community_rating)
                }
              />
              {movie.rating_count > 0 && (
                <span className="tiny-muted">
                  {movie.rating_count} community rating
                  {movie.rating_count === 1 ? "" : "s"}
                </span>
              )}
            </div>
          </div>

          {user && (
            <div className="hero-actions">
              <Link
                to={`/movies/${movie.id}/edit`}
                className="button button--ghost"
              >
                Edit movie
              </Link>
              <button
                className="button button--danger-ghost"
                onClick={() => void softDelete()}
              >
                Delete
              </button>
            </div>
          )}
        </div>
      </div>

      {user && (
        <MyMoviePanel
          movieId={movie.id}
          state={state}
          onChanged={reload}
        />
      )}

      <div className="detail-grid">
        <article className="content-card content-card--wide">
          <p className="eyebrow">Synopsis</p>
          <h2>About the film</h2>
          <p className="prose">
            {movie.overview || "No synopsis available yet."}
          </p>

          {movie.editorial_note && (
            <>
              <hr />
              <p className="eyebrow">Editorial note</p>
              <p className="prose">{movie.editorial_note}</p>
            </>
          )}
        </article>

        <aside className="content-card">
          <p className="eyebrow">Details</p>
          <dl className="detail-list">
            <div>
              <dt>Languages</dt>
              <dd>
                {movie.languages.length
                  ? movie.languages
                      .map((x) => `${x.name}${x.is_original ? " ★" : ""}`)
                      .join(", ")
                  : "—"}
              </dd>
            </div>
            <div>
              <dt>Studios</dt>
              <dd>
                {movie.studios.length
                  ? movie.studios.map((x) => x.name).join(", ")
                  : "—"}
              </dd>
            </div>
            <div>
              <dt>IMDb ID</dt>
              <dd>{movie.imdb_id ?? "—"}</dd>
            </div>
          </dl>

          {movie.links.length > 0 && (
            <div className="link-stack">
              {movie.links.map((link) => (
                <a
                  key={link.id}
                  href={link.url}
                  target="_blank"
                  rel="noreferrer"
                >
                  {link.label ?? link.source}
                </a>
              ))}
            </div>
          )}
        </aside>
      </div>

      {cast.length > 0 && (
        <section className="stack">
          <div className="section-heading">
            <p className="eyebrow">Cast</p>
            <h2>Top billed cast</h2>
          </div>
          <div className="cast-grid">
            {cast.slice(0, 12).map((credit) => (
              <div className="cast-card" key={credit.credit_id}>
                <strong>{credit.name}</strong>
                <span>{credit.character_name || "—"}</span>
              </div>
            ))}
          </div>
        </section>
      )}

      <ReviewsSection
        movieId={movie.id}
        reviews={reviews}
        onChanged={reload}
      />
    </section>
  );
}

function ExternalScores({ movie }: { movie: MovieRead }) {
  const get = (
    source: string,
    type: string,
  ): ExternalRatingRead | undefined =>
    movie.external_ratings.find(
      (x) => x.source === source && x.rating_type === type,
    );

  const imdb = get("imdb", "audience");
  const rtCritics = get("rotten_tomatoes", "critics");
  const rtAudience = get("rotten_tomatoes", "audience");
  const mcCritics = get("metacritic", "critics");
  const mcAudience = get("metacritic", "audience");

  return (
    <>
      <div className="rating-panel">
        <ScoreBadge label="IMDb" value={imdb?.value ?? null} />
      </div>
      <div className="rating-panel">
        <ScoreBadge
          label="RT Critics"
          value={rtCritics?.value ?? null}
          suffix={rtCritics?.scale === 100 ? "%" : ""}
        />
      </div>
      <div className="rating-panel">
        <ScoreBadge
          label="RT Audience"
          value={rtAudience?.value ?? null}
          suffix={rtAudience?.scale === 100 ? "%" : ""}
        />
      </div>
      <div className="rating-panel">
        <ScoreBadge label="Metacritic" value={mcCritics?.value ?? null} />
        {mcAudience && (
          <span className="tiny-muted">
            Users {mcAudience.value}/{mcAudience.scale}
          </span>
        )}
      </div>
    </>
  );
}

function MyMoviePanel({
  movieId,
  state,
  onChanged,
}: {
  movieId: string;
  state: UserMovieState | null;
  onChanged: () => Promise<void>;
}) {
  const [rating, setRating] = useState<number | null>(state?.rating ?? null);
  const [watched, setWatched] = useState(state?.watched ?? false);
  const [favorite, setFavorite] = useState(state?.favorite ?? false);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    setRating(state?.rating ?? null);
    setWatched(state?.watched ?? false);
    setFavorite(state?.favorite ?? false);
  }, [state]);

  async function save() {
    setSaving(true);
    try {
      await api(`/movies/${movieId}/me`, {
        method: "PATCH",
        csrf: true,
        body: JSON.stringify({
          rating,
          watched,
          favorite,
        }),
      });
      await onChanged();
    } finally {
      setSaving(false);
    }
  }

  return (
    <section className="content-card my-movie-panel">
      <div>
        <p className="eyebrow">Your film</p>
        <h2>Personal rating</h2>
      </div>

      <div className="my-movie-panel__rating">
        <label className="field">
          <span>Score (0–100)</span>
          <input
            type="number"
            min="0"
            max="100"
            value={rating ?? ""}
            placeholder="—"
            onChange={(e) =>
              setRating(
                e.target.value === ""
                  ? null
                  : Number(e.target.value),
              )
            }
          />
        </label>

        <BrickRating rating={rating} />
      </div>

      <label className="toggle-row">
        <input
          type="checkbox"
          checked={watched}
          onChange={(e) => setWatched(e.target.checked)}
        />
        <span>Watched</span>
      </label>

      <label className="toggle-row">
        <input
          type="checkbox"
          checked={favorite}
          onChange={(e) => setFavorite(e.target.checked)}
        />
        <span>Favorite</span>
      </label>

      <button
        className="button"
        disabled={saving}
        onClick={() => void save()}
      >
        {saving ? "Saving…" : "Save"}
      </button>
    </section>
  );
}

function ReviewsSection({
  movieId,
  reviews,
  onChanged,
}: {
  movieId: string;
  reviews: Review[];
  onChanged: () => Promise<void>;
}) {
  const { user } = useAuth();
  const myReview = reviews.find((review) => review.user.id === user?.id);

  return (
    <section className="stack">
      <div className="section-heading">
        <p className="eyebrow">Community</p>
        <h2>Reviews</h2>
      </div>

      {user && !myReview && (
        <ReviewComposer
          movieId={movieId}
          onChanged={onChanged}
        />
      )}

      <div className="review-list">
        {reviews.length === 0 && (
          <div className="empty-state">
            No reviews yet.
          </div>
        )}

        {reviews.map((review) => (
          <ReviewCard
            key={review.id}
            movieId={movieId}
            review={review}
            onChanged={onChanged}
          />
        ))}
      </div>
    </section>
  );
}

function ReviewComposer({
  movieId,
  onChanged,
}: {
  movieId: string;
  onChanged: () => Promise<void>;
}) {
  const [title, setTitle] = useState("");
  const [body, setBody] = useState("");
  const [spoilers, setSpoilers] = useState(false);
  const [saving, setSaving] = useState(false);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setSaving(true);

    try {
      await api(`/movies/${movieId}/reviews`, {
        method: "POST",
        csrf: true,
        body: JSON.stringify({
          title: title.trim() || null,
          body,
          contains_spoilers: spoilers,
        }),
      });

      setTitle("");
      setBody("");
      setSpoilers(false);
      await onChanged();
    } finally {
      setSaving(false);
    }
  }

  return (
    <form className="review-composer content-card" onSubmit={submit}>
      <h3>Write your review</h3>

      <label className="field">
        <span>Title (optional)</span>
        <input value={title} onChange={(e) => setTitle(e.target.value)} />
      </label>

      <label className="field">
        <span>Review</span>
        <textarea
          rows={6}
          value={body}
          onChange={(e) => setBody(e.target.value)}
          required
        />
      </label>

      <label className="toggle-row">
        <input
          type="checkbox"
          checked={spoilers}
          onChange={(e) => setSpoilers(e.target.checked)}
        />
        <span>Contains spoilers</span>
      </label>

      <button className="button" disabled={saving}>
        {saving ? "Publishing…" : "Publish review"}
      </button>
    </form>
  );
}

function ReviewCard({
  movieId,
  review,
  onChanged,
}: {
  movieId: string;
  review: Review;
  onChanged: () => Promise<void>;
}) {
  const { user } = useAuth();
  const canDelete =
    user?.id === review.user.id || user?.role === "admin";

  async function remove() {
    if (!window.confirm("Delete this review?")) return;

    if (user?.role === "admin" && user.id !== review.user.id) {
      await api(`/admin/reviews/${review.id}`, {
        method: "DELETE",
        csrf: true,
      });
    } else {
      await api(
        `/movies/${movieId}/reviews/${review.id}`,
        {
          method: "DELETE",
          csrf: true,
        },
      );
    }

    await onChanged();
  }

  return (
    <article className="review-card">
      <header className="review-card__header">
        <div>
          <strong>{review.user.username}</strong>
          <span>{dateLabel(review.updated_at)}</span>
        </div>
        <BrickRating rating={review.rating} compact />
      </header>

      {review.title && <h3>{review.title}</h3>}

      {review.contains_spoilers ? (
        <details className="spoiler-box">
          <summary>Review contains spoilers</summary>
          <p className="prose">{review.body}</p>
        </details>
      ) : (
        <p className="prose">{review.body}</p>
      )}

      {canDelete && (
        <button
          className="text-button text-button--danger"
          onClick={() => void remove()}
        >
          Delete review
        </button>
      )}
    </article>
  );
}
