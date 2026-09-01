# White Gold Database (WGDB) Frontend

React + Vite + React Router client for the FastAPI/PostgreSQL movie database.

## Included

- public Movie table
- pagination
- title/year filtering
- sorting
- movie detail page
- external scores
- community score
- white `Bricks` rating visualization
- Cookie/CSRF authentication integration
- login/logout
- personal 0–100 score
- watched/favorite state
- public reviews
- create/delete own review
- admin review moderation delete
- TMDB search + one-click import
- manual Movie creation
- protected/admin route layout
- responsive styling

## Install

```bash
npm install
cp .env.example .env
npm run dev
```

Backend dev default expected by `.env.example`:

```text
http://localhost:8000/api
```

## Cookie + CSRF

Every request uses:

```ts
credentials: "include"
```

For state-changing requests `src/lib/api.ts` reads the non-HttpOnly
`csrf_token` cookie and sends:

```http
X-CSRF-Token: ...
```

The JWT itself remains HttpOnly and is never exposed to React.

## Bricks

The database/API retains the exact 0–100 score.

Only the UI maps it to nearest half Brick:

```ts
Math.round((rating / 20) * 2) / 2
```

`BrickRating` renders five small white parcel-shaped bricks using CSS, so no
image assets are required.

## Backend pieces still needed for the currently-placeholder UI

The agreed backend design supports these, but the snippets built so far did
not yet expose all read endpoints:

- `GET /api/movies/deleted`
- user listing/update endpoints for the Admin table
- audit log read endpoint
- lookup endpoints for Genre/Country/Language/Studio/Person
- Movie edit form route/component

The Manual Add page therefore currently handles the scalar Movie fields and
creates empty relation lists. TMDB import already fills relation data.

## Important backend response detail

Manual `POST /api/movies` should return a Movie response (or at minimum an
object containing `id`). The frontend only relies on `id` after creation.

## Production

Recommended topology on the Oracle VM:

```text
HTTPS
  |
reverse proxy (Caddy/nginx)
  |-- /       -> built React static files
  `-- /api/*  -> FastAPI/Uvicorn
                   |
                PostgreSQL
```

Serving frontend and API under the same HTTPS site simplifies cookie auth and
removes most production CORS complexity.

Build:

```bash
npm run build
```

Static files are emitted to:

```text
dist/
```

React Router is configured as a browser SPA, so the reverse proxy/static
server must fall back unknown frontend paths such as `/movies/<uuid>` to
`index.html`.


## V1.1 additions

When the `movie_backend_frontend_support` package is merged into FastAPI:

- `/admin` becomes a working users + recycle-bin + audit page.
- `/movies/:id/edit` edits scalar Movie metadata and generic links.
- Admin can change user role/active state.
- Admin can restore and permanently delete soft-deleted movies.

Creation/editing of shared reference entities (new Genre, Country, Language,
Studio, Person) remains intentionally unresolved because that permission rule
has not been agreed yet.
