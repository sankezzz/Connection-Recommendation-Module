# Vanijyaa Backend — Frontend Gap Analysis

Compiled from full module-by-module UI review.  
Each gap is tagged: **[CRITICAL]** blocks a feature, **[IMPORTANT]** degrades UX, **[MINOR]** polish/nice-to-have.

---

## 1. Auth & Onboarding

### Confirmed Working
- Firebase ID token exchange → `POST /auth/firebase-verify` returns `onboarding_token` (new user) or `user_id + profile_id` (returning user)
- `POST /profile/user` creates user row (returns `user_id`)
- `POST /profile/` creates full profile covering screens 3–6 (role, name, commodities, interests, quantity, business, location)
- Partial onboarding (user row exists, no profile) → re-issues onboarding token correctly
- Location: frontend handles geocoding and sends `latitude` + `longitude` — backend accepts both as required fields

### Gaps

| # | Gap | Priority |
|---|-----|----------|
| 1 | `POST /profile/` response returns only `ProfileResponse`. Frontend has no explicit `user_id` or `profile_id` at the top level after onboarding. Frontend must extract `profile_id` from `data.profile.id` and already has `user_id` from `POST /profile/user`. Reshaping the response to include both at the top level would make integration unambiguous. | MINOR |
| 2 | Onboarding token expires in 15 minutes. If user is slow through screens 3–6, token expires and they restart from OTP. Consider extending to 30 minutes. | MINOR |

---

## 2. Profile Module

### Confirmed Working
- `GET /profile/me?user_id=` — fetch own profile
- `GET /profile/{profile_id}` — public profile view
- `PATCH /profile/?user_id=` — edit profile (name, business name, location)
- `DELETE /profile/user?user_id=` — delete account
- `GET /profile/avatar-upload-url` + `PATCH /profile/avatar` — avatar upload flow
- `POST /profile/verify` — submit verification documents
- Role is immutable in `ProfileUpdate` (not in the schema — correct, matches read-only UI)

### Gaps

| # | Gap | Priority |
|---|-----|----------|
| 1 | `ProfileResponse` (returned by `GET /profile/me`) has `followers_count` but **no `posts_count`**. Profile header shows both "20 Connections" and "20 Posts". `posts_count` must be added to `ProfileResponse`. | CRITICAL |
| 2 | `ProfilePublicResponse` (returned by `GET /profile/{id}`) has `posts_count` but **no `followers_count`**. Other users' profile headers also show both counts. `followers_count` must be added to `ProfilePublicResponse`. | CRITICAL |
| 3 | `GET /profile/me` does not return `phone_number` or `country_code`. Edit Profile screen shows Mobile Number as a read-only field. These fields live on the `User` model, not `Profile`. Endpoint must join and return them. | IMPORTANT |
| 4 | UI label says "Connections" but backend stores `followers_count`. Confirm whether "Connections" = followers (unidirectional) or mutual follows (bidirectional). If bidirectional, the counter logic and column name need updating. | IMPORTANT |
| 5 | Edit Profile UI only exposes: Name, Business Name, Business Location. `ProfileUpdate` schema also accepts `commodities`, `interests`, `quantity_min`, `quantity_max` — these are not editable anywhere in the current UI. Either add screens for them or remove from `ProfileUpdate` to keep the API honest. Decision required. | MINOR |

---

## 3. Connections & Recommendations Module

### Confirmed Working
- Follow / unfollow → `POST/DELETE /connections/{user_id}/follow/{target_id}`
- Follow status check → `GET /connections/{user_id}/follow/status/{target_id}`
- Filtered search (role, commodity, city, verified_only, pagination) → `GET /connections/{user_id}/search`
- Name/business prefix suggestions → `GET /connections/search/suggestions?q=`
- Vector-based recommendations → `GET /recommendations/{user_id}` (top-20, excludes already followed)
- Message request send / withdraw / accept / decline / inbox / sent → full CRUD on `MessageRequest`

### Gaps

