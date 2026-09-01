# WGDB backend

FastAPI/PostgreSQL backend for **White Gold Database (WGDB)**.

Implemented V1 areas:

- Cookie JWT auth + CSRF
- user/admin authorization
- public movie list/detail
- manual movie create/update
- soft delete, restore and permanent delete
- TMDB search/import
- personal rating/watched/favorite state
- reviews and admin review moderation
- shared reference-data lookup/create/edit for all authenticated users
- admin account management
- audit-log read API
- Excel seed importer

## Shared reference API

Authenticated users can read, create and edit:

```text
GET/POST   /api/catalog/genres
PATCH      /api/catalog/genres/{id}
GET/POST   /api/catalog/countries
PATCH      /api/catalog/countries/{id}
GET/POST   /api/catalog/languages
PATCH      /api/catalog/languages/{id}
GET/POST   /api/catalog/studios
PATCH      /api/catalog/studios/{id}
GET/POST   /api/catalog/people
PATCH      /api/catalog/people/{id}
```

Mutations are CSRF-protected and audited. V1 intentionally has no reference-data delete endpoint.

## Admin API

```text
POST  /api/admin/users
GET   /api/admin/users
PATCH /api/admin/users/{id}/role
PATCH /api/admin/users/{id}/active
GET   /api/admin/deleted-movies
GET   /api/admin/audit
DELETE /api/admin/reviews/{review_id}
```

Movie restore/permanent-delete remain under `/api/movies/{id}/...` with admin authorization.
