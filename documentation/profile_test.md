# Profile Module — Developer Guide & Test Reference

A complete reference for the onboarding flow, profile creation, and profile management APIs.

Base URL (local): `http://localhost:8000`

---

## Table of Contents

1. [Local Setup](#1-local-setup)
2. [How Auth Works](#2-how-auth-works)
3. [Seed the Database](#3-seed-the-database)
4. [Generate Test Tokens](#4-generate-test-tokens)
5. [API Quick Reference](#5-api-quick-reference)
6. [Onboarding Flow](#6-onboarding-flow)
7. [Profile APIs](#7-profile-apis)
8. [Database Schema](#8-database-schema)
9. [Error Reference](#9-error-reference)

---

## 1. Local Setup

**Start the server:**
```bash
uvicorn main:app --reload
```

Server runs at `http://localhost:8000`.
Swagger UI at `http://localhost:8000/docs` — use this to test all endpoints interactively.

---

## 2. How Auth Works

The profile module uses **two types of JWT tokens**. The auth module (OTP flow) is not built yet, so generate tokens manually using the script in Section 4.

| Token type | Used for | How to get it |
|---|---|---|
| **Onboarding token** | `POST /profile/user` and `POST /profile/` | Run `python scripts/gen_token.py` |
| **Access token** | All other endpoints (`GET /me`, `PATCH`, `DELETE`, `GET /{id}`) | Same script, different token |

**Both tokens** go in the `Authorization` header as a Bearer token:
```
Authorization: Bearer <token>
```

Both tokens encode the same `user_id`. Use the same `user_id` for all steps — that's what ties the user to their profile.

---

## 3. Seed the Database

Profiles require a valid `role_id`, `commodity` IDs, and `requirement` IDs. These must exist in the lookup tables first.

**Run once:**
```bash
python scripts/seed.py
```

**Current seed data in the DB:**

### Roles
| Name | ID |
|---|---|
| `trader` | `03b2851f-fe58-47ec-9796-414ca0eb4742` |
| `broker` | `2e436fe3-93c4-4774-b581-0905fa77fb75` |
| `exporter` | `1a7df8d1-df88-4b5e-839e-d38a3cfe0959` |

### Commodities
| Name | ID |
|---|---|
| `cotton` | `3d3b18e1-7f1e-46fb-be5a-2c7f743a16b9` |
| `rice` | `71399b6f-38cc-4101-8cbe-0dc880bc7b62` |
| `sugar` | `1ca6216a-a369-45eb-a96e-cd6bda31fff2` |

### Requirements
| Name | ID |
|---|---|
| `export_license` | `767d7ec5-ec71-424b-8c7c-712b19bc5db7` |
| `import_license` | `af399a71-d88d-4c6c-a554-ca78a03b513c` |
| `gst_registration` | `b510e72d-f411-48a7-a257-f1d0dcd10b30` |

---

## 4. Get an Onboarding Token

The auth module is built and uses OTP via SMS (MSG91) in production. In **dev mode** (`DEV_MODE=true` in `.env`) the OTP is printed to the server console — no SMS is sent.

### Option A — Use the real OTP flow (recommended)

**Step 1 — Request OTP:**
```bash
curl -X POST http://localhost:8000/auth/send-otp \
  -H "Content-Type: application/json" \
  -d '{ "phone_number": "9876543210", "country_code": "+91" }'
```

Watch the **server terminal** — you'll see:
```
[DEV] OTP for +91 9876543210: 482931
```

**Step 2 — Verify OTP and get onboarding token:**
```bash
curl -X POST http://localhost:8000/auth/verify-otp \
  -H "Content-Type: application/json" \
  -d '{
    "phone_number": "9876543210",
    "country_code": "+91",
    "otp_code": "482931"
  }'
```

**Response:**
```json
{
    "success": true,
    "message": "OTP verified. Use the onboarding token to complete registration.",
    "data": {
        "onboarding_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
        "token_type": "bearer",
        "expires_in": 900
    }
}
```

Copy the `onboarding_token` — use it for `POST /profile/user` and `POST /profile/`.

---

### Option B — Skip OTP (bypass for quick testing)

```bash
python scripts/gen_token.py
```

Generates an onboarding token directly without going through OTP. Useful for testing profile endpoints in isolation.

---

**To use in Swagger UI (`/docs`):**
1. Open `http://localhost:8000/docs`
2. Click **Authorize** (top right, lock icon)
3. Paste the onboarding token in the `Value` field — click **Authorize**
4. All requests now send `Authorization: Bearer <token>` automatically

**To use in Postman / curl:**
```
Authorization: Bearer <onboarding_token>
```

---

## 5. API Quick Reference

| Method | Endpoint | Token needed | What it does |
|---|---|---|---|
| `POST` | `/profile/user` | Onboarding | Create the user row (step 1) |
| `POST` | `/profile/` | Onboarding | Create profile + business (step 2) |
| `GET` | `/profile/me` | Access | Fetch your own profile |
| `PATCH` | `/profile/` | Access | Update your profile |
| `DELETE` | `/profile/` | Access | Delete your profile |
| `GET` | `/profile/my-posts` | Access | My posts (paginated) |
| `GET` | `/profile/saved` | Access | My saved posts (paginated) |
| `GET` | `/profile/{profile_id}` | Access | Public view of any profile |

---

## 6. Onboarding Flow

Profile creation is a **two-step process** — both steps use the **onboarding token**.

```
Step 1: POST /profile/user    ← creates the User row (phone, country_code)
Step 2: POST /profile/        ← creates Profile + Business + commodities + requirements
```

Both steps must use the **same user_id** encoded in the onboarding token.

---

### Step 1 — `POST /profile/user`

Creates the `users` row. Must be called before creating a profile.

**Token:** Onboarding token
**No request body required** — phone number and country code are read from the token.

**Example (curl):**
```bash
curl -X POST http://localhost:8000/profile/user \
  -H "Authorization: Bearer <ONBOARDING_TOKEN>"
```

**Success `201`:**
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

**Error `409`** — user already exists for this phone number:
```json
{
    "detail": "Phone number already registered"
}
```

---

### Step 2 — `POST /profile/`

Creates the profile. Call this immediately after Step 1 with the same token.

**Token:** Onboarding token
**Content-Type:** `application/json`

**Request body:**
```json
{
    "name": "Ravi Traders",
    "role_id": "03b2851f-fe58-47ec-9796-414ca0eb4742",
    "commodities": [
        "3d3b18e1-7f1e-46fb-be5a-2c7f743a16b9",
        "71399b6f-38cc-4101-8cbe-0dc880bc7b62"
    ],
    "requirements": [
        "767d7ec5-ec71-424b-8c7c-712b19bc5db7"
    ],
    "quantity_min": 100,
    "quantity_max": 500,
    "business_name": "Ravi Agro Pvt Ltd",
    "latitude": 19.076,
    "longitude": 72.877,
    "experience": 5
}
```

**Field reference:**

| Field | Type | Required | Notes |
|---|---|---|---|
| `name` | string | Yes | Display name |
| `role_id` | UUID | Yes | Must exist in `roles` table — see Section 3 |
| `commodities` | UUID[] | Yes | At least one; must exist in `commodities` table |
| `requirements` | UUID[] | Yes | At least one; must exist in `requirements` table |
| `quantity_min` | float | Yes | Minimum trade quantity in MT |
| `quantity_max` | float | Yes | Must be ≥ `quantity_min` |
| `business_name` | string | No | Optional business name |
| `latitude` | float | Yes | Business location latitude |
| `longitude` | float | Yes | Business location longitude |
| `experience` | int | No | Years of experience |

**Example (curl):**
```bash
curl -X POST http://localhost:8000/profile/ \
  -H "Authorization: Bearer <ONBOARDING_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Ravi Traders",
    "role_id": "03b2851f-fe58-47ec-9796-414ca0eb4742",
    "commodities": ["3d3b18e1-7f1e-46fb-be5a-2c7f743a16b9", "71399b6f-38cc-4101-8cbe-0dc880bc7b62"],
    "requirements": ["767d7ec5-ec71-424b-8c7c-712b19bc5db7"],
    "quantity_min": 100,
    "quantity_max": 500,
    "business_name": "Ravi Agro Pvt Ltd",
    "latitude": 19.076,
    "longitude": 72.877,
    "experience": 5
  }'
```

**Success `200`:**
```json
{
    "success": true,
    "message": "Profile created successfully",
    "data": {
        "id": "a1b2c3d4-...",
        "name": "Ravi Traders",
        "role_id": "03b2851f-fe58-47ec-9796-414ca0eb4742",
        "commodities": [
            { "id": "3d3b18e1-...", "name": "cotton" },
            { "id": "71399b6f-...", "name": "rice" }
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

**Error `409`** — profile already exists:
```json
{ "detail": "Profile already exists for this user" }
```

**Error `400`** — invalid IDs or quantity mismatch:
```json
{ "detail": "Invalid commodity_ids: 3d3b18e1-..." }
```

---

## 7. Profile APIs

All endpoints in this section require the **access token**.

---

### `GET /profile/me`

Fetch your own full profile.

**Example:**
```bash
curl http://localhost:8000/profile/me \
  -H "Authorization: Bearer <ACCESS_TOKEN>"
```

**Success `200`:**
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

### `PATCH /profile/`

Update your profile. All fields are optional — only send what you want to change.

**Request body (send only the fields you want to update):**
```json
{
    "name": "Ravi Global Traders",
    "commodities": ["1ca6216a-a369-45eb-a96e-cd6bda31fff2"],
    "quantity_min": 200,
    "quantity_max": 1000,
    "business_name": "Ravi Agro International",
    "latitude": 18.520,
    "longitude": 73.856,
    "experience": 7
}
```

**Commodity update behaviour:**
Commodities use a **diff-update** — pass the complete new list. Items not in the list are removed. Items already present are kept. New items are added.

**Example — update just the name:**
```bash
curl -X PATCH http://localhost:8000/profile/ \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{ "name": "Ravi Global Traders" }'
```

**Success `200`:**
```json
{
    "success": true,
    "message": "Profile updated successfully",
    "data": { ... }
}
```

---

### `DELETE /profile/`

Permanently delete your profile (hard delete — not reversible).

```bash
curl -X DELETE http://localhost:8000/profile/ \
  -H "Authorization: Bearer <ACCESS_TOKEN>"
```

**Success `200`:**
```json
{
    "success": true,
    "message": "Profile deleted successfully",
    "data": null
}
```

---

### `GET /profile/{profile_id}` — Public View

View any user's public profile. Returns post count but hides private fields.

**URL parameter:**

| Param | Type | Description |
|---|---|---|
| `profile_id` | UUID | The profile's UUID (from your `/me` response) |

**Example:**
```bash
curl http://localhost:8000/profile/a1b2c3d4-e5f6-... \
  -H "Authorization: Bearer <ACCESS_TOKEN>"
```

**Success `200`:**
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

---

### `GET /profile/my-posts`

Fetch your own posts (paginated).

**Query parameters:**

| Param | Default | Description |
|---|---|---|
| `limit` | 20 | Max results to return |
| `offset` | 0 | Skip N results (for pagination) |

```bash
curl "http://localhost:8000/profile/my-posts?limit=10&offset=0" \
  -H "Authorization: Bearer <ACCESS_TOKEN>"
```

---

### `GET /profile/saved`

Fetch your saved posts (paginated). Same pagination params as `my-posts`.

---

## 8. Database Schema

Tables created by the migration (`alembic upgrade head`):

```
users                  — auth identity (phone + country_code)
roles                  — trader / broker / exporter
profile                — main profile (linked 1:1 to user)
business               — business info + coordinates (1:1 with profile)
commodities            — cotton / rice / sugar / ...
profile_commodities    — profile ↔ commodity (many-to-many)
requirements           — license types
profile_requirements   — profile ↔ requirement (many-to-many)
document_types         — GST, PAN, APEDA ...
role_document_requirements — which docs each role needs
profile_documents      — uploaded docs per profile (with verification status)
posts                  — stub table (post module coming soon)
```

Run migrations:
```bash
alembic upgrade head
```

Check current migration state:
```bash
alembic current
```

---

## 9. Error Reference

| Status | When it happens |
|---|---|
| `400` | Invalid IDs (role/commodity/requirement not in DB), `quantity_min > quantity_max` |
| `401` | Missing, expired, or wrong token type (e.g. access token used where onboarding is expected) |
| `404` | User or profile not found |
| `409` | User already registered, or profile already exists for this user |
| `422` | Missing required field or wrong data type (FastAPI validation) |

All errors follow FastAPI's default shape:
```json
{
    "detail": "Human-readable description of what went wrong."
}
```

---

## Full Test Sequence (copy-paste order)

```bash
# 1. Start server
uvicorn main:app --reload

# 2. Seed lookup tables (run once)
python scripts/seed.py

# 3. Request OTP — watch the SERVER terminal for the 6-digit code
curl -X POST http://localhost:8000/auth/send-otp \
  -H "Content-Type: application/json" \
  -d '{ "phone_number": "9876543210", "country_code": "+91" }'

# 4. Verify OTP — copy the onboarding_token from the response
curl -X POST http://localhost:8000/auth/verify-otp \
  -H "Content-Type: application/json" \
  -d '{ "phone_number": "9876543210", "country_code": "+91", "otp_code": "<FROM_TERMINAL>" }'

# 5. Create user (paste ONBOARDING_TOKEN from step 4)
curl -X POST http://localhost:8000/profile/user \
  -H "Authorization: Bearer <ONBOARDING_TOKEN>"

# 6. Create profile (same ONBOARDING_TOKEN from step 4)
curl -X POST http://localhost:8000/profile/ \
  -H "Authorization: Bearer <ONBOARDING_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Ravi Traders",
    "role_id": "03b2851f-fe58-47ec-9796-414ca0eb4742",
    "commodities": ["3d3b18e1-7f1e-46fb-be5a-2c7f743a16b9"],
    "requirements": ["767d7ec5-ec71-424b-8c7c-712b19bc5db7"],
    "quantity_min": 100,
    "quantity_max": 500,
    "business_name": "Ravi Agro",
    "latitude": 19.076,
    "longitude": 72.877,
    "experience": 5
  }'

# NOTE: GET /profile/me, PATCH, DELETE also accept the onboarding token for now
# (access token will be issued by the auth developer later)

# 7. Fetch your profile
curl http://localhost:8000/profile/me \
  -H "Authorization: Bearer <ONBOARDING_TOKEN>"

# 8. Update name only
curl -X PATCH http://localhost:8000/profile/ \
  -H "Authorization: Bearer <ONBOARDING_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{ "name": "Ravi Global Traders" }'

# 9. Public profile view (replace with profile_id from step 7 response)
curl http://localhost:8000/profile/<PROFILE_ID> \
  -H "Authorization: Bearer <ONBOARDING_TOKEN>"

# 10. Delete
curl -X DELETE http://localhost:8000/profile/ \
  -H "Authorization: Bearer <ONBOARDING_TOKEN>"
```
