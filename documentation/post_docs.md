# Posts Module — Developer Guide

A complete reference for the post feed, CRUD operations, likes, comments, shares, and saves.

---

## Table of Contents

1. [Module Overview](#1-module-overview)
2. [Database Schema](#2-database-schema)
3. [File Structure](#3-file-structure)
4. [Auth & Identity](#4-auth--identity)
5. [Reference Data — Categories & Commodities](#5-reference-data--categories--commodities)
6. [API Quick Reference](#6-api-quick-reference)
7. [Shared Post Object](#7-shared-post-object)
8. [Post CRUD APIs](#8-post-crud-apis)
9. [Interaction APIs](#9-interaction-apis)
10. [Comment APIs](#10-comment-apis)
11. [Validation Rules](#11-validation-rules)
12. [Error Reference](#12-error-reference)
13. [Frontend Integration Guide](#13-frontend-integration-guide)

---

## 1. Module Overview

The posts module provides a full social-feed experience:

- **Post CRUD** — create, read, update, delete posts with category-specific fields
- **Feed** — paginated global feed of all posts, newest first
- **Likes** — toggle like/unlike, returns updated count
- **Comments** — add, list, and delete comments per post
- **Shares** — record a share event, increments share count
- **Saves** — toggle save/unsave; saved posts can be retrieved as a separate list
- **Views** — automatically recorded on `GET /posts/{post_id}`, once per profile per post (unique constraint)

All endpoints are mounted under `/posts`.

---

## 2. Database Schema

### `post_categories` — seeded, fixed IDs

```sql
CREATE TABLE post_categories (
    id    INTEGER PRIMARY KEY,  -- fixed: 1–5
    name  VARCHAR(100) UNIQUE
);
-- Seeded values: 1=Market Update, 2=Knowledge, 3=Discussion, 4=Deal/Requirement, 5=Other
```

### `posts`

```sql
CREATE TABLE posts (
    id                  SERIAL PRIMARY KEY,
    profile_id          INTEGER NOT NULL REFERENCES profile(id) ON DELETE CASCADE,
    category_id         INTEGER NOT NULL REFERENCES post_categories(id),
    commodity_id        INTEGER NOT NULL REFERENCES commodities(id),

    -- Content
    image_url           TEXT,
    caption             TEXT NOT NULL,

    -- Visibility
    is_public           BOOLEAN DEFAULT TRUE,
    target_roles        INTEGER[],             -- NULL = all roles

    -- Interaction controls
    allow_comments      BOOLEAN DEFAULT TRUE,

    -- Deal / Requirement fields (category_id = 4 only)
    grain_type_size     VARCHAR(100),
    commodity_quantity  FLOAT,
    price_type          VARCHAR(20),           -- 'fixed' | 'negotiable'

    -- Other category fields (category_id = 5 only)
    other_description   TEXT,

    -- Counters (denormalized for fast reads)
    like_count          INTEGER DEFAULT 0,
    view_count          INTEGER DEFAULT 0,
    comment_count       INTEGER DEFAULT 0,
    share_count         INTEGER DEFAULT 0,

    created_at          TIMESTAMPTZ DEFAULT NOW()
);
```

### `post_views` — unique per profile per post

```sql
CREATE TABLE post_views (
    id          SERIAL PRIMARY KEY,
    post_id     INTEGER NOT NULL REFERENCES posts(id) ON DELETE CASCADE,
    profile_id  INTEGER NOT NULL REFERENCES profile(id) ON DELETE CASCADE,
    viewed_at   TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (post_id, profile_id)
);
```

### `post_likes` — unique per profile per post

```sql
CREATE TABLE post_likes (
    id          SERIAL PRIMARY KEY,
    post_id     INTEGER NOT NULL REFERENCES posts(id) ON DELETE CASCADE,
    profile_id  INTEGER NOT NULL REFERENCES profile(id) ON DELETE CASCADE,
    liked_at    TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (post_id, profile_id)
);
```

### `post_comments`

```sql
CREATE TABLE post_comments (
    id          SERIAL PRIMARY KEY,
    post_id     INTEGER NOT NULL REFERENCES posts(id) ON DELETE CASCADE,
    profile_id  INTEGER NOT NULL REFERENCES profile(id) ON DELETE CASCADE,
    content     TEXT NOT NULL,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);
```

### `post_shares`

```sql
CREATE TABLE post_shares (
    id          SERIAL PRIMARY KEY,
    post_id     INTEGER NOT NULL REFERENCES posts(id) ON DELETE CASCADE,
    profile_id  INTEGER NOT NULL REFERENCES profile(id) ON DELETE CASCADE,
    shared_at   TIMESTAMPTZ DEFAULT NOW()
);
```

### `post_saves` — unique per profile per post

```sql
CREATE TABLE post_saves (
    id          SERIAL PRIMARY KEY,
    post_id     INTEGER NOT NULL REFERENCES posts(id) ON DELETE CASCADE,
    profile_id  INTEGER NOT NULL REFERENCES profile(id) ON DELETE CASCADE,
    saved_at    TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (post_id, profile_id)
);
```

---

## 3. File Structure

```
app/modules/post/
  models.py        ← SQLAlchemy ORM models (Post, PostLike, PostComment, …)
  schemas.py       ← Pydantic request / response schemas + validators
  service.py       ← Business logic, DB queries, custom exceptions
  router.py        ← FastAPI route definitions
  dependencies.py  ← get_current_profile_id — resolves JWT → profile row
```

`router.py` only handles HTTP concerns. All DB interaction lives in `service.py`. `dependencies.py` resolves the authenticated user's `profile_id` from the JWT via `get_current_user_id`.

---

## 4. Auth & Identity

All endpoints require a valid JWT. The `Authorization` header is read by `get_current_user_id`. The dependency chain is:

```
JWT → user_id → profile.id (profile_id)
```

`profile_id` is injected automatically via `Depends(get_current_profile_id)`. Endpoints never accept a `profile_id` in the request body or URL — it is always derived from the token.

If no profile exists for the authenticated user, all endpoints return `404 Profile not found for this user`.

---

## 5. Reference Data — Categories & Commodities

### Post Categories

| `category_id` | Name | Extra required fields |
|---|---|---|
| `1` | Market Update | — |
| `2` | Knowledge | — |
| `3` | Discussion | — |
| `4` | Deal / Requirement | `grain_type_size`, `commodity_quantity`, `price_type` |
| `5` | Other | `other_description` |

### Commodities

| `commodity_id` | Name |
|---|---|
| `1` | Rice |
| `2` | Cotton |
| `3` | Sugar |

### Target Roles

| Role ID | Role |
|---|---|
| `1` | Trader |
| `2` | Broker |
| `3` | Exporter |

`target_roles: null` means the post is visible to all roles.
`target_roles: [1, 3]` limits visibility to Traders and Exporters.

---

## 6. API Quick Reference

| Method | Endpoint | Description | Auth |
|---|---|---|---|
| `POST` | `/posts/` | Create a post | Required |
| `GET` | `/posts/` | Get global feed (paginated) | Required |
| `GET` | `/posts/mine` | Get my own posts | Required |
| `GET` | `/posts/saved` | Get my saved posts | Required |
| `GET` | `/posts/{post_id}` | Get single post (records view) | Required |
| `PATCH` | `/posts/{post_id}` | Update my post (partial) | Required |
| `DELETE` | `/posts/{post_id}` | Delete my post | Required |
| `POST` | `/posts/{post_id}/like` | Toggle like | Required |
| `POST` | `/posts/{post_id}/share` | Record a share | Required |
| `POST` | `/posts/{post_id}/save` | Toggle save | Required |
| `GET` | `/posts/{post_id}/comments` | Get comments (paginated) | Required |
| `POST` | `/posts/{post_id}/comments` | Add a comment | Required |
| `DELETE` | `/posts/{post_id}/comments/{comment_id}` | Delete my comment | Required |

---

## 7. Shared Post Object

Every endpoint that returns a post returns this shape:

```json
{
  "id": 1,
  "profile_id": 42,
  "category_id": 4,
  "commodity_id": 1,
  "caption": "Looking to buy 500 bags of long grain rice",
  "image_url": "https://example.com/photo.jpg",
  "is_public": true,
  "target_roles": null,
  "allow_comments": true,
  "grain_type_size": "Long grain, 25kg bags",
  "commodity_quantity": 500.0,
  "price_type": "negotiable",
  "other_description": null,
  "view_count": 12,
  "like_count": 4,
  "comment_count": 2,
  "share_count": 1,
  "is_liked": false,
  "is_saved": true,
  "created_at": "2026-04-16T10:00:00"
}
```

**Field notes:**

| Field | Notes |
|---|---|
| `grain_type_size`, `commodity_quantity`, `price_type` | Non-null only for `category_id = 4` |
| `other_description` | Non-null only for `category_id = 5` |
| `is_liked` | `true` if the requesting profile has liked this post |
| `is_saved` | `true` if the requesting profile has saved this post |
| `view_count` | Each profile is counted at most once per post |
| `created_at` | UTC datetime string |

All list responses (`GET /posts/`, `GET /posts/mine`, `GET /posts/saved`) return an array of this object.

---

## 8. Post CRUD APIs

### `POST /posts/`

Create a new post.

**Request body — categories 1, 2, 3 (Market Update / Knowledge / Discussion):**

```json
{
  "category_id": 1,
  "commodity_id": 2,
  "caption": "Cotton prices rose 10% this week in Maharashtra markets",
  "is_public": true,
  "target_roles": null,
  "allow_comments": true,
  "image_url": "https://example.com/chart.jpg"
}
```

**Request body — category 4 (Deal / Requirement):**

`grain_type_size`, `commodity_quantity`, and `price_type` are **required** when `category_id` is `4`.

```json
{
  "category_id": 4,
  "commodity_id": 1,
  "caption": "Looking to buy 500 bags of long grain rice — Nagpur delivery",
  "is_public": true,
  "target_roles": [1, 2],
  "allow_comments": true,
  "image_url": null,
  "grain_type_size": "Long grain, 25kg bags",
  "commodity_quantity": 500.0,
  "price_type": "negotiable"
}
```

**Request body — category 5 (Other):**

`other_description` is **required** when `category_id` is `5`.

```json
{
  "category_id": 5,
  "commodity_id": 3,
  "caption": "Announcement for our network",
  "is_public": false,
  "target_roles": [3],
  "allow_comments": false,
  "image_url": null,
  "other_description": "We have shifted our warehouse to a new location in Pune."
}
```

**Request body fields:**

| Field | Type | Required | Default | Notes |
|---|---|---|---|---|
| `category_id` | int | Yes | — | 1–5 |
| `commodity_id` | int | Yes | — | 1–3 |
| `caption` | string | Yes | — | Cannot be empty or whitespace |
| `is_public` | bool | No | `true` | `false` = followers only |
| `target_roles` | int[] or null | No | `null` | `null` = all roles; `[1,2,3]` = specific |
| `allow_comments` | bool | No | `true` | — |
| `image_url` | string or null | No | `null` | — |
| `grain_type_size` | string | Conditional | `null` | Required if `category_id = 4` |
| `commodity_quantity` | float | Conditional | `null` | Required if `category_id = 4` |
| `price_type` | string | Conditional | `null` | Required if `category_id = 4`; must be `"fixed"` or `"negotiable"` |
| `other_description` | string | Conditional | `null` | Required if `category_id = 5` |

**Response `201`:**

```json
{
  "status": "ok",
  "message": "Post created successfully",
  "data": { /* Post Object */ }
}
```

---

### `GET /posts/`

Paginated global feed. All posts from all active profiles, newest first.

**Query parameters:**

| Param | Type | Default | Description |
|---|---|---|---|
| `limit` | int | `20` | Max posts to return |
| `offset` | int | `0` | Number of posts to skip |

**Example:**
```
GET /posts/?limit=10&offset=0
GET /posts/?limit=10&offset=10
```

**Response `200`:**

```json
{
  "status": "ok",
  "message": "Feed fetched successfully",
  "data": [
    { /* Post Object */ },
    { /* Post Object */ }
  ]
}
```

---

### `GET /posts/mine`

Posts created by the authenticated profile, newest first.

**Query parameters:** Same as feed — `limit` (default `20`), `offset` (default `0`).

**Response `200`:**

```json
{
  "status": "ok",
  "message": "Posts fetched successfully",
  "data": [ /* array of Post Objects */ ]
}
```

---

### `GET /posts/saved`

Posts the authenticated profile has saved, ordered by save time descending (most recently saved first). Only returns posts whose author is still an active profile.

**Query parameters:** `limit` (default `20`), `offset` (default `0`).

**Response `200`:**

```json
{
  "status": "ok",
  "message": "Saved posts fetched successfully",
  "data": [ /* array of Post Objects */ ]
}
```

---

### `GET /posts/{post_id}`

Fetch a single post. Also records a view for the requesting profile (each profile is counted at most once — duplicate views are silently ignored).

**Response `200`:**

```json
{
  "status": "ok",
  "message": "Post fetched successfully",
  "data": { /* Post Object */ }
}
```

**Errors:**

| Code | Reason |
|---|---|
| `404` | Post does not exist or author's profile is inactive |

---

### `PATCH /posts/{post_id}`

Partially update a post. Only the post's author can update it. Send only the fields you want to change — all fields are optional.

**Request body:**

```json
{
  "caption": "Updated: Cotton prices stabilized after initial spike",
  "image_url": "https://example.com/updated-chart.jpg",
  "is_public": false,
  "target_roles": [1, 2],
  "allow_comments": false,
  "grain_type_size": "Medium grain, 50kg bags",
  "commodity_quantity": 300.0,
  "price_type": "fixed",
  "other_description": "Updated description text"
}
```

> Send only the fields you want to change. Fields omitted from the body are not modified.

**Response `200`:**

```json
{
  "status": "ok",
  "message": "Post updated successfully",
  "data": { /* updated Post Object */ }
}
```

**Errors:**

| Code | Reason |
|---|---|
| `404` | Post not found |
| `403` | Attempting to edit someone else's post |

---

### `DELETE /posts/{post_id}`

Delete a post. Only the post's author can delete it. Cascades to all views, likes, comments, shares, and saves for that post.

**Response `204`:** No body.

**Errors:**

| Code | Reason |
|---|---|
| `404` | Post not found |
| `403` | Attempting to delete someone else's post |

---

## 9. Interaction APIs

### `POST /posts/{post_id}/like`

Toggle like on a post. Calling it once likes the post; calling it again unlikes it.

**Request body:** None.

**Response `200` — after liking:**

```json
{
  "status": "ok",
  "message": "Like toggled",
  "data": {
    "liked": true,
    "like_count": 5
  }
}
```

**Response `200` — after unliking:**

```json
{
  "status": "ok",
  "message": "Like toggled",
  "data": {
    "liked": false,
    "like_count": 4
  }
}
```

**Errors:**

| Code | Reason |
|---|---|
| `404` | Post not found |

---

### `POST /posts/{post_id}/share`

Record a share event for a post. Each call increments `share_count` by 1 — this is **not idempotent**. Multiple calls from the same profile each count as a separate share.

**Request body:** None.

**Response `200`:**

```json
{
  "status": "ok",
  "message": "Share recorded",
  "data": {
    "share_count": 3
  }
}
```

**Errors:**

| Code | Reason |
|---|---|
| `404` | Post not found |

---

### `POST /posts/{post_id}/save`

Toggle save on a post. Calling it once saves the post; calling it again removes it from saved posts.

**Request body:** None.

**Response `200` — after saving:**

```json
{
  "status": "ok",
  "message": "Save toggled",
  "data": {
    "saved": true
  }
}
```

**Response `200` — after unsaving:**

```json
{
  "status": "ok",
  "message": "Save toggled",
  "data": {
    "saved": false
  }
}
```

**Errors:**

| Code | Reason |
|---|---|
| `404` | Post not found |

---

## 10. Comment APIs

### `GET /posts/{post_id}/comments`

Get paginated comments for a post. Returned oldest-first (chronological order).

**Query parameters:**

| Param | Type | Default | Description |
|---|---|---|---|
| `limit` | int | `20` | Max comments to return |
| `offset` | int | `0` | Number of comments to skip |

**Response `200`:**

```json
{
  "status": "ok",
  "message": "Comments fetched successfully",
  "data": [
    {
      "id": 1,
      "post_id": 5,
      "profile_id": 42,
      "content": "Interested — what's your location?",
      "created_at": "2026-04-16T10:05:00"
    },
    {
      "id": 2,
      "post_id": 5,
      "profile_id": 17,
      "content": "We can supply, DM me",
      "created_at": "2026-04-16T10:12:00"
    }
  ]
}
```

**Errors:**

| Code | Reason |
|---|---|
| `404` | Post not found |

---

### `POST /posts/{post_id}/comments`

Add a comment to a post.

**Request body:**

```json
{
  "content": "Great deal! What's the delivery timeline?"
}
```

| Field | Type | Required | Notes |
|---|---|---|---|
| `content` | string | Yes | Cannot be empty or whitespace |

**Response `201`:**

```json
{
  "status": "ok",
  "message": "Comment added successfully",
  "data": {
    "id": 3,
    "post_id": 5,
    "profile_id": 42,
    "content": "Great deal! What's the delivery timeline?",
    "created_at": "2026-04-16T10:20:00"
  }
}
```

**Errors:**

| Code | Reason |
|---|---|
| `404` | Post not found |
| `403` | Comments are disabled on this post (`allow_comments: false`) |

---

### `DELETE /posts/{post_id}/comments/{comment_id}`

Delete a comment. Only the comment's author can delete it.

**Response `204`:** No body.

**Errors:**

| Code | Reason |
|---|---|
| `404` | Comment not found on this post |
| `403` | Attempting to delete someone else's comment |

---

## 11. Validation Rules

### Caption

- Cannot be empty or consist only of whitespace.
- Leading/trailing whitespace is stripped automatically.

### `price_type`

- Must be exactly `"fixed"` or `"negotiable"` (case-sensitive).
- Any other value raises a `422`.

### Category 4 (Deal / Requirement)

All three fields below are required together when `category_id = 4`:

| Field | Validation |
|---|---|
| `grain_type_size` | Must be a non-empty string |
| `commodity_quantity` | Must be a positive float |
| `price_type` | Must be `"fixed"` or `"negotiable"` |

If any of these are missing, the response is `422` with detail listing the missing fields.

### Category 5 (Other)

`other_description` must be provided and non-empty when `category_id = 5`.

### PATCH (update) validation

Same `price_type` and `caption` validators apply to updates. Category-specific field requirements are **not re-validated** on PATCH — you can update individual deal fields without re-sending all three.

---

## 12. Error Reference

| Code | When |
|---|---|
| `201` | Post or comment created |
| `204` | Post or comment deleted (no body) |
| `400` | Bad request |
| `403` | Forbidden — editing/deleting someone else's post or comment; comments disabled |
| `404` | Post not found, comment not found, or profile not found for JWT user |
| `422` | Pydantic validation failed — missing required fields, wrong type, invalid `price_type`, empty caption/content |

All errors follow FastAPI's standard shape:

```json
{
  "detail": "Human-readable description of the error."
}
```

`422` errors return a list of validation issues:

```json
{
  "detail": [
    {
      "type": "value_error",
      "loc": ["body", "price_type"],
      "msg": "Value error, price_type must be one of: fixed, negotiable",
      "input": "cheap"
    }
  ]
}
```

---

## 13. Frontend Integration Guide

### General wrapper shape

Every successful response is wrapped by the `ok()` utility:

```json
{
  "status": "ok",
  "message": "...",
  "data": { ... }
}
```

Always read from `response.data` in your client code.

---

### Creating a Post

1. Determine `category_id` from the user's selection.
2. If `category_id = 4`, show the deal fields form (`grain_type_size`, `commodity_quantity`, `price_type`).
3. If `category_id = 5`, show the `other_description` textarea.
4. `POST /posts/` with the body. On `422`, surface the validation errors inline.

---

### Feed Pagination

Use `offset`-based pagination:

```
Page 1: GET /posts/?limit=20&offset=0
Page 2: GET /posts/?limit=20&offset=20
Page 3: GET /posts/?limit=20&offset=40
```

No cursor is needed — the feed is ordered by `created_at DESC`.

---

### Like Button State

The `is_liked` field on every PostResponse reflects whether the current user has liked the post. Use this to set the initial button state when rendering.

On click:
1. Call `POST /posts/{post_id}/like`.
2. Read `data.liked` and `data.like_count` from the response.
3. Update UI optimistically or from the response — both work since the response is synchronous.

---

### Save Button State

Same pattern as likes — use `is_saved` from the PostResponse to set initial state, then toggle via `POST /posts/{post_id}/save` and read `data.saved`.

---

### Share

Call `POST /posts/{post_id}/share` when the user completes a share action (after opening the native share sheet or copying the link). The response returns the new `share_count`.

---

### Comment Pagination

```
Page 1: GET /posts/{post_id}/comments?limit=20&offset=0
Load more: GET /posts/{post_id}/comments?limit=20&offset=20
```

Comments are ordered oldest-first — append new pages to the bottom.

After successfully adding a comment via `POST /posts/{post_id}/comments`, append the returned comment object to the local list and increment your local `comment_count` rather than re-fetching.

---

### Visibility & Targeting

| `is_public` | `target_roles` | Who sees it |
|---|---|---|
| `true` | `null` | Everyone |
| `true` | `[1, 2]` | Only Traders and Brokers |
| `false` | `null` | Followers only |
| `false` | `[3]` | Followers who are Exporters |

> Note: visibility filtering is currently not enforced server-side on the feed query — `is_public` and `target_roles` are stored and returned but feed results are not yet filtered by them. Plan your UI accordingly.

---

### Editing a Post

Only the post author (`profile_id` matches) should see the edit/delete controls. Use the `profile_id` field on the post object compared to the logged-in user's profile ID.

`PATCH` is partial — only send changed fields. You do not need to re-send the entire post.

---

### Deal / Requirement Post Card

When rendering a post with `category_id = 4`, show the deal-specific fields in the card:

| Field | Display label |
|---|---|
| `grain_type_size` | Grain / Size |
| `commodity_quantity` | Quantity |
| `price_type` | Price Type (`Fixed` / `Negotiable`) |

---

### View Count

Views are recorded automatically on `GET /posts/{post_id}`. No extra call needed from the frontend. Duplicate views from the same profile are silently ignored by the server.
