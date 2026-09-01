# WGDB V1 status

## Implemented

### Backend
- PostgreSQL/SQLAlchemy model (17 tables)
- Alembic initial migration
- UUIDv7 primary keys
- public movie list/detail API
- filtering/sorting/pagination
- manual create/update
- TMDB search/preview/import
- soft delete / admin restore / admin permanent delete
- canonical Movie snapshot + audit diff layer
- cookie JWT auth + CSRF
- admin-created accounts, roles and activation
- personal 0–100 rating, watched, favorite
- one review per user/movie
- admin review moderation
- shared reference-data create/edit for every authenticated user
- admin audit-log read API
- Excel dry-run/commit importer

### Frontend
- WGDB navbar/branding
- login/logout
- public movie table with small posters
- year/search filters, sorting, pagination
- movie detail page
- external/community scores
- white Brick rating component
- watched/favorite/personal rating controls
- reviews + spoiler handling
- TMDB Add Movie flow
- manual Add Movie flow including normalized relations
- Movie edit flow including relations and links
- shared Catalog manager
- Admin user creation/roles/activation
- recycle bin + restore/permanent delete
- audit viewer
- responsive CSS

## Verified in this workspace

- Python source `compileall`: pass
- SQLAlchemy metadata test: pass, expected 17 tables
- `pytest`: pass
- supplied `.xlsm` dry-run: 1300 movies parsed
- 94 legacy personal rows retained unassigned
- duplicate/suspicious rows surfaced as warnings/errors rather than silently fixed

### Deployment
- backend and frontend Containerfiles
- local Podman Compose stack
- production rootless Podman Quadlets
- dedicated Podman network and persistent PostgreSQL 18 volume
- host nginx HTTP/HTTPS reverse-proxy templates
- Certbot bootstrap + renewal reload hook
- explicit migration/update scripts
- daily pg_dump systemd user timer
- checksum-backed restore helper
- production preflight/security/Oracle VM checklists

## Verified in the deployment layer

- all deployment shell scripts pass `bash -n`
- Compose YAML parses successfully
- both nginx HTTP and HTTPS templates pass `nginx -t` after rendering
- production Pydantic environment shape parses
- no generated production secret is committed

## Still requires the actual Oracle VM / external services

- install Podman/nginx/Certbot on the chosen VM OS
- provide the real domain/DNS and Certbot email
- provide production DB/JWT/TMDB secrets
- build the frontend with npm-registry access
- run the Quadlets against real PostgreSQL storage
- perform the Excel commit import only after reviewing dry-run warnings/overrides
- run the final end-to-end browser test over HTTPS
- configure an off-VM backup destination
