import { FormEvent, useCallback, useEffect, useState } from "react";

import { useAuth } from "../auth/AuthContext";
import { Loading } from "../components/Loading";
import { Poster } from "../components/Poster";
import { api, ApiError } from "../lib/api";
import { dateLabel } from "../lib/format";
import type { AuditLogItem, DeletedMovie, User } from "../types";

export function AdminPage() {
  const { user: currentUser } = useAuth();
  const [users, setUsers] = useState<User[]>([]);
  const [deleted, setDeleted] = useState<DeletedMovie[]>([]);
  const [audit, setAudit] = useState<AuditLogItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [newUser, setNewUser] = useState({
    username: "",
    email: "",
    password: "",
    role: "user" as "user" | "admin",
  });
  const [creatingUser, setCreatingUser] = useState(false);

  const reload = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const [userRows, deletedRows, auditRows] = await Promise.all([
        api<User[]>("/admin/users"),
        api<DeletedMovie[]>("/admin/deleted-movies"),
        api<AuditLogItem[]>("/admin/audit?limit=100"),
      ]);

      setUsers(userRows);
      setDeleted(deletedRows);
      setAudit(auditRows);
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Admin data failed to load");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void reload();
  }, [reload]);


  async function createUser(event: FormEvent) {
    event.preventDefault();
    setCreatingUser(true);
    setError(null);
    try {
      await api("/admin/users", {
        method: "POST",
        csrf: true,
        body: JSON.stringify(newUser),
      });
      setNewUser({ username: "", email: "", password: "", role: "user" });
      await reload();
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Could not create user");
    } finally {
      setCreatingUser(false);
    }
  }

  async function setRole(user: User, role: "user" | "admin") {
    await api(`/admin/users/${user.id}/role`, {
      method: "PATCH",
      csrf: true,
      body: JSON.stringify({ role }),
    });
    await reload();
  }

  async function setActive(user: User, isActive: boolean) {
    await api(`/admin/users/${user.id}/active`, {
      method: "PATCH",
      csrf: true,
      body: JSON.stringify({ is_active: isActive }),
    });
    await reload();
  }

  async function restore(movie: DeletedMovie) {
    await api(`/movies/${movie.id}/restore`, {
      method: "POST",
      csrf: true,
    });
    await reload();
  }

  async function hardDelete(movie: DeletedMovie) {
    if (!window.confirm(`Permanently delete "${movie.title}"? This cannot be restored.`)) return;

    await api(`/movies/${movie.id}/permanent`, {
      method: "DELETE",
      csrf: true,
    });
    await reload();
  }

  if (loading) return <Loading label="Loading admin…" />;

  return (
    <section className="stack stack--large">
      <header className="page-heading">
        <p className="eyebrow">Administration</p>
        <h1>Admin</h1>
        <p className="muted">Users, recycle bin and recent audit events.</p>
      </header>

      {error && <div className="alert alert--error">{error}</div>}

      <section className="stack">
        <div className="section-heading">
          <p className="eyebrow">Access</p>
          <h2>Users</h2>
        </div>

        <form className="admin-create-user content-card" onSubmit={createUser}>
          <label className="field">
            <span>Username</span>
            <input
              value={newUser.username}
              onChange={(e) => setNewUser((x) => ({ ...x, username: e.target.value }))}
              required
            />
          </label>
          <label className="field">
            <span>Email</span>
            <input
              type="email"
              value={newUser.email}
              onChange={(e) => setNewUser((x) => ({ ...x, email: e.target.value }))}
              required
            />
          </label>
          <label className="field">
            <span>Temporary password</span>
            <input
              type="password"
              minLength={12}
              value={newUser.password}
              onChange={(e) => setNewUser((x) => ({ ...x, password: e.target.value }))}
              required
            />
          </label>
          <label className="field">
            <span>Role</span>
            <select
              value={newUser.role}
              onChange={(e) =>
                setNewUser((x) => ({ ...x, role: e.target.value as "user" | "admin" }))
              }
            >
              <option value="user">user</option>
              <option value="admin">admin</option>
            </select>
          </label>
          <button className="button" disabled={creatingUser}>
            {creatingUser ? "Creating…" : "Create account"}
          </button>
        </form>

        <div className="movie-table-shell">
          <table className="movie-table admin-table">
            <thead>
              <tr>
                <th>User</th>
                <th>Email</th>
                <th>Role</th>
                <th>Active</th>
              </tr>
            </thead>
            <tbody>
              {users.map((user) => (
                <tr key={user.id}>
                  <td><strong>{user.username}</strong></td>
                  <td>{user.email}</td>
                  <td>
                    <select
                      value={user.role}
                      disabled={user.id === currentUser?.id}
                      onChange={(e) => void setRole(user, e.target.value as "user" | "admin")}
                    >
                      <option value="user">user</option>
                      <option value="admin">admin</option>
                    </select>
                  </td>
                  <td>
                    <label className="toggle-row">
                      <input
                        type="checkbox"
                        checked={user.is_active}
                        disabled={user.id === currentUser?.id}
                        onChange={(e) => void setActive(user, e.target.checked)}
                      />
                      <span>{user.is_active ? "active" : "inactive"}</span>
                    </label>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="stack">
        <div className="section-heading">
          <p className="eyebrow">Recycle bin</p>
          <h2>Deleted movies</h2>
        </div>

        <div className="deleted-grid">
          {deleted.length === 0 && <div className="empty-state">Recycle bin is empty.</div>}

          {deleted.map((movie) => (
            <article className="deleted-card" key={movie.id}>
              <Poster
                src={movie.poster_path ?? movie.poster_url}
                alt={movie.title}
                className="poster--deleted"
              />
              <div>
                <strong>{movie.title}</strong>
                <p className="muted">
                  {movie.release_year ?? "—"} · deleted {dateLabel(movie.deleted_at)}
                  {movie.deleted_by_username ? ` by ${movie.deleted_by_username}` : ""}
                </p>
              </div>
              <div className="deleted-card__actions">
                <button className="button button--ghost" onClick={() => void restore(movie)}>
                  Restore
                </button>
                <button className="button button--danger-ghost" onClick={() => void hardDelete(movie)}>
                  Delete permanently
                </button>
              </div>
            </article>
          ))}
        </div>
      </section>

      <section className="stack">
        <div className="section-heading">
          <p className="eyebrow">History</p>
          <h2>Audit log</h2>
        </div>

        <div className="audit-list">
          {audit.map((item) => (
            <details className="audit-card" key={item.id}>
              <summary>
                <span className="audit-action">{item.action}</span>
                <strong>{item.entity_type}</strong>
                <span>{item.actor?.username ?? "system"}</span>
                <time>{dateLabel(item.created_at)}</time>
              </summary>
              <div className="audit-json-grid">
                <AuditJson title="Before" value={item.before_data} />
                <AuditJson title="After" value={item.after_data} />
              </div>
            </details>
          ))}
        </div>
      </section>
    </section>
  );
}

function AuditJson({
  title,
  value,
}: {
  title: string;
  value: Record<string, unknown> | null;
}) {
  return (
    <div>
      <span className="eyebrow">{title}</span>
      <pre>{value ? JSON.stringify(value, null, 2) : "—"}</pre>
    </div>
  );
}
