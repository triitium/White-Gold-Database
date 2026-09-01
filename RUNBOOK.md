# WGDB local end-to-end runbook

## 1. PostgreSQL

Create a database/user matching your `.env`, e.g.:

```sql
CREATE USER wgdb_app WITH PASSWORD 'change-me';
CREATE DATABASE wgdb OWNER wgdb_app;
```

## 2. Backend

```bash
cd backend
python3.14 -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
cp .env.example .env
```

Generate a secret:

```bash
openssl rand -hex 32
```

Put that and the TMDB API Read Access Token into `.env`.

For local plain HTTP keep:

```dotenv
COOKIE_SECURE=false
```

Then:

```bash
alembic upgrade head
python -m app.cli.create_admin
uvicorn app.main:app --reload --port 8000
```

Check:

```text
http://localhost:8000/health
http://localhost:8000/docs
```

## 3. Excel seed dry-run

```bash
python scripts/import_excel.py /path/to/FILME-V1.1.xlsm --report-dir import_report
```

Inspect at least:

```text
import_report/summary.json
import_report/warnings.csv
import_report/personal_pending.csv
```

Do not assign `personal_pending.csv` to an account until its owner is explicitly known.

## 4. Optional seed commit

Resolve/accept duplicate warnings first, then use explicit overrides if necessary.

```bash
python scripts/import_excel.py /path/to/FILME-V1.1.xlsm \
  --overrides /path/to/import_overrides.json \
  --commit
```

## 5. Frontend

```bash
cd ../frontend
npm install
cp .env.example .env
npm run dev
```

Open the Vite URL (normally `http://localhost:5173`).

## 6. Smoke-test flow

1. Public movie list opens without login.
2. Login with bootstrap admin.
3. Create a normal user in Admin.
4. Search/import a film via TMDB.
5. Create a manual film with genre/country/language/studio/person relations.
6. Edit a film and verify Admin audit history.
7. Rate it, mark watched/favorite, write a review.
8. Soft-delete a test film as user.
9. Restore it as admin.
10. Soft-delete again and permanently delete as admin.

## 7. Containerized local integration

Alternatively, run the complete local stack with Podman Compose:

```bash
cp deployment/local/.env.example deployment/local/.env
podman compose --env-file deployment/local/.env up --build -d
podman compose --env-file deployment/local/.env exec backend alembic upgrade head
```

Then open `http://localhost:8080`.

## 8. Production

Production is now specified as rootless Podman + Quadlet/systemd behind host nginx + Certbot. Continue with:

```text
deployment/README.md
deployment/ORACLE_VM.md
deployment/SECURITY.md
```
