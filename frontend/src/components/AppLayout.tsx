import { Link, NavLink, Outlet } from "react-router";

import { useAuth } from "../auth/AuthContext";

export function AppLayout() {
  const { user, logout } = useAuth();

  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="topbar__inner">
          <Link to="/" className="brand">
            <span className="brand__mark">WG</span>
            <span>White Gold Database</span>
          </Link>

          <nav className="main-nav">
            <NavLink to="/movies">Movies</NavLink>
            {user && <NavLink to="/movies/add">Add movie</NavLink>}
            {user && <NavLink to="/catalog">Catalog</NavLink>}
            {user?.role === "admin" && (
              <NavLink to="/admin">Admin</NavLink>
            )}
          </nav>

          <div className="topbar__user">
            {user ? (
              <>
                <span className="user-chip">
                  {user.username}
                  {user.role === "admin" && (
                    <span className="role-badge">admin</span>
                  )}
                </span>
                <button
                  className="button button--ghost button--small"
                  onClick={() => void logout()}
                >
                  Log out
                </button>
              </>
            ) : (
              <Link className="button button--small" to="/login">
                Log in
              </Link>
            )}
          </div>
        </div>
      </header>

      <main className="page-shell">
        <Outlet />
      </main>

      <footer className="site-footer">
        <div className="site-footer__inner">
          <span>White Gold Database</span>

          <div className="tmdb-attribution">
            <a
              href="https://www.themoviedb.org/"
              target="_blank"
              rel="noreferrer"
              aria-label="The Movie Database"
            >
              <img
                src="/tmdb-logo.svg"
                alt="TMDB"
                className="tmdb-attribution__logo"
              />
            </a>

            <span>
              This product uses the TMDB API but is not endorsed or certified
              by TMDB.
            </span>
          </div>
        </div>
      </footer>
    </div>
  );
}
