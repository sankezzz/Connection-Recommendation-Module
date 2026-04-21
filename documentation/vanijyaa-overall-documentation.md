# Vanijyaa — Frontend API Reference

**Base URL:** `https://vanijyaa-backend.onrender.com`  
**Swagger UI:** `https://vanijyaa-backend.onrender.com/docs`

---

## Critical Identity Rules

Two different IDs are used across the platform — never mix them up:

| ID | Type | Where you get it | Used for |
|----|------|-----------------|----------|
| `user_id` | UUID string | `POST /profile/user` response → `data.id` | Connections, News, Home Feed, Groups, Profile |
| `profile_id` | Integer | `POST /profile/` response → `data.profile.id` | Posts, Post Recommendation |

**Save both to local storage immediately after onboarding. Every API call uses one or the other.**

---

## Auth Rules

| Token | Required for | How long it lasts |
|-------|-------------|-------------------|
| `onboarding_token` | `POST /profile/user` and `POST /profile/` only | 15 minutes |

**After onboarding is complete — no token ever again.** All APIs use `user_id` or `profile_id` as query params or path params.

Onboarding token goes in the header as:
```
Authorization: Bearer <onboarding_token>
```

---

## Response Envelope

Every API response (except errors) follows this shape:
```json
{
  "success": true,
  "message": "...",
  "data": { ... }
}
```

Every error follows this shape:
```json
{
  "detail": "Human-readable message."
}
```

---

## Table of Contents