| # | Gap | Priority |
|---|-----|----------|
| 1 | `_fmt_profile()` (used by search, suggestions, and recommendations responses) returns `latitude` + `longitude` but **not `city`/`state` text**, **not `avatar_url`**, and **not `profile_id`**. Every user card in the UI needs city text, avatar, and profile_id for navigation. | CRITICAL |
| 2 | `MessageRequest` model has no `message` field. The UI shows a 160-character text input on the message request screen ("Hi Sanket I came across your profile"). The recipient sees the request in their inbox with no intro text. Add `message: str` (max 160 chars) to `MessageRequest` model and `send_message_request()` service. | CRITICAL |
| 3 | **Mutual connections count** is shown on every connection card ("2 mutual connections", "8 mutual connections"). No calculation exists anywhere in the codebase. Requires a query: count of users followed by both `me` and `target`. | IMPORTANT |
| 4 | **"Did you mean" suggestions** on misspelled search ("xpotar" → "Exporters, Exporter, Export…"). Current `search_users` uses ILIKE — returns nothing on misspell. Needs pg_trgm trigram similarity or a fuzzy match layer. | IMPORTANT |
| 5 | **Recent searches** — UI shows a persistent list of recent people searched. No endpoint to store or retrieve search history (`POST /connections/{user_id}/search/history`, `GET`, `DELETE`). | IMPORTANT |
| 6 | **"Most active groups"** section on the Groups tab. `GET /api/v1/groups/suggestions/{user_id}` is vector-based (relevance). No endpoint ordered by member count or recent activity. Needs a separate `GET /api/v1/groups/most-active` or a sort param on suggestions. | IMPORTANT |
| 7 | **Group search** — Groups tab has a search bar. No `GET /api/v1/groups/search?q=` endpoint exists. | IMPORTANT |
| 8 | "Recommended for you" (horizontal scroll) and "People you may know" (vertical list) both appear in the Connections screen. Currently both would call `GET /recommendations/{user_id}`. Confirm if the frontend splits the top-N results into two sections, or if two separate calls with different limits are expected. | MINOR |

---

## 4. Posts Module

### Confirmed Working
- `POST /posts/upload-image` → `POST /posts/` — create post with image
- Deal/Requirement category with full detail fields (grain_type_size, qty_min/max, price_type)
- `Other` category with `other_description`
- `is_public` + `allow_comments` + `target_roles` visibility controls
- Like / save / share / view tracking
- Comment add / delete
- `GET /posts/` (all), `GET /posts/following`, `GET /posts/mine`, `GET /posts/saved`
- Unfollow / Block from 3-dot menu → existing connections / safety endpoints
- Share deeplink → `GET /share/post/{post_id}`

### Gaps

