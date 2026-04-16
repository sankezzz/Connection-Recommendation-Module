# Connections Module — Developer Guide

A complete reference for the follow system, message requests, and user search.

---

## Table of Contents

1. [Module Overview](#1-module-overview)
2. [Database Schema](#2-database-schema)
3. [File Structure](#3-file-structure)
4. [API Quick Reference](#4-api-quick-reference)
5. [Follow APIs](#5-follow-apis)
6. [Message Request APIs](#6-message-request-apis)
7. [Search APIs](#7-search-apis)
8. [Shared User Object](#8-shared-user-object)
9. [Error Reference](#9-error-reference)
10. [Setup & Migration](#10-setup--migration)
11. [Auth Note](#11-auth-note)

---

## 1. Module Overview

The connections module handles three things:

- **Follow** — one-directional, no approval needed. All profiles are public. User A follows User B instantly with no confirmation step.
- **Message requests** — bidirectional, requires acceptance. User A sends a request, User B must accept or decline before messaging is unlocked.
- **Search** — text search across all users on the platform with optional filters. Includes fuzzy matching for typos via `pg_trgm`.

---

## 2. Database Schema

Two tables live in Supabase (Postgres).

### `user_connections` — follow relationships

```sql
CREATE TABLE user_connections (
    id           BIGSERIAL PRIMARY KEY,
    follower_id  INTEGER NOT NULL REFERENCES "Users"(user_id) ON DELETE CASCADE,
    following_id INTEGER NOT NULL REFERENCES "Users"(user_id) ON DELETE CASCADE,
    followed_at  TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE (follower_id, following_id),
    CHECK  (follower_id != following_id)
);
```

| Column | Description |
|---|---|
| `follower_id` | The user who pressed Follow |
| `following_id` | The user being followed |
| `followed_at` | Timestamp of the follow action |

One row = one follow relationship. User A follows User B → one row. User B follows User A back → a second separate row. There is no status column — a row existing means they are following, no row means they are not.

### `message_requests` — message request lifecycle

```sql
CREATE TABLE message_requests (
    id          BIGSERIAL PRIMARY KEY,
    sender_id   INTEGER NOT NULL REFERENCES "Users"(user_id) ON DELETE CASCADE,
    receiver_id INTEGER NOT NULL REFERENCES "Users"(user_id) ON DELETE CASCADE,
    status      VARCHAR(20) DEFAULT 'pending'
                CHECK (status IN ('pending', 'accepted', 'declined')),
    sent_at     TIMESTAMPTZ DEFAULT NOW(),
    acted_at    TIMESTAMPTZ,

    UNIQUE (sender_id, receiver_id),
    CHECK  (sender_id != receiver_id)
);
```

| Column | Description |
|---|---|
| `sender_id` | User who sent the request |
| `receiver_id` | User who needs to accept or decline |
| `status` | `pending` → `accepted` or `declined` |
| `sent_at` | When the request was sent |
| `acted_at` | When it was accepted or declined — `NULL` while pending |

### Indexes

```sql
CREATE INDEX idx_uc_follower        ON user_connections(follower_id);
CREATE INDEX idx_uc_following       ON user_connections(following_id);
CREATE INDEX idx_mr_sender          ON message_requests(sender_id);
CREATE INDEX idx_mr_receiver        ON message_requests(receiver_id, status);

-- Trigram indexes on Users table for fuzzy search
CREATE INDEX idx_users_city_trgm      ON "Users" USING GIN (city gin_trgm_ops);
CREATE INDEX idx_users_commodity_trgm ON "Users" USING GIN (commodity gin_trgm_ops);
CREATE INDEX idx_users_role_trgm      ON "Users" USING GIN (role gin_trgm_ops);
```

---

## 3. File Structure

```
app/
  routes/
    connections.py      ← FastAPI router — URL definitions, request parsing
  db/
    connections.py      ← All SQL queries, returns plain dicts
migrate_connections.py  ← Run once to create tables and indexes
```

`app/routes/connections.py` defines the router with prefix `/connections`. It only handles HTTP input/output and delegates everything to `app/db/connections.py` which contains all SQL.

---

## 4. API Quick Reference

| Method | Endpoint | What it does |
|---|---|---|
| `POST` | `/connections/follow/{user_id}` | Follow a user |
| `DELETE` | `/connections/follow/{user_id}` | Unfollow a user |
| `GET` | `/connections/followers/{user_id}` | List everyone who follows this user |
| `GET` | `/connections/following/{user_id}` | List everyone this user follows |
| `GET` | `/connections/follow/status/{user_id}` | Check if I am following this user |
| `POST` | `/connections/message-request/{user_id}` | Send a message request |
| `DELETE` | `/connections/message-request/{user_id}` | Withdraw a pending message request |
| `PATCH` | `/connections/message-request/{request_id}/accept` | Accept a message request |
| `PATCH` | `/connections/message-request/{request_id}/decline` | Decline a message request |
| `GET` | `/connections/message-requests/received` | My pending inbox |
| `GET` | `/connections/message-requests/sent` | Requests I have sent |
| `GET` | `/connections/search` | Search users with filters |
| `GET` | `/connections/search/suggestions` | Fuzzy "did you mean?" suggestions |

---

## 5. Follow APIs

### `POST /connections/follow/{user_id}`

Follow a user. Instant — no approval required.

**URL parameter:**

| Param | Type | Description |
|---|---|---|
| `user_id` | int | The user you want to follow |

**Request body (JSON):**
```json
{
    "me": 1
}
```

**Example:**
```
POST /connections/follow/2
Body: { "me": 1 }
```

**Success `200`:**
```json
{
    "status": "following",
    "following_id": 2
}
```

**Error `409`** — already following:
```json
{
    "detail": "Already following this user."
}
```

---

### `DELETE /connections/follow/{user_id}`

Unfollow a user.

**URL parameter:**

| Param | Type | Description |
|---|---|---|
| `user_id` | int | The user to unfollow |

**Query parameter:**

| Param | Type | Description |
|---|---|---|
| `me` | int | The acting user's id |

**Example:**
```
DELETE /connections/follow/2?me=1
```

**Success `200`:**
```json
{
    "status": "unfollowed",
    "following_id": 2
}
```

**Error `404`** — not currently following this user:
```json
{
    "detail": "You are not following this user."
}
```

---

### `GET /connections/followers/{user_id}`

Get a list of everyone who follows this user.

**URL parameter:**

| Param | Type | Description |
|---|---|---|
| `user_id` | int | The user whose followers to fetch |

**Example:**
```
GET /connections/followers/2
```

**Success `200`:**
```json
{
    "user_id": 2,
    "total": 1,
    "followers": [
        {
            "user_id": 1,
            "role": "trader",
            "commodity": "rice; cotton",
            "city": "Nagpur",
            "state": "Maharashtra",
            "qty_range": "100–500mt",
            "followed_at": "2026-04-15T08:19:31.248438+00:00"
        }
    ]
}
```

Results are ordered by `followed_at DESC` — most recent follower first.

---

### `GET /connections/following/{user_id}`

Get a list of everyone this user follows.

**URL parameter:**

| Param | Type | Description |
|---|---|---|
| `user_id` | int | The user whose following list to fetch |

**Example:**
```
GET /connections/following/1
```

**Success `200`:**
```json
{
    "user_id": 1,
    "total": 2,
    "following": [
        {
            "user_id": 7,
            "role": "exporter",
            "commodity": "sugar",
            "city": "Pune",
            "state": "Maharashtra",
            "qty_range": "500–2000mt",
            "followed_at": "2026-04-15T08:19:54.649203+00:00"
        },
        {
            "user_id": 2,
            "role": "broker",
            "commodity": "rice",
            "city": "Mumbai",
            "state": "Maharashtra",
            "qty_range": "200–800mt",
            "followed_at": "2026-04-15T08:19:31.248438+00:00"
        }
    ]
}
```

Results are ordered by `followed_at DESC` — most recently followed first.

---

### `GET /connections/follow/status/{user_id}`

Check whether the acting user (`me`) is currently following a specific user. Use this to drive the Follow / Unfollow button state when opening a profile.

**URL parameter:**

| Param | Type | Description |
|---|---|---|
| `user_id` | int | The user to check against |

**Query parameter:**

| Param | Type | Description |
|---|---|---|
| `me` | int | The acting user's id |

**Example:**
```
GET /connections/follow/status/2?me=1
```

**Success `200`:**
```json
{
    "me": 1,
    "target": 2,
    "following": true
}
```

`following` is always `true` or `false` — this endpoint never returns a 404.

---

## 6. Message Request APIs

### `POST /connections/message-request/{user_id}`

Send a message request to a user. Status is set to `pending` on creation.

**URL parameter:**

| Param | Type | Description |
|---|---|---|
| `user_id` | int | The user to send the request to |

**Request body (JSON):**
```json
{
    "me": 1
}
```

**Example:**
```
POST /connections/message-request/2
Body: { "me": 1 }
```

**Success `200`:**
```json
{
    "status": "sent",
    "id": 4,
    "sent_at": "2026-04-15T10:00:00.000000+00:00"
}
```

**Error `409`** — a request already exists between this pair (any status):
```json
{
    "detail": "Message request already sent."
}
```

---

### `DELETE /connections/message-request/{user_id}`

Withdraw a pending message request. Only works while status is `pending` — cannot withdraw a request that has already been accepted or declined.

**URL parameter:**

| Param | Type | Description |
|---|---|---|
| `user_id` | int | The user the request was sent to |

**Query parameter:**

| Param | Type | Description |
|---|---|---|
| `me` | int | The acting user's id (must be the original sender) |

**Example:**
```
DELETE /connections/message-request/2?me=1
```

**Success `200`:**
```json
{
    "status": "withdrawn",
    "receiver_id": 2
}
```

**Error `404`** — no pending request found (either doesn't exist or already accepted/declined):
```json
{
    "detail": "No pending request found to withdraw."
}
```

---

### `PATCH /connections/message-request/{request_id}/accept`

Accept a message request. Only the receiver can call this. Use the `request_id` from the received requests list.

**URL parameter:**

| Param | Type | Description |
|---|---|---|
| `request_id` | int | The `id` of the message request row (from received requests list) |

**Request body (JSON):**
```json
{
    "me": 2
}
```

`me` must match the `receiver_id` on the request — otherwise returns `404`.

**Example:**
```
PATCH /connections/message-request/4/accept
Body: { "me": 2 }
```

**Success `200`:**
```json
{
    "id": 4,
    "status": "accepted"
}
```

**Error `404`** — request not found, already acted on, or `me` is not the receiver:
```json
{
    "detail": "Request not found, already acted on, or you are not the receiver."
}
```

---

### `PATCH /connections/message-request/{request_id}/decline`

Decline a message request. Only the receiver can call this. Same rules as accept.

**URL parameter:**

| Param | Type | Description |
|---|---|---|
| `request_id` | int | The `id` of the message request row (from received requests list) |

**Request body (JSON):**
```json
{
    "me": 2
}
```

**Example:**
```
PATCH /connections/message-request/4/decline
Body: { "me": 2 }
```

**Success `200`:**
```json
{
    "id": 4,
    "status": "declined"
}
```

**Error `404`** — same conditions as accept.

---

### `GET /connections/message-requests/received`

Get all pending message requests waiting on me to accept or decline. Only returns `pending` status — accepted and declined are excluded.

**Query parameter:**

| Param | Type | Description |
|---|---|---|
| `me` | int | The acting user's id (the receiver) |

**Example:**
```
GET /connections/message-requests/received?me=2
```

**Success `200`:**
```json
{
    "me": 2,
    "total": 1,
    "requests": [
        {
            "request_id": 4,
            "from": {
                "user_id": 1,
                "role": "trader",
                "commodity": "rice; cotton",
                "city": "Nagpur",
                "state": "Maharashtra",
                "qty_range": "100–500mt"
            },
            "sent_at": "2026-04-15T10:00:00.000000+00:00"
        }
    ]
}
```

Use `request_id` from this response when calling the accept or decline endpoints.

---

### `GET /connections/message-requests/sent`

Get all message requests the acting user has sent, across all statuses.

**Query parameter:**

| Param | Type | Description |
|---|---|---|
| `me` | int | The acting user's id (the sender) |

**Example:**
```
GET /connections/message-requests/sent?me=1
```

**Success `200`:**
```json
{
    "me": 1,
    "total": 1,
    "requests": [
        {
            "request_id": 4,
            "to": {
                "user_id": 2,
                "role": "broker",
                "commodity": "rice",
                "city": "Mumbai",
                "state": "Maharashtra",
                "qty_range": "200–800mt"
            },
            "status": "pending",
            "sent_at": "2026-04-15T10:00:00.000000+00:00",
            "acted_at": null
        }
    ]
}
```

`acted_at` is `null` while pending. It is filled once the receiver accepts or declines.

---

## 7. Search APIs

### `GET /connections/search`

Search for users across the platform. The acting user is always excluded from results. All filter params are optional and stack with AND logic. Returns at most 50 results.

**Query parameters:**

| Param | Required | Type | Description |
|---|---|---|---|
| `me` | Yes | int | Acting user's id — excluded from results |
| `q` | No | string | Free text — case-insensitive partial match across city, state, commodity, role |
| `role` | No | string | Exact role match: `trader`, `broker`, or `exporter` |
| `commodity` | No | string | Partial case-insensitive match on commodity field |
| `city` | No | string | Partial case-insensitive match on city field |

`q` matches any substring using `ILIKE %q%`. `role` is exact. `commodity` and `city` are partial matches.

**Examples:**

Search by name fragment only:
```
GET /connections/search?me=1&q=abhishek
```

Filter by role and commodity:
```
GET /connections/search?me=1&role=exporter&commodity=rice
```

All filters combined:
```
GET /connections/search?me=1&q=pune&role=exporter&commodity=sugar&city=pune
```

No filters — returns all users except me (up to 50):
```
GET /connections/search?me=1
```

**Success `200`:**
```json
{
    "total": 2,
    "results": [
        {
            "user_id": 5,
            "role": "exporter",
            "commodity": "sugar",
            "city": "Pune",
            "state": "Maharashtra",
            "qty_range": "1000–5000mt"
        },
        {
            "user_id": 9,
            "role": "exporter",
            "commodity": "rice",
            "city": "Pune",
            "state": "Maharashtra",
            "qty_range": "200–1000mt"
        }
    ]
}
```

Results are ordered alphabetically by city.

---

### `GET /connections/search/suggestions`

Fuzzy "did you mean?" suggestions using trigram similarity (`pg_trgm`). Handles typos and partial spellings. Matches against city, commodity, and role fields. Returns the top 8 closest matches scored by similarity.

**Query parameter:**

| Param | Required | Type | Description |
|---|---|---|---|
| `q` | Yes | string | Search term — minimum 2 characters |

The similarity threshold is `0.15` — anything below this score is not returned. Score is the highest similarity value across city, commodity, and role for each user.

**Example — typo:**
```
GET /connections/search/suggestions?q=xpotar
```

**Success `200`:**
```json
{
    "q": "xpotar",
    "total": 2,
    "suggestions": [
        {
            "user_id": 5,
            "role": "exporter",
            "commodity": "sugar",
            "city": "Pune",
            "state": "Maharashtra",
            "qty_range": "1000–5000mt",
            "score": 0.364
        },
        {
            "user_id": 9,
            "role": "exporter",
            "commodity": "rice",
            "city": "Pune",
            "state": "Maharashtra",
            "qty_range": "200–1000mt",
            "score": 0.291
        }
    ]
}
```

`score` ranges from 0 to 1. Higher = closer match. Results are ordered by score descending.

---

## 8. Shared User Object

Every user profile object across all endpoints is produced by `_fmt_user()` in `app/db/connections.py` and always has this exact shape:

```json
{
    "user_id": 1,
    "role": "trader",
    "commodity": "rice; cotton",
    "city": "Nagpur",
    "state": "Maharashtra",
    "qty_range": "100–500mt"
}
```

`qty_range` is a formatted string: `"{min_quantity_mt}–{max_quantity_mt}mt"`. Raw integer values are not exposed in any response.

Some endpoints add extra fields alongside this object:

| Endpoint | Extra fields |
|---|---|
| `GET /followers/{user_id}` | `followed_at` |
| `GET /following/{user_id}` | `followed_at` |
| `GET /message-requests/received` | `sent_at` |
| `GET /message-requests/sent` | `status`, `sent_at`, `acted_at` |
| `GET /search/suggestions` | `score` |

---

## 9. Error Reference

| Status | When it happens |
|---|---|
| `404` | Not following, no pending request found, request already acted on, or wrong receiver on accept/decline |
| `409` | Already following, message request already exists |
| `422` | Missing required field or wrong data type (FastAPI validation) |

All errors follow FastAPI's default shape:
```json
{
    "detail": "Human-readable message describing what went wrong."
}
```

---

## 10. Setup & Migration

Run once after cloning or setting up a new environment:

```bash
python migrate_connections.py
```

What it does in order:
1. Enables the `pg_trgm` Postgres extension (required for fuzzy search)
2. Creates `user_connections` table
3. Creates `message_requests` table
4. Creates all follow and message request indexes
5. Creates GIN trigram indexes on `city`, `commodity`, and `role` columns of the `Users` table

Safe to re-run — all statements use `IF NOT EXISTS`. Does not touch or drop existing data.

Requires `DATABASE_URL` in `.env`:
```
DATABASE_URL=postgresql+asyncpg://user:password@host/dbname
```

The migration script strips the `+asyncpg` prefix internally before connecting via `asyncpg` directly.

---

## 11. Auth Note

All endpoints currently use a `me` parameter (in the request body or as a query param) to identify the acting user. This is a temporary stand-in until authentication is implemented.

Once auth is added, `me` is removed everywhere and replaced with the user id read from the JWT token:

```python
# Current — no auth
async def follow(user_id: int, body: ActorBody):
    return await db.follow_user(follower_id=body.me, following_id=user_id)

# After auth
async def follow(user_id: int, current_user: User = Depends(get_current_user)):
    return await db.follow_user(follower_id=current_user.id, following_id=user_id)
```

All URL structures and response shapes stay exactly the same — only the actor identification changes.