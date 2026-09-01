# Central Movie Audit / Snapshot Layer

This package completes the audit TODO from the Cookie Auth + TMDB package.

## Modules

- `app/services/movie_snapshot.py`
  - canonical, JSON-safe Movie snapshot
  - includes genres, countries, languages, studios, credits, links and external ratings

- `app/services/audit.py`
  - append-only AuditLog creator
  - top-level snapshot diffing

- `app/services/movie_loader.py`
  - canonical eager-loading graph for Movie
  - avoids implicit lazy I/O with AsyncSession

- `app/services/movie_mutations.py`
  - shared update finalization
  - soft delete
  - restore
  - permanent delete

- `app/services/tmdb_import.py`
  - TMDB import now writes CREATE audit in the SAME transaction

## Transaction rule

Service functions add/flush changes and audit records but generally DO NOT
commit.

The route or upper application transaction boundary commits once:

```python
try:
    movie = await service.do_something(...)
    await session.commit()
except Exception:
    await session.rollback()
    raise
```

This makes:

```text
Movie changes
+ relationship changes
+ AuditLog
```

atomic.

## Manual create

After the Movie and all relationships have been created:

```python
await session.flush()

movie = await reload_movie_full(
    session,
    movie.id,
    include_deleted=True,
)

snapshot = movie_snapshot(movie)

await log_audit(
    session,
    actor_user_id=current_user.id,
    action=AUDIT_CREATE,
    entity_type="movie",
    entity_id=movie.id,
    before_data=None,
    after_data=snapshot,
    reduce_to_diff=False,
)
```

Then commit once.

## Manual update

Before changing anything:

```python
before = await snapshot_before_change(session, movie)
```

Apply scalar fields and replace requested association lists, then:

```python
movie = await finish_movie_update(
    session,
    movie_id=movie.id,
    actor_user_id=current_user.id,
    before_snapshot=before,
)
await session.commit()
```

The resulting AuditLog stores only changed top-level fields.

For example:

```json
before_data = {
  "title": "Raid",
  "genres": ["Action"]
}

after_data = {
  "title": "The Raid",
  "genres": ["Action", "Thriller"]
}
```

## Soft delete

```python
movie = await soft_delete_movie(
    session,
    movie=movie,
    actor_user_id=current_user.id,
)
await session.commit()
```

Audit diff normally contains only `deleted_at` / `deleted_by_id`.

## Restore

Admin-only:

```python
movie = await restore_movie(
    session,
    movie=movie,
    actor_user_id=admin.id,
)
await session.commit()
```

## Hard delete

Admin-only and only after a Movie has already been soft-deleted:

```python
await hard_delete_movie(
    session,
    movie=movie,
    actor_user_id=admin.id,
)
await session.commit()
```

The full BEFORE snapshot is retained even though the Movie and cascading
association rows disappear.

## Important snapshot convention

The Movie snapshot intentionally does NOT include `UserMovie` or `UserReview`.

Reason:

- Movie editorial/shared data and per-user social data are separate domains.
- A user changing their own rating should not create a giant Movie UPDATE audit.
- Reviews/ratings can get their own audit policy later if desired.

The snapshot DOES include shared Movie metadata:

- scalar Movie fields
- genres
- countries
- languages
- studios
- cast/crew
- links
- external ratings

## One caveat

The snapshot diff is intentionally top-level, not a recursive JSON patch.

For V1 this is more human-readable:

```text
genres before: [...]
genres after: [...]
```

rather than low-level list add/remove operations.

If the audit UI later needs field-level nested diffs, the snapshot format can
stay unchanged and only `diff_snapshots()` needs to become recursive.