1. [Onboarding & Auth](#1-onboarding--auth)
2. [Profile](#2-profile)
3. [Connections](#3-connections)
4. [Posts](#4-posts)
5. [Post Recommendation Feed](#5-post-recommendation-feed)
6. [News](#6-news)
7. [Home Feed](#7-home-feed)
8. [Groups](#8-groups)
9. [User Recommendations](#9-user-recommendations)
10. [Reference Data](#10-reference-data)
11. [Global Error Reference](#11-global-error-reference)

---

## 1. Onboarding & Auth

### Step 1 — Firebase OTP (Client-side only — no backend call)

```dart
// Flutter
await FirebaseAuth.instance.verifyPhoneNumber(
  phoneNumber: '+919876543210',
  ...
);

final credential = PhoneAuthProvider.credential(
  verificationId: verificationId,
  smsCode: otpEnteredByUser,
);
final userCredential = await FirebaseAuth.instance.signInWithCredential(credential);
final idToken = await userCredential.user!.getIdToken();
// → send idToken to POST /auth/firebase-verify
```

---

### Step 2 — Verify Firebase Token with Backend

```
POST /auth/firebase-verify
Content-Type: application/json
```

**Request body:**
```json
{
  "firebase_id_token": "<id token from Firebase SDK>"
}
```

**Response — New user `200`:**
```json
{
  "success": true,
  "message": "OTP verified. Use the onboarding token to complete registration.",
  "data": {
    "is_new_user": true,
    "onboarding_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "user_id": null,
    "token_type": "bearer"
  }
}
```

**Response — Returning user `200`:**
```json
{
  "success": true,
  "message": "Welcome back.",
  "data": {
    "is_new_user": false,
    "onboarding_token": null,
    "user_id": "c37a3257-dc3f-43be-9fb0-33cf918b11ff",
    "token_type": "bearer"
  }
}
```

**Frontend logic:**
```
if data.is_new_user == true  → proceed to Steps 3, 4, 5 using data.onboarding_token
if data.is_new_user == false → skip onboarding — save data.user_id to local storage
```

**Errors:**

| Status | Reason |
|--------|--------|
| `401` | Invalid or expired Firebase token |

---

### Step 3 — Create User Row

```
POST /profile/user
Authorization: Bearer <onboarding_token>
```

No request body — phone and country code are read from the token.

**Response `201`:**
```json
{
  "success": true,
  "message": "User created successfully",
  "data": {
    "id": "c37a3257-dc3f-43be-9fb0-33cf918b11ff",
    "phone_number": "9876543210",
    "country_code": "+91",
    "created_at": "2026-04-16T10:00:00.000000"
  }
}
```

> ✅ **Save `data.id` immediately as `user_id`** — this UUID is used by most APIs.

**Errors:**

| Status | Reason |
|--------|--------|
| `409` | Phone number already registered |

---

### Step 4 — Create Profile

```
POST /profile/
Authorization: Bearer <onboarding_token>
Content-Type: application/json
```

**Request body:**
```json
{
  "name": "Ravi Traders",
  "role_id": 1,
  "commodities": [1, 2],
  "interests": [1, 2],
  "quantity_min": 100,
  "quantity_max": 500,
  "business_name": "Ravi Agro Pvt Ltd",
  "latitude": 19.076,
  "longitude": 72.877,
  "experience": 5
}
```

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `name` | string | Yes | Display name |
| `role_id` | int | Yes | 1 = Trader, 2 = Broker, 3 = Exporter |
| `commodities` | int[] | Yes | At least one. 1 = Rice, 2 = Cotton, 3 = Sugar |
| `interests` | int[] | Yes | At least one. 1 = Connections, 2 = Leads, 3 = News |
| `quantity_min` | float | Yes | Min trade quantity in MT |
| `quantity_max` | float | Yes | Must be ≥ `quantity_min` |
| `business_name` | string | No | Optional |
| `latitude` | float | Yes | Location latitude |
| `longitude` | float | Yes | Location longitude |
| `experience` | int | No | Years of experience |

**Response `200`:**
```json
{
  "success": true,
  "message": "Profile created successfully",
  "data": {
    "profile": {
      "id": 1,
      "name": "Ravi Traders",
      "role_id": 1,
      "commodities": [
        { "id": 1, "name": "rice" },
        { "id": 2, "name": "cotton" }
      ],
      "is_verified": false,
      "followers_count": 0,
      "business_name": "Ravi Agro Pvt Ltd",
      "latitude": 19.076,
      "longitude": 72.877,
      "experience": 5
    }
  }
}
```

> ✅ **Save `data.profile.id` immediately as `profile_id`** — this integer is used by Posts and Recommendation APIs.

**Errors:**

| Status | Reason |
|--------|--------|
| `409` | Profile already exists for this user |

---

### Step 5 — Register FCM Token (Push Notifications)

Call immediately after Step 4. Call again whenever the Firebase device token rotates.

```
PATCH /profile/user/fcm-token?user_id=<user_uuid>
Content-Type: application/json
```

**Request body:**
```json
{
  "fcm_token": "<firebase-device-token>"
}
```

**Response `200`:**
```json
{
  "success": true,
  "message": "FCM token updated",
  "data": null
}
```

---

### Complete Onboarding Flow Summary

```
NEW USER
────────
Firebase verifyPhoneNumber → user enters OTP → getIdToken()
POST /auth/firebase-verify                  → { is_new_user: true, onboarding_token }
POST /profile/user  ← onboarding_token      → save user_id (UUID)
POST /profile/      ← onboarding_token      → save profile_id (integer)
PATCH /profile/user/fcm-token?user_id=      → device registered

RETURNING USER
──────────────
Firebase verifyPhoneNumber → user enters OTP → getIdToken()
POST /auth/firebase-verify                  → { is_new_user: false, user_id }
                                               save user_id — skip all other steps
```

---

## 2. Profile

> **Auth:** No token required after onboarding. Pass `user_id` as query param.

---

### Get My Profile

```
GET /profile/me?user_id=<user_uuid>
```

**Response `200`:**
```json
{
  "success": true,
  "message": "Profile fetched successfully",
  "data": {
    "id": "a1b2c3d4-...",
    "name": "Ravi Traders",
    "role_id": "03b2851f-...",
    "commodities": [
      { "id": "3d3b18e1-...", "name": "cotton" }
    ],
    "is_verified": false,
    "is_user_verified": false,
    "is_business_verified": false,
    "followers_count": 0,
    "business_name": "Ravi Agro Pvt Ltd",
    "latitude": 19.076,
    "longitude": 72.877,
    "experience": 5
  }
}
```

---

### View Another User's Profile

```
GET /profile/{profile_id}?user_id=<acting_user_uuid>
```

| Param | Type | Description |
|-------|------|-------------|
| `profile_id` | int (path) | The target user's profile ID (integer) |
| `user_id` | UUID (query) | The logged-in user's UUID |

**Response `200`:**
```json
{
  "success": true,
  "message": "Profile fetched successfully",
  "data": {
    "id": "a1b2c3d4-...",
    "name": "Ravi Traders",
    "role_id": "03b2851f-...",
    "is_verified": false,
    "commodities": [
      { "id": "3d3b18e1-...", "name": "cotton" }
    ],
    "business_name": "Ravi Agro Pvt Ltd",
    "latitude": 19.076,
    "longitude": 72.877,
    "experience": 5,
    "posts_count": 0
  }
}
```

**Errors:**

| Status | Reason |
|--------|--------|
| `404` | Profile not found |
| `422` | Missing `user_id` or invalid format |

---

### Update My Profile

```
PATCH /profile/?user_id=<user_uuid>
Content-Type: application/json
```

All fields are optional — only send what you want to change.

**Request body:**
```json
{
  "name": "Ravi Global Traders",
  "commodities": [1, 3],
  "quantity_min": 200,
  "quantity_max": 1000,
  "business_name": "Ravi Agro International",
  "latitude": 18.520,
  "longitude": 73.856,
  "experience": 7
}
```

> **Commodity update:** Pass the complete new list. Items not in the list are removed. This is a full replace, not append.

**Response `200`:**
```json
{
  "success": true,
  "message": "Profile updated successfully",
  "data": { ... }
}
```

---

### Delete My Profile

```
DELETE /profile/?user_id=<user_uuid>
```

> ⚠️ Hard delete — not reversible.

**Response `200`:**
```json
{
  "success": true,
  "message": "Profile deleted successfully",
  "data": null
}
```

---

### Get My Posts (via Profile)

```
GET /profile/my-posts?user_id=<user_uuid>&limit=20&offset=0
```

| Param | Default | Description |
|-------|---------|-------------|
| `limit` | 20 | Max results |
| `offset` | 0 | Pagination offset |

---

### Get My Saved Posts (via Profile)

```
GET /profile/saved?user_id=<user_uuid>&limit=20&offset=0
```

Same pagination params as above.

---

## 3. Connections

> **Auth:** No token required. `user_id` is always in the URL path.

**Base prefix:** `/connections`

---

### Follow a User

```
POST /connections/{user_id}/follow/{target_id}
```

No request body.

**Response `200`:**
```json
{ "status": "following", "following_id": "a1b2c3d4-..." }
```

**Errors:**

| Status | Reason |
|--------|--------|
| `409` | Already following |

---

### Unfollow a User

```
DELETE /connections/{user_id}/follow/{target_id}
```

**Response `200`:**
```json
{ "status": "unfollowed", "following_id": "a1b2c3d4-..." }
```

**Errors:**

| Status | Reason |
|--------|--------|
| `404` | Not currently following this user |

---

### Get My Followers

```
GET /connections/{user_id}/followers
```

**Response `200`:**
```json
{
  "user_id": "c37a3257-...",
  "total": 1,
  "followers": [
    {
      "user_id": "a1b2c3d4-...",
      "name": "Ravi Traders",
      "business_name": "Ravi Agro",
      "role": "trader",
      "commodity": ["rice", "cotton"],
      "is_verified": false,
      "qty_range": "100–500mt",
      "followed_at": "2026-04-15T08:19:31.248438+00:00"
    }
  ]
}
```

Ordered by `followed_at DESC`.

---

### Get Who I Follow

```
GET /connections/{user_id}/following
```

Same response shape as followers — uses `"following"` array key instead of `"followers"`.

---

### Check Follow Status

Use this to drive the Follow / Unfollow button state.

```
GET /connections/{user_id}/follow/status/{target_id}
```

**Response `200`:**
```json
{ "me": "c37a3257-...", "target": "a1b2c3d4-...", "following": true }
```

> `following` is always `true` or `false` — never a 404.

---

### Send a Message Request

```
POST /connections/{user_id}/message-request/{target_id}
```

No request body.

**Response `200`:**
```json
{ "status": "sent", "id": 4, "sent_at": "2026-04-15T10:00:00.000000+00:00" }
```

**Errors:**

| Status | Reason |
|--------|--------|
| `409` | Request already sent |

---

### Withdraw a Message Request

Only works while the request is still `pending`.

```
DELETE /connections/{user_id}/message-request/{target_id}
```

**Response `200`:**
```json
{ "status": "withdrawn", "receiver_id": "a1b2c3d4-..." }
```

---

### Accept a Message Request

`user_id` must be the receiver. Use `request_id` from the received inbox.

```
PATCH /connections/{user_id}/message-request/{request_id}/accept
```

**Response `200`:**
```json
{ "id": 4, "status": "accepted" }
```

**Errors:**

| Status | Reason |
|--------|--------|
| `404` | Not found, already acted on, or you are not the receiver |

---

### Decline a Message Request

```
PATCH /connections/{user_id}/message-request/{request_id}/decline
```

**Response `200`:**
```json
{ "id": 4, "status": "declined" }
```

---

### Get Received Message Requests (Inbox)

Only returns `pending` requests.

```
GET /connections/{user_id}/message-requests/received
```

**Response `200`:**
```json
{
  "user_id": "a1b2c3d4-...",
  "total": 1,
  "requests": [
    {
      "request_id": 4,
      "from": {
        "user_id": "c37a3257-...",
        "name": "Ravi Traders",
        "role": "trader",
        "commodity": ["rice", "cotton"],
        "qty_range": "100–500mt"
      },
      "sent_at": "2026-04-15T10:00:00.000000+00:00"
    }
  ]
}
```

> Use `request_id` when calling accept or decline.

---

### Get Sent Message Requests

Returns across all statuses (pending, accepted, declined).

```
GET /connections/{user_id}/message-requests/sent
```

**Response `200`:**
```json
{
  "user_id": "c37a3257-...",
  "total": 1,
  "requests": [
    {
      "request_id": 4,
      "to": {
        "user_id": "a1b2c3d4-...",
        "name": "Anita Shah",
        "role": "broker",
        "commodity": ["rice"],
        "qty_range": "200–800mt"
      },
      "status": "pending",
      "sent_at": "2026-04-15T10:00:00.000000+00:00",
      "acted_at": null
    }
  ]
}
```

> `acted_at` is `null` while pending. Filled once the receiver accepts or declines.

---

### Search Profiles

All filter params are optional.

```
GET /connections/{user_id}/search?q=ravi&role=trader&commodity=rice
```

| Query Param | Required | Description |
|-------------|----------|-------------|
| `q` | No | Partial match on name or business name |
| `role` | No | Exact: `trader`, `broker`, `exporter` |
| `commodity` | No | Partial match on commodity name |

**Response `200`:**
```json
{
  "total": 2,
  "results": [
    {
      "user_id": "a1b2c3d4-...",
      "name": "Anita Shah",
      "business_name": "Shah Exports",
      "role": "exporter",
      "commodity": ["sugar"],
      "is_verified": true,
      "qty_range": "1000–5000mt"
    }
  ]
}
```

> The acting `user_id` is always excluded from results.

---

### Search Suggestions (Autocomplete)

Returns top 8 name/business name matches. Minimum 2 characters.

```
GET /connections/search/suggestions?q=rav
```

**Response `200`:**
```json
{
  "q": "rav",
  "total": 3,
  "suggestions": [
    {
      "user_id": "c37a3257-...",
      "name": "Ravi Traders",
      "business_name": "Ravi Agro Pvt Ltd",
      "role": "trader",
      "commodity": ["rice", "cotton"],
      "is_verified": false
    }
  ]
}
```

---

### Connections Error Reference

| Status | When |
|--------|------|
| `404` | Not following, request not found, request already acted on, wrong receiver |
| `409` | Already following, message request already exists |
| `422` | Missing required field or wrong data type |

---

## 4. Posts

> **Auth:** No token. Uses `profile_id` (integer) as query param on every endpoint.

**Base prefix:** `/posts`

---

### Post Object (Full Shape)

```json
{
  "id": 1,
  "profile_id": 3,
  "category_id": 1,
  "commodity_id": 2,
  "caption": "Cotton prices are up this week.",
  "image_url": null,
  "is_public": true,
  "target_roles": null,
  "allow_comments": true,
  "grain_type_size": null,
  "commodity_quantity_min": null,
  "commodity_quantity_max": null,
  "price_type": null,
  "other_description": null,
  "view_count": 14,
  "like_count": 3,
  "comment_count": 2,
  "share_count": 1,
  "is_liked": false,
  "is_saved": true,
  "created_at": "2026-04-17T10:30:00"
}
```

---

### Create Post

```
POST /posts/?profile_id={profile_id}
Content-Type: application/json
```

#### Standard Post (categories 1, 2, 3)

```json
{
  "category_id": 1,
  "commodity_id": 2,
  "caption": "Cotton market is very active this season.",
  "is_public": true,
  "allow_comments": true,
  "target_roles": null,
  "image_url": null
}
```

#### Deal / Requirement Post (category 4) — extra fields required

```json
{
  "category_id": 4,
  "commodity_id": 1,
  "caption": "Looking for 500 MT of basmati rice.",
  "is_public": true,
  "allow_comments": true,
  "grain_type_size": "Basmati Long Grain",
  "commodity_quantity_min": 200.0,
  "commodity_quantity_max": 500.0,
  "price_type": "negotiable"
}
```

#### Other Post (category 5) — extra field required

```json
{
  "category_id": 5,
  "commodity_id": 3,
  "caption": "Check this out.",
  "is_public": true,
  "allow_comments": true,
  "other_description": "This is a general update about our operations."
}
```

**All fields:**

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `category_id` | int | Yes | 1–5 |
| `commodity_id` | int | Yes | 1–3 |
| `caption` | string | Yes | Cannot be empty |
| `is_public` | bool | No | Default: `true` |
| `allow_comments` | bool | No | Default: `true` |
| `target_roles` | int[] \| null | No | Default: `null` (all roles) |
| `image_url` | string \| null | No | Default: `null` |
| `grain_type_size` | string | Required if category 4 | — |
| `commodity_quantity_min` | float | Required if category 4 | Lower bound in MT |
| `commodity_quantity_max` | float | Required if category 4 | Upper bound in MT |
| `price_type` | string | Required if category 4 | `"fixed"` or `"negotiable"` |
| `other_description` | string | Required if category 5 | Cannot be empty |

**Response `201`:** Full post object inside `data`.

**Errors:**

| Status | Reason |
|--------|--------|
| `422` | Empty caption, missing deal fields for category 4, missing `other_description` for category 5, invalid `price_type` |

---

### Get Feed (All Posts)

View counts are NOT incremented here — only by `GET /posts/{post_id}`.

```
GET /posts/?profile_id={profile_id}&limit=20&offset=0
```

**Response `200`:** `data` is an array of post objects (may be `[]`).

---

### Get My Posts

```
GET /posts/mine?profile_id={profile_id}&limit=20&offset=0
```

**Response `200`:** Array of post objects, newest first.

---

### Get My Saved Posts

```
GET /posts/saved?profile_id={profile_id}&limit=20&offset=0
```

**Response `200`:** Array of post objects, most-recently-saved first.

---

### Get Single Post

Increments `view_count` by 1 — only once per profile. Subsequent views by the same profile are ignored.

```
GET /posts/{post_id}?profile_id={profile_id}
```

**Response `200`:** Full post object inside `data`.

**Errors:**

| Status | Reason |
|--------|--------|
| `404` | Post not found |

---

### Update Post (Owner Only)

```
PATCH /posts/{post_id}?profile_id={profile_id}
Content-Type: application/json
```

Send only the fields you want to change.

**Response `200`:** Updated full post object.

**Errors:**

| Status | Reason |
|--------|--------|
| `403` | You do not own this post |
| `404` | Post not found |

---

### Delete Post (Owner Only)

```
DELETE /posts/{post_id}?profile_id={profile_id}
```

**Response `204`:** No body.

**Errors:**

| Status | Reason |
|--------|--------|
| `403` | You do not own this post |
| `404` | Post not found |

---

### Like / Unlike Post (Toggle)

First call = like. Second call = unlike.

```
POST /posts/{post_id}/like?profile_id={profile_id}
```

**Response `200`:**
```json
{
  "success": true,
  "message": "Like toggled",
  "data": {
    "liked": true,
    "like_count": 4
  }
}
```

---

### Get Comments

```
GET /posts/{post_id}/comments?profile_id={profile_id}&limit=20&offset=0
```

**Response `200`:**
```json
{
  "success": true,
  "message": "Comments fetched successfully",
  "data": [
    {
      "id": 12,
      "post_id": 7,
      "profile_id": 5,
      "content": "Very insightful, thanks!",
      "created_at": "2026-04-17T11:00:00"
    }
  ]
}
```

Ordered oldest first.

---

### Add Comment

```
POST /posts/{post_id}/comments?profile_id={profile_id}
Content-Type: application/json
```

**Request body:**
```json
{ "content": "Very insightful, thanks!" }
```

**Response `201`:** Comment object inside `data`.

**Errors:**

| Status | Reason |
|--------|--------|
| `403` | Comments are disabled on this post |
| `404` | Post not found |
| `422` | Empty content |

---

### Delete Comment (Owner Only)

```
DELETE /posts/{post_id}/comments/{comment_id}?profile_id={profile_id}
```

**Response `204`:** No body.

**Errors:**

| Status | Reason |
|--------|--------|
| `403` | You do not own this comment |
| `404` | Comment not found |

---

### Share Post

Records a share event. **Not a toggle** — each call adds one more share.

```
POST /posts/{post_id}/share?profile_id={profile_id}
```

**Response `200`:**
```json
{
  "success": true,
  "message": "Share recorded",
  "data": { "share_count": 5 }
}
```

---

### Save / Unsave Post (Toggle)

First call = save. Second call = unsave.

```
POST /posts/{post_id}/save?profile_id={profile_id}
```

**Response `200`:**
```json
{
  "success": true,
  "message": "Save toggled",
  "data": { "saved": true }
}
```

---

### Posts Error Reference

| Status | When |
|--------|------|
| `201` | Post or comment created |
| `204` | Delete succeeded (no body) |
| `403` | You don't own the resource |
| `404` | Post or comment not found |
| `422` | Validation failed |

---

## 5. Post Recommendation Feed

> **Auth:** No token. Uses `profile_id` (integer) as query param.

---

### Get Recommended Feed

Returns up to 25 personalised post IDs ranked by composite score. **Does not return full post content** — use the IDs to hydrate post cards via `GET /posts/{post_id}`.

```
GET /posts/recommendation/feed?profile_id={profile_id}
```

**Response `200`:**
```json
{
  "success": true,
  "message": "...",
  "data": [
    { "post_id": 42, "score": 0.847231 },
    { "post_id": 17, "score": 0.763904 },
    { "post_id": 88, "score": 0.701455 }
  ]
}
```

> `data` is an array — may be `[]` if no eligible posts exist.

**Frontend flow:**
```
1. GET /posts/recommendation/feed?profile_id={profile_id}
   → get list of { post_id, score }

2. For each post_id (in order), call:
   GET /posts/{post_id}?profile_id={profile_id}
   → fetch full post card

3. Render in the order returned by step 1 (already best-first)
   → step 2 calls can be made in parallel
```

**Pagination:** No `limit`/`offset`. Seen-post deduplication means the same post won't be served again for 30 days. Simply call the endpoint again when the user reaches the end — a fresh batch is returned automatically.

**Empty feed fallback:** If `data` is `[]`, fall back to `GET /posts/?profile_id={profile_id}` (chronological feed).

**Errors:**

| Status | Reason |
|--------|--------|
| `404` | No profile found for this `profile_id` |
| `422` | `profile_id` missing or not an integer |

---

### How Scoring Works

```
final_score = vec_score × taste_weight × (1 + engagement) × freshness × social_boost
```

| Factor | Description |
|--------|-------------|
| `vec_score` | Cosine similarity between user and post vectors (commodity 3×, role 2×, geo 1.5×, qty 1×) |
| `taste_weight` | User's historical engagement with this post category |
| `engagement` | Based on saves, comments, likes |
| `freshness` | 1.4× if < 2h old, 1.2× if < 6h old |
| `social_boost` | 1.5× if post author is followed by viewer |

**Diversity caps (applied last):** Max 3 posts per category, max 2 posts per author, max 25 total.

---

## 6. News

> **Auth:** No token. Uses `user_id` (UUID) as query param on all endpoints.

---

### Get Personalised News Feed

Returns 5 sections of ranked articles.

```
GET /news/feed?user_id={user_id}&scope=national
```

| Query Param | Required | Description |
|-------------|----------|-------------|
| `user_id` | Yes | Acting user's UUID |
| `state` | No | User's state e.g. `punjab` (for region matching) |
| `scope` | No | `local` / `state` / `national` / `global` — default `national` |

**Response `200`:**
```json
{
  "success": true,
  "message": "Feed fetched successfully",
  "data": {
    "sections": [
      { "key": "right_now",      "label": "Right Now",                   "articles": [...] },
      { "key": "for_you_today",  "label": "For You Today",               "articles": [...] },
      { "key": "trending",       "label": "Trending in Your Network",    "articles": [...] },
      { "key": "worth_knowing",  "label": "Worth Knowing",               "articles": [...] },
      { "key": "government",     "label": "From Government Sources",     "articles": [...] }
    ]
  }
}
```

| Section | Max articles | Logic |
|---------|-------------|-------|
| `right_now` | 3 | Breaking news: cluster 1 or 2, severity ≥ 8.0 |
| `for_you_today` | 12 | Top scored articles for this user |
| `trending` | 5 | Trending in user's role:commodity:state segment |
| `worth_knowing` | 5 | Medium severity (4.0–7.9) |
| `government` | 3 | Government sources only |

**Errors:**

| Status | Reason |
|--------|--------|
| `404` | Profile not found for this user |

---

### Article Object

```json
{
  "id": "3f8a2c1d-9e74-4b1a-8d3f-2c1d9e744b1a",
  "title": "Wheat MSP hiked by ₹150 per quintal",
  "summary": "The government announced...",
  "url": "https://economictimes.com/...",
  "image_url": "https://...",
  "published_at": "2026-04-18T09:30:00",
  "cluster_id": 1,
  "severity": 8.5,
  "commodities": ["wheat"],
  "regions": ["punjab", "haryana"],
  "scope": "national",
  "source_name": "Economic Times Markets",
  "trader_impact": "Traders may face higher procurement costs.",
  "broker_impact": "Brokers should anticipate increased activity.",
  "exporter_impact": "Exporters might see reduced margins.",
  "liked": false,
  "saved": false,
  "like_count": 42,
  "comment_count": 7,
  "share_count": 15
}
```

> Show `trader_impact` / `broker_impact` / `exporter_impact` based on the logged-in user's role.

---

### Search News

Full-text search on article titles and summaries. Articles older than 72 hours are excluded.

```
GET /news/search?q=wheat+price&commodity=wheat&page=1&per_page=20
```

| Param | Required | Default | Description |
|-------|----------|---------|-------------|
| `q` | No | — | Search query |
| `commodity` | No | — | Filter by commodity name |
| `page` | No | 1 | Page number |
| `per_page` | No | 20 | Max 100 |

**Response `200`:** `data` is an array of article objects.

---

### Get Single Article

```
GET /news/{article_id}?user_id={user_id}
```

`user_id` is optional — pass it to get personalised `liked` / `saved` flags.

**Response `200`:** Single article object inside `data`.

**Errors:**

| Status | Reason |
|--------|--------|
| `404` | Article not found |

---

### Record Engagement

Call when the user views, clicks, or dwells on an article. For like/save/share/comment use the dedicated endpoints below.

```
POST /news/{article_id}/engage?user_id={user_id}
Content-Type: application/json
```

**Request body:**
```json
{
  "action_type": "dwell",
  "dwell_time_s": 45,
  "segment_id": "trader:wheat:punjab"
}
```

| Field | Required | Notes |
|-------|----------|-------|
| `action_type` | Yes | `view` / `click` / `dwell` / `skip` |
| `dwell_time_s` | Conditional | Required when `action_type` is `dwell`. Dwell < 12s is ignored. |
| `segment_id` | No | Format: `role:commodity:state` |

**When to call:**
```
Article enters viewport    → action_type: "view"
User taps to open article  → action_type: "click"
User leaves article screen → action_type: "dwell", dwell_time_s: <seconds>
User scrolls past quickly  → action_type: "skip"
```

**Response `201`:**
```json
{ "success": true, "message": "Engagement recorded", "data": null }
```

---

### Like / Unlike Article (Toggle)

```
POST /news/{article_id}/like?user_id={user_id}
```

**Response `200`:**
```json
{
  "success": true,
  "message": "Like toggled",
  "data": { "liked": true, "like_count": 43 }
}
```

---

### Save / Unsave Article (Toggle)

```
POST /news/{article_id}/save?user_id={user_id}
```

**Response `200`:**
```json
{
  "success": true,
  "message": "Save toggled",
  "data": { "saved": true }
}
```

---

### Share Article

**Not a toggle** — each call adds one share.

```
POST /news/{article_id}/share?user_id={user_id}
```

**Response `200`:**
```json
{
  "success": true,
  "message": "Shared successfully",
  "data": { "share_count": 16 }
}
```

---

### Post a Comment on Article

```
POST /news/{article_id}/comment?user_id={user_id}
Content-Type: application/json
```

**Request body:**
```json
{ "text": "Prices in Punjab will rise this week." }
```

Min 1 char, max 1000 chars.

**Response `201`:**
```json
{ "success": true, "message": "Comment posted", "data": null }
```

**Errors:**

| Status | Reason |
|--------|--------|
| `404` | Article not found |
| `422` | Empty or too long (> 1000 chars) |

---

### Get Article Comments

```
GET /news/{article_id}/comments?page=1&per_page=20
```

**Response `200`:**
```json
{
  "success": true,
  "message": "Comments fetched",
  "data": [
    {
      "id": "a1b2c3d4-...",
      "user_id": "uuid-of-commenter",
      "comment_text": "Prices in Punjab will rise this week.",
      "created_at": "2026-04-18T10:15:00"
    }
  ]
}
```

Newest first.

---

### Get My News Taste Profile

Returns the user's cluster taste weights — shows which news types they engage with most.

```
GET /news/my/taste?user_id={user_id}
```

**Response `200`:**
```json
{
  "success": true,
  "message": "Taste profile fetched",
  "data": {
    "user_id": "...",
    "clusters": [
      {
        "cluster_id": 8,
        "cluster_name": "Price Volatility & Sentiment",
        "taste_weight": 0.9,
        "interaction_count": 0,
        "avg_dwell_time": 0.0,
        "is_seeded": true
      }
    ]
  }
}
```

---

### Get My News Engagement History

```
GET /news/my/history?user_id={user_id}&action_type=like&page=1&per_page=20
```

| Param | Required | Description |
|-------|----------|-------------|
| `action_type` | No | Filter: `view` / `click` / `dwell` / `like` / `save` / `comment` / `share_out` |

---

## 7. Home Feed

> **Auth:** No token. Uses `user_id` (UUID) as query param.

The home feed blends posts, news, groups, and connection suggestions into one ranked stream.

---

### Get Home Feed

```
GET /feed/home?user_id={user_id}
GET /feed/home?user_id={user_id}&cursor={cursor_json}
```

- **First call:** No cursor — priority pins are resolved (unseen posts from followed users last 6h + breaking news last 3h).
- **Subsequent calls:** Pass the `cursor` from the previous response to get the next page.

**Response `200`:**
```json
{
  "success": true,
  "message": "...",
  "data": {
    "items": [ ... ],
    "cursor": {
      "post_cursor": "2026-04-17T10:30:00+00:00|42",
      "news_cursor": "2026-04-17T08:00:00+00:00|a1b2c3d4-...",
      "group_cursor": "2026-04-17T09:15:00+00:00|88",
      "connection_cursor": 3,
      "page_num": 2
    },
    "has_more": true,
    "weights_used": { ... }
  }
}
```

**Each item in `items`:**
```json
{
  "item_type": "post",
  "item_id": "42",
  "content_type_label": "post",
  "is_priority": false,
  "data": { ... }
}
```

| `item_type` | `content_type_label` | `is_priority` | What to render |
|-------------|---------------------|---------------|----------------|
| `post` | `post` | false | Regular post card |
| `post` | `post` | true | Post from followed user (pinned) — show badge |
| `news` | `news` | false | News card |
| `news` | `breaking_news` | true | Breaking news card + badge |
| `group` | `group_activity` | false | Post card with group label |
| `connection` | `connection` | false | People suggestion card |

**Pagination:**
```
First load:  GET /feed/home?user_id=<uuid>                          → save cursor
Load more:   GET /feed/home?user_id=<uuid>&cursor=<json_cursor>     → replace cursor
Refresh:     GET /feed/home?user_id=<uuid>  (no cursor)             → re-runs priority pins
```

> **Cursor must be passed as a JSON string** in the query parameter.  
> When `has_more` is `false` → no more pages.

**Errors:**

| Status | Reason |
|--------|--------|
| `400` | `cursor` is not valid JSON |
| `404` | No profile found for this `user_id` |
| `422` | Missing `user_id` |

---

### Submit Engagement Signals

Send after every ~10 viewport events, or when a user performs an explicit action (like, save, share).

```
POST /feed/engagement?user_id={user_id}
Content-Type: application/json
```

**Request body:**
```json
{
  "signals": [
    { "item_id": "42",           "item_type": "post",       "action": "dwell",              "dwell_ms": 5500 },
    { "item_id": "42",           "item_type": "post",       "action": "like" },
    { "item_id": "a1b2c3d4-...", "item_type": "news",       "action": "skip",               "dwell_ms": 900 },
    { "item_id": "uuid-...",     "item_type": "connection", "action": "connection_dismiss" }
  ]
}
```

**Passive signals (viewport-based):**

| Action | `dwell_ms` required | Trigger |
|--------|---------------------|---------|
| `skip` | Yes | Item visible < 1.5s |
| `dwell` | Yes | Item visible 4–10s |
| `strong_dwell` | Yes | Item visible > 10s |

> Items visible 1.5–4s are neutral — do not send a signal.

**Explicit signals (user action):**

| Action | Applies to |
|--------|------------|
| `like` | post, news, group |
| `save` | post, news, group |
| `share` | post, news, group |
| `comment` | post, group |
| `connection_accept` | connection |
| `connection_dismiss` | connection |

**Response `200`:**
```json
{
  "success": true,
  "message": "Engagement recorded",
  "data": { "acknowledged": true, "signals_processed": 4 }
}
```

---

## 8. Groups

> **Auth:** No token. Uses `user_id` (UUID) as query param on all endpoints.  
> **Important:** All group endpoints need a trailing slash and the `?user_id=` param.

**Base prefix:** `/api/v1/groups`

---

### Get Group Suggestions

Returns top 20 personalised group suggestions. Excludes groups the user is already in and private groups.

```
GET /api/v1/groups/suggestions/{user_id}
```

**Response `200`:**
```json
{
  "success": true,
  "message": "Group suggestions fetched",
  "data": [
    {
      "group": { "id": "uuid-...", "name": "Sugar Traders Maharashtra", "member_count": 14 },
      "match_score": 0.8004,
      "match_reasons": ["Matches your commodities", "Targets your role"]
    }
  ]
}
```

---

### List Groups

```
GET /api/v1/groups/?user_id={user_id}&commodity=sugar&accessibility=public&page=1&per_page=20
```

| Param | Required | Description |
|-------|----------|-------------|
| `user_id` | Yes | Populates `is_member`, `is_muted`, `is_favorite` per group |
| `commodity` | No | Filter by commodity |
| `accessibility` | No | `public`, `private`, or `invite_only` |
| `page` | No | Default 1 |
| `per_page` | No | Default 20, max 100 |

**Response `200`:** Array of GroupOut objects inside `data`.

---

### Create a Group

> ⚠️ Only **verified users** (`is_verified: true`) can create groups.

```
POST /api/v1/groups/?user_id={user_id}
Content-Type: application/json
```

**Request body:**
```json
{
  "name": "Sugar Traders Maharashtra",
  "description": "A group for sugar traders to discuss market rates.",
  "group_rules": "No spam. Only trade-related discussions.",
  "commodities": ["sugar", "rice"],
  "region_market": "Maharashtra",
  "region_lat": 19.7515,
  "region_lon": 75.7139,
  "category": "commodity_trading",
  "accessibility": "public",
  "posting_perm": "all_members",
  "chat_perm": "all_members",
  "target_roles": ["trader", "broker"]
}
```

| Field | Required | Notes |
|-------|----------|-------|
| `name` | Yes | — |
| `commodities` | No | Array of commodity strings |
| `category` | No | `commodity_trading`, `news`, `network` |
| `accessibility` | No | `public`, `private`, `invite_only` |
| `posting_perm` | No | `all_members`, `admins_only` |
| `chat_perm` | No | `all_members`, `admins_only` |
| `target_roles` | No | `trader`, `broker`, `exporter` |

**Response `201`:**
```json
{
  "success": true,
  "message": "Group created successfully",
  "data": {
    "id": "uuid-of-new-group",
    "name": "Sugar Traders Maharashtra",
    "accessibility": "public",
    "member_count": 1,
    "created_by": "uuid-of-creator",
    "created_at": "2026-04-16T16:00:00.000000",
    "is_member": true,
    "member_role": "admin",
    "is_muted": false,
    "is_favorite": false
  }
}
```

> ✅ Save `data.id` — this is the group's UUID used for all subsequent group calls.

**Errors:**

| Status | Reason |
|--------|--------|
| `403` | User is not verified |

---

### Get Group Details

```
GET /api/v1/groups/{group_id}?user_id={user_id}
```

> `group_id` is the UUID returned from group creation or the group list.

**Response `200`:** Full GroupOut object inside `data`.

**Errors:**

| Status | Reason |
|--------|--------|
| `404` | Group not found |

---

### Update Group (Admin Only)

```
PATCH /api/v1/groups/{group_id}?user_id={user_id}
Content-Type: application/json
```

Send only fields you want to update.

**Errors:**

| Status | Reason |
|--------|--------|
| `403` | Not an admin |

---

### Update Group Permissions (Admin Only)

```
PATCH /api/v1/groups/{group_id}/permissions?user_id={user_id}
Content-Type: application/json
```

```json
{
  "accessibility": "invite_only",
  "posting_perm": "admins_only",
  "chat_perm": "all_members"
}
```

---

### Join a Public Group

```
POST /api/v1/groups/{group_id}/join?user_id={user_id}
```

Only works for `accessibility: public` groups.

**Response `200`:**
```json
{
  "success": true,
  "message": "Joined group",
  "data": { "group_id": "uuid-...", "role": "member", "joined_at": "..." }
}
```

**Errors:**

| Status | Reason |
|--------|--------|
| `409` | Already a member |

---

### Join via Invite Link

```
POST /api/v1/groups/join-by-link/{token}?user_id={user_id}
```

`token` is the `invite_link_token` from the invite link endpoint.

**Response `200`:**
```json
{
  "success": true,
  "message": "Joined group via invite link",
  "data": {
    "group_id": "uuid-...",
    "group_name": "Sugar Traders Maharashtra",
    "role": "member",
    "joined_at": "2026-04-16T17:00:00.000000+00:00"
  }
}
```

**Errors:**

| Status | Reason |
|--------|--------|
| `404` | Invalid invite token |

---

### Leave a Group

```
DELETE /api/v1/groups/{group_id}/leave?user_id={user_id}
```

**Response `200`:**
```json
{ "success": true, "message": "Left group", "data": null }
```

---

### List Group Members

```
GET /api/v1/groups/{group_id}/members?user_id={user_id}&page=1&per_page=20
```

**Response `200`:** Array of GroupMemberOut objects inside `data`.

```json
{
  "user_id": "uuid",
  "name": "Ravi Kumar",
  "role_name": "Trader",
  "is_verified": true,
  "member_role": "admin",
  "is_frozen": false,
  "joined_at": "..."
}
```

---

### Add Members (Admin Only)

```
POST /api/v1/groups/{group_id}/members/add?user_id={user_id}
Content-Type: application/json
```

```json
{ "user_ids": ["uuid-1", "uuid-2"] }
```

---

### Remove a Member (Admin Only)

```
DELETE /api/v1/groups/{group_id}/members/{target_user_id}?user_id={user_id}
```

---

### Freeze a Member (Admin Only)

Frozen members cannot post or chat.

```
POST /api/v1/groups/{group_id}/members/{target_user_id}/freeze?user_id={user_id}
```

**Response `200`:**
```json
{ "success": true, "message": "Member frozen", "data": { "user_id": "...", "is_frozen": true } }
```

---

### Unfreeze a Member (Admin Only)

```
DELETE /api/v1/groups/{group_id}/members/{target_user_id}/freeze?user_id={user_id}
```

---

### Toggle Mute Notifications

Each call toggles the state.

```
POST /api/v1/groups/{group_id}/mute?user_id={user_id}
```

**Response `200`:**
```json
{ "success": true, "message": "Mute toggled", "data": { "is_muted": true } }
```

---

### Toggle Favorite

```
POST /api/v1/groups/{group_id}/favorite?user_id={user_id}
```

**Response `200`:**
```json
{ "success": true, "message": "Favorite toggled", "data": { "is_favorite": true } }
```

---

### Get Invite Link (Admin Only)

Token is generated on first call if none exists.

```
GET /api/v1/groups/{group_id}/invite-link?user_id={user_id}
```

**Response `200`:**
```json
{
  "success": true,
  "message": "Invite link ready",
  "data": { "invite_link_token": "abc123xyz456def7" }
}
```

---

### Report a Group

```
POST /api/v1/groups/{group_id}/report?user_id={user_id}
Content-Type: application/json
```

```json
{ "reason": "spam" }
```

**Response `200`:**
```json
{
  "success": true,
  "message": "Report submitted — our team will review it",
  "data": { "group_id": "...", "reason": "spam", "status": "submitted" }
}
```

---

### Groups Error Reference

| Status | When |
|--------|------|
| `403` | Not an admin, or not verified (group creation) |
| `404` | Group not found, invalid invite token |
| `409` | Already a member |
| `422` | Missing required field or wrong data type |

---

## 9. User Recommendations

> **Auth:** No token. Uses `user_id` (UUID) in path.

---

### Get Recommendations for a User

Returns top 20 matched users based on cosine similarity (commodity, role, location, quantity).

```
GET /recommendations/{user_id}
```

**Response `200`:**
```json
{
  "user_id": 42,
  "role": "trader",
  "commodity": "rice; cotton",
  "qty_range": "100–500mt",
  "total": 20,
  "results": [
    {
      "user_id": 7,
      "role": "exporter",
      "commodity": "rice",
      "city": "Mumbai",
      "state": "Maharashtra",
      "qty_range": "200–800mt",
      "similarity": 0.9312
    }
  ]
}
```

---

### Refresh User's Recommendation Vector

Call this after a user updates their profile to recompute and persist their embedding, then returns fresh recommendations.

```
GET /recommendations/{user_id}/refresh
```

Same response shape as above.

---

### Ad-hoc Recommendation Search

Search for matches without an existing user account (useful for previewing before registration).

```
POST /recommendations/search
Content-Type: application/json
```

**Request body:**
```json
{
  "commodity": ["rice", "cotton"],
  "role": "trader",
  "latitude_raw": 19.076,
  "longitude_raw": 72.877,
  "qty_min_mt": 100,
  "qty_max_mt": 500
}
```

**Response `200`:** `results` array in same format as above (no outer `user_id` wrapper).

---

## 10. Reference Data

### Roles

| ID | Name |
|----|------|
| `1` | Trader |
| `2` | Broker |
| `3` | Exporter |

### Commodities

| ID | Name |
|----|------|
| `1` | Rice |
| `2` | Cotton |
| `3` | Sugar |

### Interests

| ID | Name |
|----|------|
| `1` | Connections |
| `2` | Leads |
| `3` | News |

### Post Categories

| ID | Name |
|----|------|
| `1` | Market Update |
| `2` | Knowledge |
| `3` | Discussion |
| `4` | Deal / Requirement |
| `5` | Other |

### News Clusters

| ID | Name |
|----|------|
| `1` | Policy & Regulation |
| `2` | Geopolitical & Macro Shocks |
| `3` | Supply-side Disruptions |
| `4` | Financial & Market Mechanics |
| `5` | Structural & Industrial Shifts |
| `6` | Long-term Demand Trends |
| `7` | Market Participation & Deal Flow |
| `8` | Price Volatility & Sentiment |
| `9` | Local Operational Events |
| `10` | Indirect / General News |

### Group Accessibility Rules

| Value | Who can join |
|-------|-------------|
| `public` | Anyone via `POST /{group_id}/join` |
| `private` | Only if added by admin |
| `invite_only` | Only via invite link token |

---

## 11. Global Error Reference

| Status | Meaning |
|--------|---------|
| `200` | Success |
| `201` | Created |
| `204` | Deleted (no body) |
| `400` | Bad request — invalid JSON, bad cursor, invalid action type |
| `401` | Invalid or expired onboarding token |
| `403` | Forbidden — wrong ownership or insufficient permissions |
| `404` | Resource not found |
| `409` | Conflict — already exists (duplicate follow, duplicate request, etc.) |
| `422` | Validation error — missing required param, wrong type, empty field |
| `500` | Server error |

All error responses:
```json
{ "detail": "Human-readable message." }
```

---

## Quick Identity Cheatsheet

```
user_id    (UUID)    → Profile, Connections, News, Home Feed, Groups, User Recommendations
profile_id (integer) → Posts, Post Recommendation Feed

onboarding_token → ONLY for POST /profile/user and POST /profile/
                   expires in 15 minutes, never used again after onboarding
```
