# Manual Movie write path

Adds complete manual create/update logic on top of the existing snapshot/audit layer.

## PATCH semantics

- omitted scalar: unchanged
- scalar explicitly null: set NULL
- omitted relation: unchanged
- relation `[]`: clear all
- relation `[...ids...]`: replace complete relation set

## Atomicity

The service never commits. Route layer commits once after Movie changes + relationships + AuditLog.

## Validation

Genre/Country/Language/Studio/Person UUIDs are checked before relationship replacement. Duplicate IDs are rejected early.

## Route pattern

```python
try:
    movie = await movie_manual.update_movie(...)
    await session.commit()
except Exception:
    await session.rollback()
    raise
```

Map `MovieReferenceError` to HTTP 422 and `IntegrityError` to HTTP 409. Keep `CsrfProtected` on all write routes.
