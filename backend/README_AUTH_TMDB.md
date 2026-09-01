# Cookie auth + CSRF + TMDB integration

## Dependencies

Add at least:

```bash
pip install "pwdlib[argon2]" PyJWT httpx email-validator
```

The project already expects FastAPI, SQLAlchemy async, psycopg, Alembic and
pydantic-settings.

## Cookie auth

- `access_token`: JWT, `HttpOnly`, `Secure` in production.
- `csrf_token`: random double-submit token, readable by React.
- All state-changing protected calls must send:

```http
X-CSRF-Token: <value of csrf_token cookie>
```

React fetches must include credentials when frontend/backend are on different
origins in development:

```ts
fetch("http://localhost:8000/api/movies", {
  credentials: "include",
})
```

For writes:

```ts
fetch("http://localhost:8000/api/movies/...", {
  method: "PATCH",
  credentials: "include",
  headers: {
    "Content-Type": "application/json",
    "X-CSRF-Token": readCookie("csrf_token"),
  },
  body: JSON.stringify(payload),
})
```

In production, prefer serving frontend and `/api` under the same site/domain.
Keep `COOKIE_SECURE=true` behind HTTPS.

## Login lifecycle

- `POST /api/auth/login` sets both cookies.
- `GET /api/auth/me` reads the HttpOnly JWT cookie.
- `POST /api/auth/logout` requires authentication + CSRF and deletes both.

## Apply CSRF to all writes

Add `_csrf: CsrfProtected` to every authenticated `POST`, `PATCH` and `DELETE`
route, including Movie create/update/delete/restore/permanent-delete and admin
mutations.

GET/HEAD routes should remain side-effect free and do not need CSRF.

## TMDB

TMDB application authentication uses the API Read Access Token as a Bearer
token. The server holds it; React never receives it.

Endpoints:

```text
GET  /api/tmdb/search?q=The%20Raid
GET  /api/tmdb/movies/{tmdb_id}/preview
POST /api/tmdb/movies/{tmdb_id}/import
```

The import endpoint upserts reference entities by stable TMDB/ISO identifiers
and creates our own local Movie UUID.

The code intentionally does not overwrite an existing or soft-deleted movie
with the same TMDB ID.

## Important integration TODO

`POST /tmdb/.../import` has one intentional TODO: insert your `AuditLog`
CREATE snapshot before the transaction commit. This should use the same
snapshot/audit helper as manual Movie creation so both paths are identical
from the audit system's point of view.