| # | Gap | Priority |
|---|-----|----------|
| 1 | **`title` field does not exist.** UI Create Post Step 1 has a separate "Title" field (60 chars) and "Body Text" (rich text). Backend has only `caption` (single text field). `Post` model needs a `title: str` column. `caption` stays as body text. `PostCreate`, `PostUpdate`, `PostResponse` all need updating. | CRITICAL |
| 2 | **Author info not in `PostResponse` or feed items.** Every post card shows avatar, name, role, business name. `PostResponse` only has `profile_id`. Frontend would need one profile API call per post in the feed. Embed `author_name`, `author_role`, `author_avatar_url`, `author_business_name`, `author_is_verified` directly in the response. | CRITICAL |
| 3 | **Feed category filter tabs don't exist.** UI shows tabs: All / Following / Discussions / (more). "Discussions" means `category_id=3`. No `?category_id=` filter param exists on `GET /posts/`. Add optional `category_id: int` query param. | CRITICAL |
| 4 | **Comment author info not in `CommentResponse`.** UI shows "Sanket Suryawanshi (Trader) · 5hrs ago" per comment. `CommentResponse` only has `profile_id`. Embed `author_name`, `author_role`, `author_avatar_url`. | CRITICAL |
| 5 | **Video upload not supported.** UI says "PNG, JPG, MP4, max 50MB". `get_post_upload_url` only accepts `image/jpeg | image/png | image/webp`. MP4 / video/mp4 content type is rejected. Supabase signed URL generation and allowed types need to include video. | IMPORTANT |
| 6 | **"Information source link" field missing.** Create Post Step 2 has a URL input field for citing a source. No `source_url: Optional[str]` field in `PostCreate` or `Post` model. | IMPORTANT |
| 7 | **Post location field missing.** Create Post Step 2 has a Location picker. No `city`, `state`, `latitude`, `longitude` fields on the `Post` model. | IMPORTANT |
| 8 | **Comment likes do not exist.** UI shows ❤️ 89 and ❤️ 156 on individual comments. `PostComment` has no `like_count`. No `PostCommentLike` table. No toggle-like-on-comment endpoint. | IMPORTANT |
| 9 | **Comment replies (threading) do not exist.** UI has a "Reply" button on each comment. `PostComment` has no `parent_id`. No nested reply structure. | IMPORTANT |
| 10 | **"Delete from feed" does not exist.** 3-dot menu option hides a post from the viewer's personal feed (not a full delete). No `PostHide` table or endpoint (`POST /posts/{id}/hide`). | MINOR |
| 11 | **Report reasons mismatch.** UI shows: Misleading/False Information, Offensive/Inappropriate Content, Fraud/Suspicious Activity, Spam/Irrelevant Content, Others. Backend `VALID_REASONS` = `spam \| harassment \| inappropriate_content \| scam \| impersonation \| other`. Labels and categories don't align. Reconcile both sides. | MINOR |

---

## 5. News Module

### Confirmed Working
- Article ingestion via Gemini (RSS → classify → store) — background APScheduler job
- `GET /news/feed?user_id=&scope=local|state|national|global` — returns `FeedResponse` with `FeedSection[]`
- `GET /news/search?q=&commodity=`
- `POST /news/{id}/like` + `POST /news/{id}/save` + `POST /news/{id}/share`
- `GET /news/saved?user_id=`
- `POST /news/{id}/comment` + `GET /news/{id}/comments`
- `POST /news/{id}/engage` — engagement signal recording
- Role-specific impact text: `trader_impact`, `broker_impact`, `exporter_impact` per article
- Taste profile + trending background jobs

### Gaps

| # | Gap | Priority |
|---|-----|----------|
| 1 | **Feed tab structure mismatch.** UI tabs: Trending, Global, Government, Domestic. Backend `scope` param: `local \| state \| national \| global`. "Government" and "Domestic" have no scope equivalent. "Trending" has a `NewsTrending` table (computed every 5 min) but no dedicated `GET /news/trending` endpoint. Tab → API mapping must be defined and endpoints created or scope values extended. | CRITICAL |
| 2 | **"Impact: Positive/Negative" badge convention undefined.** `NewsArticle` has `direction_tags: list[str]` (Gemini-generated). `ArticleOut` exposes it. But there is no documented convention for what string values mean "Positive" vs "Negative" vs "Neutral". The frontend cannot render the badge reliably without this being defined and consistently produced by the Gemini prompt. | CRITICAL |
| 3 | **`like_count` not stored on `NewsArticle`.** `ArticleOut` exposes `like_count: int = 0` but the column does not exist on the model. It must be aggregated from `NewsEngagement` rows at query time. On a busy feed this will be slow. Add a denormalized `like_count` counter column to `NewsArticle` (same pattern as the posts module). | IMPORTANT |
| 4 | **Comment author info missing.** `CommentOut` has `user_id` and `comment_text` only. News comments need the commenter's name and role for display, same as posts. | IMPORTANT |
| 5 | **"Quick Summary" bullet format undefined.** Card shows 3–4 bullet points under "Quick Summary". `ArticleOut.summary` is a plain `Text` field. Whether Gemini writes this as markdown bullets, newline-separated lines, or prose is not defined. The frontend rendering approach needs to be agreed with the Gemini prompt format. | MINOR |

---

## 6. Home Feed Module

