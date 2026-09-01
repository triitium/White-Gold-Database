# User Movie State + Reviews

## Personal movie state

Stored in `UserMovie`:

```text
rating    0..100 | NULL
watched   bool
favorite  bool
```

Routes:

```text
GET    /api/movies/{movie_id}/me
PATCH  /api/movies/{movie_id}/me
DELETE /api/movies/{movie_id}/me
```

Examples:

```json
PATCH /api/movies/{id}/me

{
  "rating": 87,
  "watched": true,
  "favorite": true
}
```

`rating=null` explicitly removes the rating.

The frontend converts `0..100` to the white-Brick UI:

```text
brick_value = round((rating / 20) * 2) / 2
```

The DB/API stays on the 0..100 scale.

## Reviews

One review per user per movie is already enforced by the database constraint.

Routes:

```text
GET    /api/movies/{movie_id}/reviews
POST   /api/movies/{movie_id}/reviews
PATCH  /api/movies/{movie_id}/reviews/{review_id}
DELETE /api/movies/{movie_id}/reviews/{review_id}
```

Normal users may only edit/delete their own review.

Admins additionally get:

```text
DELETE /api/admin/reviews/{review_id}
```

for moderation.

## Rating + review separation

A review does not store a second rating.

The API looks up the author's current `UserMovie.rating` and includes it in
`UserReviewRead`.

Therefore changing:

```text
87 -> 92
```

automatically changes the rating shown next to that user's review without
editing the review itself.

A review without a numeric rating remains valid.

## Public review listing

`GET /movies/{movie_id}/reviews` is public, matching the public-read model of
the site.

## CSRF

Every state-changing route uses `CsrfProtected`.

React must send:

```http
X-CSRF-Token: <csrf_token cookie>
```

with credentials enabled.

## Performance note

The initial review-list implementation fetches each review's rating separately.
For a small friend-run site this is fine for V1.

Before scaling the public review list heavily, replace it with one joined query
against `UserReview + User + UserMovie` to avoid N+1 queries. The API response
model does not need to change.

## Audit policy

This package intentionally does NOT write Movie audit records for personal
ratings/watched/favorite changes.

That follows the agreed domain split:

```text
shared Movie editorial data -> Movie AuditLog
personal social data        -> separate concern
```

Admin moderation of reviews can later get its own moderation/audit log if
desired.
