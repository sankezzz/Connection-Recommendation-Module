# Avatar Upload API

Handles profile picture uploads. Images are stored in Supabase Storage and the public URL is saved to the user's profile row.

---

## Endpoint

```
PATCH /profile/avatar
```

**No JWT required.** The acting user is identified by `user_id` as a query parameter.

---

## Request

### Query Parameters

| Parameter | Type   | Required | Description         |
|-----------|--------|----------|---------------------|
| `user_id` | UUID   | Yes      | The user's UUID     |

### Body — `multipart/form-data`

| Field    | Type | Required | Description                              |
|----------|------|----------|------------------------------------------|
| `avatar` | File | Yes      | Image file — `jpeg`, `png`, or `webp` only |

**Example (curl):**
```bash
curl -X PATCH "http://localhost:8000/profile/avatar?user_id=<user_id>" \
     -F "avatar=@/path/to/photo.webp;type=image/webp"
```

**Example (Python / httpx):**
```python
import httpx

with open("photo.webp", "rb") as f:
    resp = httpx.patch(
        "http://localhost:8000/profile/avatar",
        params={"user_id": "<user_id>"},
        files={"avatar": ("photo.webp", f, "image/webp")},
    )
print(resp.json())
```

---

## Response

### 200 OK

```json
{
  "status": "success",
  "message": "Avatar updated successfully",
  "data": {
    "avatar_url": "https://<project>.supabase.co/storage/v1/object/public/avatars/<user_id>.webp"
  }
}
```

### Error Responses

| Status | Cause                                                          |
|--------|----------------------------------------------------------------|
| `400`  | Unsupported image type (must be jpeg / png / webp)             |
| `400`  | Supabase storage upload failed (see `detail` for reason)       |
| `404`  | No profile found for the given `user_id`                       |
| `422`  | Missing `avatar` field or `user_id` query param                |

---

## How It Works (internals)

1. Validates the profile exists for `user_id`.
2. Checks `content_type` is one of `image/jpeg`, `image/png`, `image/webp`.
3. Derives the file extension from the original filename (falls back to `.jpg`).
4. Constructs the storage path: `{user_id}{ext}` — e.g. `e5f3b268-....webp`.
5. `POST`s the raw bytes to Supabase Storage with `x-upsert: true` (overwrites any previous avatar).
6. On success, saves the public URL to `profiles.avatar_url` and returns it.

**Storage path pattern:**
```
{SUPABASE_URL}/storage/v1/object/{SUPABASE_STORAGE_BUCKET}/{user_id}{ext}
```

**Public URL pattern (what is stored and returned):**
```
{SUPABASE_URL}/storage/v1/object/public/{SUPABASE_STORAGE_BUCKET}/{user_id}{ext}
```

---

## Environment Variables

| Variable                  | Required | Default    | Description                                      |
|---------------------------|----------|------------|--------------------------------------------------|
| `SUPABASE_URL`            | Yes      | —          | Your Supabase project URL (no trailing slash)    |
| `SUPABASE_SERVICE_KEY`    | Yes      | —          | **Service role** JWT — NOT the anon key          |
| `SUPABASE_STORAGE_BUCKET` | No       | `avatars`  | Storage bucket name                              |

> **Important:** `SUPABASE_SERVICE_KEY` must be the **service role** key from  
> Supabase Dashboard → Settings → API → `service_role` (secret).  
> Using the `anon` key will cause a `403 Invalid Compact JWS` error.

---

## Supabase Setup Checklist

- [ ] Storage bucket named `avatars` exists (or set `SUPABASE_STORAGE_BUCKET` to match your bucket name).
- [ ] Bucket is set to **Public** — Supabase Dashboard → Storage → `avatars` → Make Public.
- [ ] `SUPABASE_SERVICE_KEY` in `.env` is the full `service_role` JWT (`eyJ...` — long string, ~200+ chars).
- [ ] `SUPABASE_URL` does not have a trailing slash.

---

## Common Errors

### `400 Storage upload failed: {"statusCode":"403","error":"Unauthorized","message":"Invalid Compact JWS"}`

`SUPABASE_SERVICE_KEY` is wrong, truncated, or is the `anon` key.  
Fix: copy the `service_role` key from Supabase Dashboard → Settings → API and paste the full string into `.env`.

### `400 Unsupported image type`

The uploaded file's `Content-Type` is not `image/jpeg`, `image/png`, or `image/webp`.  
Fix: convert the file or set the correct MIME type when sending the request.

### `404 Profile not found`

No profile row exists for the given `user_id`.  
Fix: create a profile first via `POST /profile/`.

---

## Test Script

An interactive test script is provided at `TESTING/test_avatar_upload.py`. It runs three checks:

1. **Upload** — `PATCH /profile/avatar` and validates a 200 response.
2. **Supabase URL** — `GET`s the returned `avatar_url` and confirms the image is publicly accessible.
3. **DB check** — `GET /profile/me` and confirms `avatar_url` was persisted.

**Run interactively:**
```bash
py -m TESTING.test_avatar_upload
```

**Run with CLI args:**
```bash
py TESTING/test_avatar_upload.py \
  --base-url http://localhost:8000 \
  --user-id e5f3b268-86c6-475d-815f-9a8535a08593 \
  --image /path/to/photo.webp
```