### Confirmed Working
- `GET /feed/home?user_id=&cursor=` — cursor-paginated mixed feed
- 4 pipelines: posts (60 candidates), news (15), group activity (10, velocity-ranked), connection suggestions (3)
- Priority pins (breaking news) returned on first load with `is_priority: true`
- Static page-level weight mixing (heavier posts on page 1, more news/connections on deeper pages)
- `POST /feed/engagement` — batch engagement signal endpoint (acknowledged)
- Cursor advances correctly per item type

### Gaps

| # | Gap | Priority |
|---|-----|----------|
| 1 | **Post FeedItems missing author info.** `data` dict for `item_type="post"` has `profile_id` only. Every post card header needs `author_name`, `author_role`, `author_avatar_url`, `author_is_verified`, `author_business_name`. Without these the feed renders blank headers. | CRITICAL |
| 2 | **News FeedItems missing `direction_tags`.** News pipeline builds the `data` dict with `severity`, `cluster_id`, `role_impact` — but **omits `direction_tags`**. The "Impact: ● Negative/Positive" badge on every news card in the feed reads from this field. Badge cannot render. One-line fix: add `"direction_tags": a.direction_tags or []` to the news pipeline data dict. | CRITICAL |
| 3 | **Connection FeedItems missing `avatar_url`, commodity names, `city`/`state`, and mutual connections count.** The suggestion card shows all four. Pipeline returns only `user_id, profile_id, name, business_name, role_id, latitude, longitude`. | CRITICAL |
| 4 | **Group FeedItems missing `group_avatar_url`.** Group posts show a group header with an image/icon. `data` dict has `group_name` but no `group_avatar_url`. | IMPORTANT |
| 5 | **"Categories" filter tabs (All / Trending / Popular) have no backend support.** `GET /feed/home` takes no tab/category param. Switching tabs requires either a new query param or separate endpoints. | IMPORTANT |
| 6 | **"Search for places…" on home screen has no backend.** Appears to be a location context selector (user changes location to see regional content). No endpoint to update temporary location context for feed personalisation. | IMPORTANT |
| 7 | **Follow/Connect button state not in post FeedItems.** Post headers show "Follow" or "Connect" button. No `is_following` flag in the post FeedItem data. Frontend needs a separate per-author status call or bulk follow-status endpoint. | IMPORTANT |
| 8 | **Redis-dependent features are all disabled.** Three systems are commented out and non-functional: (a) seen-item deduplication — same posts/news reappear on each page load; (b) session taste — in-session engagement signals don't adjust weights; (c) engagement processing — `POST /feed/engagement` is a no-op. Feed works but has no personalisation feedback loop and infinite scroll shows duplicates. | IMPORTANT |

---

## 7. Chat Module

### Confirmed Working
- `GET /{user_id}/conversations` — list all conversations (DMs + groups)
- `POST /{user_id}/conversations` — open new DM (creates conversation in `status="requested"` + first message)
- `GET /{user_id}/conversations/{conv_id}/messages` — paginated message history (cursor via `before` timestamp)
- `POST /{user_id}/conversations/{conv_id}/messages` — send message (pushes to receiver via WebSocket immediately, persists in background)
- `POST /{user_id}/conversations/{conv_id}/accept` + `.../decline` — accept/reject chat request
- `POST /{user_id}/conversations/{conv_id}/read` — mark as read
- `GET/POST /{user_id}/groups/{group_id}/messages` — group chat
- All message types: `text | image | video | document | audio | location | system | post | news | user`
- Reply threading via `reply_to_id`
- Location share via `location_lat` + `location_lon`
- Block from chat → safety module endpoint
- Exit group → `DELETE /api/v1/groups/{group_id}/join`
- Create group from chat → `POST /api/v1/groups/` with `initial_member_ids`

### Gaps

