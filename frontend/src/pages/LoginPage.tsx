import { FormEvent, useState } from "react";
import { Navigate, useLocation, useNavigate } from "react-router";

import { useAuth } from "../auth/AuthContext";
import { ApiError } from "../lib/api";

export function LoginPage() {
  const { user, login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const [loginValue, setLoginValue] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  if (user) {
    return <Navigate to="/movies" replace />;
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setSubmitting(true);
    setError(null);

    try {
      await login(loginValue, password);

      const destination =
        (location.state as { from?: string } | null)?.from ??
        "/movies";

      navigate(destination, { replace: true });
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.detail
          : "Login failed",
      );
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="auth-page">
      <form className="auth-card" onSubmit={handleSubmit}>
        <div>
          <p className="eyebrow">Members</p>
          <h1>Log in</h1>
          <p className="muted">
            Public browsing stays open. Editing, ratings and reviews
            require an account.
          </p>
        </div>

        {error && <div className="alert alert--error">{error}</div>}

        <label className="field">
          <span>Username or email</span>
          <input
            autoComplete="username"
            value={loginValue}
            onChange={(e) => setLoginValue(e.target.value)}
            required
          />
        </label>

        <label className="field">
          <span>Password</span>
          <input
            type="password"
            autoComplete="current-password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
        </label>

        <button className="button" disabled={submitting}>
          {submitting ? "Logging in…" : "Log in"}
        </button>
      </form>
    </div>
  );
}
