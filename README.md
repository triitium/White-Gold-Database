# White Gold Database (WGDB)

Collaborative film database with a public catalogue and invite/admin-created user accounts.

## Current V1 stack

- **Backend:** FastAPI, async SQLAlchemy 2.x, PostgreSQL, Alembic
- **Frontend:** React + TypeScript + Vite + React Router
- **Authentication:** Argon2 passwords, JWT in `HttpOnly` cookie, CSRF double-submit cookie
- **Metadata import:** TMDB search/import plus manual film creation
- **Legacy seed:** Excel `.xlsm` importer with dry-run reports and explicit override support

## Core behaviour

- Public users can browse films and reviews.
- Logged-in users can create/edit films and shared reference data.
- Logged-in users can rate films `0–100`, mark watched/favorite, and write one review per film.
- UI maps ratings to **0–5 Bricks** in half-Brick steps while retaining the exact `0–100` value.
- Movie deletion is soft-delete by default.
- Admins can restore or permanently delete already-soft-deleted films.
- Admins manage accounts/roles/activation and may remove reviews for moderation.
- Movie and shared-reference edits are audited.

## Shared reference data

All authenticated users may **create and edit**:

- people
- genres
- countries
- languages
- studios

There is intentionally no reference-data delete endpoint in V1.

## Repository layout

```text
wgdb/
  backend/
    app/
    alembic/
    scripts/
    tests/
  frontend/
    src/
  importer/
  deployment/
  compose.yaml
  Makefile
```

## Backend bootstrap

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
cp .env.example .env
```

Set at minimum in `.env`:

```dotenv
DATABASE_URL=postgresql+psycopg://movie_app:password@localhost:5432/wgdb
SECRET_KEY=<openssl rand -hex 32>
TMDB_READ_ACCESS_TOKEN=<TMDB API read token>
COOKIE_SECURE=false
```

Create/update the schema:

```bash
alembic upgrade head
```

Create the first administrator:

```bash
python -m app.cli.create_admin
```

Run development API:

```bash
uvicorn app.main:app --reload
```

Health check:

```text
GET /health
```

## Frontend bootstrap

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

The default development API is `http://localhost:8000/api`.

## Excel import

Dry-run first:

```bash
cd backend
python scripts/import_excel.py /path/to/FILME-V1.1.xlsm --report-dir import_report
```

Only after reviewing warnings/overrides:

```bash
python scripts/import_excel.py /path/to/FILME-V1.1.xlsm \
  --overrides /path/to/import_overrides.json \
  --commit
```

The current workbook dry-run parsed **1300 movie rows** and retained **94 personal rating/watched rows as unassigned pending data** rather than guessing their owner. Duplicate and suspicious metadata candidates are reported rather than silently corrected.

## Verification status

Backend source compiles and the SQLAlchemy metadata test registers the expected **17 tables**. The Excel importer has been exercised in dry-run mode against the supplied workbook.

A full browser production build still needs `npm install && npm run build` in an environment with npm-registry access.

## Podman deployment

The agreed production topology is now included in `deployment/`:

- rootless Podman for frontend, backend and PostgreSQL
- Quadlet/systemd for production lifecycle
- host nginx for TCP 80/443 and reverse proxying
- Certbot for TLS
- explicit Alembic migration script
- persistent PostgreSQL volume
- daily `pg_dump` backup timer + interactive restore helper
- local `podman compose` integration stack

See `deployment/README.md` and `deployment/ORACLE_VM.md`.