| # | Gap | Priority |
|---|-----|----------|
| 1 | **Two conflicting chat request systems.** Connections module has `MessageRequest` table (`POST /connections/{user_id}/message-request/{target_id}`). Chat module has `Conversation.status="requested"` with its own accept/decline. These are **separate tables doing the same job**. The "Requests" tab in chat shows `Conversation` rows with `status="requested"`. The connections screen creates `MessageRequest` rows. A `MessageRequest` never becomes a `Conversation` — the two are disconnected. **Decision required:** either wire `MessageRequest` acceptance to create a `Conversation`, or deprecate `MessageRequest` and use only the `Conversation` request flow. | CRITICAL |
| 2 | **No filter params on `GET /{user_id}/conversations`.** UI has 4 tabs: All, DMs, Groups, Requests. No `?type=dm\|group` or `?status=requested` filter exists. Frontend must fetch all conversations and filter client-side, which breaks pagination and unread counts per tab. | CRITICAL |
| 3 | **Participant snap missing `avatar_url` and `role`.** `_snap()` returns `user_id, profile_id, name, is_verified`. Every conversation list row and open chat header shows avatar and role badge ("Exporter"). Both missing. `UserSnap` entity and `_snap()` serializer need to include them. | CRITICAL |
| 4 | **No clear chat endpoint.** "Clear chat" appears in the DM 3-dot menu and User Info screen. No endpoint to delete/hide all messages in a conversation for one user. Needs `POST /{user_id}/conversations/{conv_id}/clear` or `DELETE .../messages`. | IMPORTANT |
| 5 | **No search messages endpoint.** DM 3-dot menu has "Search message". No `GET /{user_id}/conversations/{conv_id}/messages/search?q=` exists. | IMPORTANT |
| 6 | **No conversation media list.** User Info screen shows "Media · 56" with a photo/video grid. No endpoint to list all media attachments shared in a conversation (`GET /{user_id}/conversations/{conv_id}/media`). `ChatAttachment` table exists but has no read endpoint. | IMPORTANT |
| 7 | **No online presence indicator.** User Info shows a green dot for online status. No heartbeat, no Redis-based `is_online` tracking, no presence field anywhere in the codebase. | IMPORTANT |
| 8 | **`OpenChatRequest` char limit mismatch.** First message limit in `OpenChatRequest` is 4000 chars. The connections module message request UI caps intro at 160 chars. Once gap #1 is resolved and both flows are unified, the first-message limit must be decided and applied consistently. | MINOR |

---

## Cross-Module Summary

| Module | Critical | Important | Minor |
|--------|----------|-----------|-------|
| Auth & Onboarding | 0 | 0 | 2 |
| Profile | 2 | 2 | 1 |
| Connections | 2 | 5 | 1 |
| Posts | 4 | 5 | 2 |
| News | 2 | 2 | 1 |
| Home Feed | 3 | 5 | 0 |
| Chat | 3 | 4 | 1 |
| **Total** | **16** | **23** | **8** |

---

## Suggested Fix Order

### Do first (unblock the UI from rendering at all)
1. Author embed in PostResponse + FeedItems (posts, connections)
2. `direction_tags` in news FeedItems (Impact badge)
3. `posts_count` in ProfileResponse + `followers_count` in ProfilePublicResponse
4. `avatar_url` + `role` in chat participant snap
5. Conversation filter params (All/DMs/Groups/Requests tabs)

### Do next (complete core features)
6. Chat request system unification (MessageRequest ↔ Conversation)
7. `MessageRequest.message` field (160-char intro)
8. `title` field on Post model
9. News feed tab structure + `GET /news/trending` endpoint
10. `_fmt_profile` add avatar_url, profile_id, city text
11. `phone_number` in `GET /profile/me`
12. Feed category filter tab param on `GET /posts/`
13. `like_count` counter on NewsArticle
14. Mutual connections count

### Defer (polish / phase 2)
15. Comment likes + replies
16. Video upload support
17. Source URL + post location fields
18. Group search + most active groups endpoint
19. Recent searches store/retrieve
20. Clear chat + search messages + media list endpoints
21. "Did you mean" fuzzy search
22. "Delete from feed" hide endpoint
23. Online presence
24. Report reasons alignment
25. Redis re-enable (seen-set, session taste, engagement processing)
