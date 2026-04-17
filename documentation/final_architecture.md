**VANIJYAA**

Production Architecture &

API Contracts

Clean Architecture · Database Schema · 93 API Endpoints · JSON Contracts

Recommendation Engines · Chat & WebSocket · Notifications · Background
Jobs

Flutter + Python/FastAPI · Modular Monolith · Trader · Broker · Exporter

Team: 3 Engineers · 4-Day Sprint

Version 4.0 (Final Merged) \| April 2026 \| Shri Balaji Global

Table of Contents

**PART A --- Architecture & Infrastructure**

1\. Clean Architecture --- Separation of Concerns

2\. Backend Architecture (Folder Structure & Layer Rules)

3\. Frontend Architecture (Flutter Folder Structure)

4\. Technology Stack

5\. Infrastructure & Deployment

6\. Response Envelope Standard

**PART B --- Database Schema (All Tables)**

7\. Core User Tables (users, profiles, documents, embeddings,
behavioral_scores)

8\. Social Graph (connections, follows, blocks, reports)

9\. Posts & Feed (posts, post_embeddings, comments, popular,
engagements, taste, hashtags)

10\. News (sources, articles, engagements, cluster_taste, trending)

11\. Groups (groups, embeddings, members, activity_cache, group_posts)

12\. Chat & Messaging (conversations, members, messages, attachments)

13\. Notifications (notifications, preferences)

14\. Configuration (role_configs, state_neighbours)

**PART C --- API Contracts (93 Endpoints with JSON)**

15\. Auth & User Creation (10 endpoints)

16\. Profile Management (11 endpoints)

17\. Connections & Recommendations (12 endpoints)

18\. Posts & Feed (16 endpoints)

19\. News (8 endpoints)

20\. Groups & Management (18 endpoints)

21\. Home Feed Orchestration (3 endpoints)

22\. Chat & Messaging with WebSocket (9 endpoints)

23\. Notifications (5 endpoints)

24\. Engagement Tracking (2 endpoints)

**PART D --- Recommendation Engine Internals**

25\. Vector Search (pgvector) --- User, Post, Group Embeddings

26\. Background Jobs & Cron Tasks (14 jobs)

27\. Redis Cache Architecture (12 key patterns)

28\. WebSocket Architecture (Chat Real-time)

**PART E --- Deployment & Sprint Plan**

29\. Production Server Setup

30\. Scaling Path

31\. CI/CD Pipeline

32\. Four-Day Sprint Board

33\. Complete API Summary Table (93 Endpoints)

**PART A --- Architecture & Infrastructure**

1\. Clean Architecture --- Separation of Concerns

Both backend and frontend follow the same three-layer pattern. Every
module respects these boundaries. This makes the codebase scalable,
testable, and easy to onboard new developers.

1.1 The Three Layers

  -------------- ------------------------------ -----------------------------
  **Layer**      **Backend (Python/FastAPI)**   **Frontend (Flutter)**

  Domain         Entities (pure Python          Entities (Dart classes),
                 classes), Repository           Repository interfaces
                 interfaces (abstract), Use     (abstract), Use cases
                 cases / Business logic, Value  (optional, can merge into
                 objects, Domain events         providers for speed)

  Data           Repository implementations,    Repository implementations,
                 SQLAlchemy models, API clients Dio API clients, Local
                 to external services,          storage (Hive), DTOs
                 pgvector/Meilisearch/Redis     (fromJson/toJson), Data
                 adapters, S3 storage adapter   source abstractions

  Presentation   FastAPI routers (controllers), Screens, Widgets, Riverpod
                 Pydantic schemas               providers (state management),
                 (request/response DTOs),       UI models / view states
                 Middleware, Dependency         
                 injection                      
  -------------- ------------------------------ -----------------------------

1.2 Dependency Direction

Dependencies flow inward. Presentation depends on Domain. Data depends
on Domain. Domain depends on nothing.

> Presentation ───▶ Domain ◀─── Data
>
> (routers/screens) (entities/use cases) (repos/DB/API)

Domain layer contains pure business logic with zero framework imports.
No SQLAlchemy in Domain. No Dio in Domain. No FastAPI in Domain. This
means you can change the database, API framework, or state management
without touching business logic.

1.3 How Layers Communicate

The Domain layer defines abstract repository interfaces. The Data layer
implements them. The Presentation layer receives them through dependency
injection.

> Backend: Router → Use Case → Repository Interface → Repository Impl →
> Database
>
> Frontend: Screen → Provider → Repository Interface → Repository Impl →
> Dio API Client

2\. Backend Architecture (Folder Structure & Layer Rules)

Every module follows the same internal structure. The core/ directory
contains shared infrastructure. The modules/ directory contains
feature-specific code, each with domain, data, and presentation layers.

2.1 Full Folder Structure

> vanijyaa-backend/
>
> ├── app/
>
> │ ├── main.py \# App factory, CORS, router registration
>
> │ ├── config.py \# Pydantic Settings (env-based)
>
> │ ├── container.py \# Dependency injection container
>
> │ │
>
> │ ├── core/ \# Shared infrastructure layer
>
> │ │ ├── database/engine.py \# Async SQLAlchemy engine + session
>
> │ │ ├── database/base_model.py \# Declarative base + ID/Timestamp
> mixins
>
> │ │ ├── database/migrations/ \# Alembic
>
> │ │ ├── security/jwt_handler.py \# JWT create / validate / refresh
>
> │ │ ├── security/hasher.py \# OTP / password hashing
>
> │ │ ├── security/rbac.py \# Role-based access control decorator
>
> │ │ ├── cache/redis_client.py \# Redis connection + helpers
>
> │ │ ├── storage/s3_client.py \# MinIO/S3 upload + signed URLs
>
> │ │ ├── search/meilisearch_client.py \# Meilisearch connection
>
> │ │ ├── vector/pgvector_client.py \# pgvector query helpers
>
> │ │ ├── events/event_bus.py \# In-process domain event bus
>
> │ │ ├── tasks/celery_app.py \# Celery config + base task
>
> │ │ └── exceptions.py \# Shared exception hierarchy
>
> │ │
>
> │ ├── modules/ \# Feature modules (each owns domain/data/presentation)
>
> │ │ ├── auth/ \# DEV B: OTP, JWT, role selection, onboarding
>
> │ │ ├── profile/ \# DEV B: CRUD, documents, verification
>
> │ │ ├── feed/ \# DEV B: Posts CRUD, vector store, popular posts
>
> │ │ ├── news/ \# DEV B: Ingestion, Gemini classification, scoring
>
> │ │ ├── home_feed/ \# DEV B: Priority queue, mixer, taste engine
>
> │ │ ├── connections/ \# DEV C: Search, recommendations, social graph
>
> │ │ ├── chat/ \# DEV C: DM, group chat, WebSocket handler
>
> │ │ ├── groups/ \# DEV C: CRUD, recommendations, permissions
>
> │ │ └── notifications/ \# DEV C: Push, in-app, preferences
>
> │ │
>
> │ └── shared/ \# Cross-cutting
>
> │ ├── schemas/ (pagination.py, envelope.py)
>
> │ ├── middleware/ (rate_limiter.py, audit_log.py, locale.py)
>
> │ └── utils/ (phone.py, sms.py, vector_math.py)
>
> │
>
> ├── tests/ (mirrors modules/ structure)
>
> ├── alembic.ini / pyproject.toml / Dockerfile
>
> ├── docker-compose.yml
>
> └── .env.example

2.2 Module Internal Pattern (Every Module)

> modules/\[name\]/
>
> ├── domain/ \# Pure business logic. No framework imports.
>
> │ ├── entities.py \# Dataclasses. Business rules. Validations.
>
> │ ├── repository.py \# Abstract base class (interface).
>
> │ └── use_cases.py \# One class per use case. Calls repository.
>
> ├── data/ \# Infrastructure. Implements domain interfaces.
>
> │ ├── models.py \# SQLAlchemy table models.
>
> │ ├── repository_impl.py \# Concrete repo.
>
> │ └── \[adapters\].py \# External service adapters (S3, pgvector,
> etc.)
>
> ├── presentation/ \# HTTP layer. Thin. No business logic.
>
> │ ├── router.py \# FastAPI route definitions.
>
> │ ├── schemas.py \# Pydantic DTOs (request/response shapes).
>
> │ └── dependencies.py \# Wire use cases + repos for DI.
>
> └── tasks.py \# Celery async tasks (optional)

2.3 Layer Rules

  --------------- ---------------------- ---------------------------------
  **Layer**       **File**               **Can Call**

  Router          router.py              Service/Use Case only

  Use Case        use_cases.py           Repository Interface, other Use
                                         Cases, Core

  Repository      repository_impl.py     Database, External APIs, Cache

  Model           models.py              Passive (called, never calls)

  Schema          schemas.py             Passive (Pydantic DTOs)
  --------------- ---------------------- ---------------------------------

3\. Frontend Architecture (Flutter)

3.1 Folder Structure

> vanijyaa_app/lib/
>
> ├── main.dart / app.dart
>
> ├── core/
>
> │ ├── network/ (dio_client.dart, api_endpoints.dart,
> api_response.dart)
>
> │ ├── auth/ (auth_state.dart, auth_notifier.dart, token_manager.dart,
> role_guard.dart)
>
> │ ├── storage/ (secure_storage.dart, local_cache.dart)
>
> │ ├── theme/ (app_theme.dart, app_colors.dart)
>
> │ ├── localization/ (l10n.dart, arb/)
>
> │ ├── router/ (app_router.dart)
>
> │ ├── utils/ (validators.dart, debouncer.dart, extensions.dart)
>
> │ └── widgets/ (v_button, v_text_field, v_loading, verified_badge,
> role_aware_widget)
>
> ├── features/
>
> │ ├── onboarding/ (domain/ data/ presentation/)
>
> │ ├── profile/ (domain/ data/ presentation/)
>
> │ ├── connections/ (domain/ data/ presentation/)
>
> │ ├── feed/ (domain/ data/ presentation/)
>
> │ ├── news/ (domain/ data/ presentation/)
>
> │ ├── chat/ (domain/ data/ presentation/)
>
> │ ├── groups/ (domain/ data/ presentation/)
>
> │ └── home/ (presentation only --- aggregator)
>
> └── shared/ (domain/entities, data/dto, providers/)

3.2 Navigation Architecture

> / (splash) ──\> checks auth state
>
> ├─ unauthenticated ─\> /login \> /otp \> /role-select \> /onboarding
>
> └─ authenticated ─\> /home (ShellRoute, bottom navigation)
>
> ├─ /home/feed
>
> ├─ /home/connections (/search, /user/:id, /group/:id)
>
> ├─ /home/news
>
> ├─ /home/chat (/dm/:id, /group/:id)
>
> └─ /home/profile (/edit, /settings, /saved)

3.3 State Management (Riverpod)

  ---------------- ----------------------------------- ----------------------------
  **State Type**   **Provider**                        **Example**

  Auth state       StateNotifierProvider               AuthNotifier --- user +
                                                       token + role

  API data         FutureProvider.autoDispose          profileProvider --- fetches
                                                       profile

  Search           StateNotifierProvider.autoDispose   SearchNotifier --- query +
                                                       results + filters

  Form state       StateProvider                       onboardingStepProvider ---
                                                       current step

  Role config      Provider (computed)                 roleConfigProvider ---
                                                       derives from role
  ---------------- ----------------------------------- ----------------------------

4\. Technology Stack

  ------------------ -------------------- ----------------------------------
  **Layer**          **Technology**       **Purpose**

  Backend Framework  Python 3.12+ /       Async API server, auto OpenAPI
                     FastAPI              docs, Pydantic validation

  ORM                SQLAlchemy 2.0 +     Async DB access, schema migrations
                     Alembic              

  Primary Database   PostgreSQL 16 +      All relational data + vector
                     pgvector             embeddings

  Cache & Sessions   Redis 7              Session taste, seen-posts, OTP,
                                          rate limiting, chat pub/sub

  Text Search        Meilisearch          Typo-tolerant fuzzy search for
                                          connections and news

  Task Queue         Celery + Redis       Background jobs: ingestion,
                                          popularity, shelf migration

  File Storage       MinIO (dev) / S3     KYC docs, photos, post media, chat
                     (prod)               attachments

  AI Classification  Google Gemini Flash  News article classification and
                     API                  tagging

  Push Notifications Firebase Cloud       Breaking news, chat notifications,
                     Messaging            trending

  SMS Gateway        MSG91 / Twilio       OTP delivery

  WebSocket          FastAPI WebSocket +  Real-time chat message delivery
                     Redis Pub/Sub        

  Reverse Proxy      Caddy / Nginx        SSL + WSS termination

  Containerization   Docker + Docker      All services containerized
                     Compose              

  CI/CD              GitHub Actions       Auto build, test, deploy on push

  Monitoring         Sentry +             Errors and performance
                     Prometheus/Grafana   
  ------------------ -------------------- ----------------------------------

5\. Infrastructure & Deployment

> Base URL (REST): https://api.vanijyaa.com
>
> WebSocket (Chat): wss://api.vanijyaa.com/ws/chat
>
> All REST APIs: https://api.vanijyaa.com/api/v1/{module}/{endpoint}

The Flutter Dio client calls these URLs. JWT in Authorization header for
REST. JWT as query param for WebSocket. From the Flutter side, calling
FastAPI is identical to calling a Firebase Cloud Function --- it is just
an HTTPS request that returns JSON.

6\. Response Envelope Standard

Every API response uses this consistent envelope so the Flutter client
has one parser.

> {
>
> \"success\": true,
>
> \"data\": { \... }, // Actual payload. null on error.
>
> \"message\": \"Profile updated successfully\",
>
> \"errors\": \[\], // Array of field-level errors on 422
>
> \"meta\": { // Only on paginated responses
>
> \"page\": 1,
>
> \"per_page\": 20,
>
> \"total\": 142,
>
> \"total_pages\": 8
>
> }
>
> }

All endpoints return this shape. Flutter parses the envelope first, then
the typed data inside.

**PART B --- Database Schema (All Tables)**

7\. Core User Tables

users

  ------------------ -------------------------------------------------------------------------- ------------------------------
  **Column**         **Type**                                                                   **Notes**

  id                 UUID PRIMARY KEY                                                           gen_random_uuid()

  phone              VARCHAR(15) UNIQUE NOT NULL                                                OTP login

  role               ENUM(trader,broker,exporter)                                               From onboarding

  onboarding_state   ENUM(phone_verified,role_selected,details_filled,docs_uploaded,verified)   Progress tracking

  app_language       VARCHAR(5) DEFAULT \'en\'                                                  en, hi, mr

  is_active          BOOLEAN DEFAULT true                                                       Soft delete

  last_active_at     TIMESTAMP                                                                  Throttled 1/min

  fcm_token          VARCHAR(500)                                                               Push notification token

  created_at         TIMESTAMP                                                                  

  updated_at         TIMESTAMP                                                                  
  ------------------ -------------------------------------------------------------------------- ------------------------------

profiles

  ------------------ ---------------------------------------------- -----------------------------------------
  **Column**         **Type**                                       **Notes**

  id                 UUID PRIMARY KEY                               

  user_id            UUID FK UNIQUE                                 One-to-one

  name               VARCHAR(100)                                   

  business_name      VARCHAR(200)                                   

  commodities        JSONB                                          \[\'sugar\',\'rice\',\'cotton\'\]

  regions            JSONB                                          \[\'maharashtra\'\]

  city               VARCHAR(100)                                   

  state              VARCHAR(100)                                   

  latitude           FLOAT                                          Geo matching

  longitude          FLOAT                                          Geo matching

  qty_min_mt         FLOAT                                          Min trade quantity (MT)

  qty_max_mt         FLOAT                                          Max trade quantity (MT)

  trade_scope        ENUM(local,regional,national,international)    News personalisation

  what_looking_for   JSONB                                          \[\'connections\',\'staying_updated\'\]

  photo_url          VARCHAR(500)                                   S3 path

  experience         INTEGER                                        Years

  kyc_status         ENUM(pending,submitted,verified,rejected)      

  gst_status         ENUM(pending,submitted,verified,rejected,na)   

  iec_status         ENUM(pending,submitted,verified,rejected,na)   Exporters only
  ------------------ ---------------------------------------------- -----------------------------------------

documents

  ------------------ --------------------------------------------- ------------------------------
  **Column**         **Type**                                      **Notes**

  id                 UUID PRIMARY KEY                              

  user_id            UUID FK                                       

  doc_type           ENUM(kyc,gst,iec,other)                       

  file_url           VARCHAR(500)                                  S3 signed URL

  status             ENUM(uploaded,processing,verified,rejected)   

  rejection_reason   TEXT                                          

  created_at         TIMESTAMP                                     
  ------------------ --------------------------------------------- ------------------------------

user_embeddings

  ---------------------- ---------------------- -------------------------
  **Column**             **Type**               **Notes**

  user_id                UUID PK FK             One-to-one

  is_vector              VECTOR(11)             IS embedding: 3
                                                commodity + 3 role + 3
                                                geo + 2 qty

  updated_at             TIMESTAMP              
  ---------------------- ---------------------- -------------------------

> CREATE INDEX idx_user_embed ON user_embeddings USING hnsw (is_vector
> vector_cosine_ops) WITH (m=16, ef_construction=100);

user_behavioral_scores

  ---------------------- ---------------------- -------------------------
  **Column**             **Type**               **Notes**

  user_id                UUID PK FK             

  follower_count         INTEGER DEFAULT 0      

  engagement_score       FLOAT DEFAULT 0        ln(1+x)/ln(1+max)

  screentime_score       FLOAT DEFAULT 0        

  last_active_at         TIMESTAMP              Recency decay

  updated_at             TIMESTAMP              
  ---------------------- ---------------------- -------------------------

8\. Social Graph Tables

connections

  ---------------- ----------------------------------------- ------------------------------
  **Column**       **Type**                                  **Notes**

  id               UUID PK                                   

  requester_id     UUID FK                                   Sender

  receiver_id      UUID FK                                   Receiver

  status           ENUM(pending,accepted,rejected,blocked)   

  note             TEXT                                      Message with request

  created_at       TIMESTAMP                                 
  ---------------- ----------------------------------------- ------------------------------

> UNIQUE(requester_id, receiver_id)

follows

  ---------------------- ------------------------ -----------------------
  **Column**             **Type**                 **Notes**

  follower_id            UUID FK                  

  following_id           UUID FK                  

  created_at             TIMESTAMP                
  ---------------------- ------------------------ -----------------------

> PRIMARY KEY (follower_id, following_id)

blocks

  ---------------- ------------------------ ------------------------------
  **Column**       **Type**                 **Notes**

  id               UUID PK                  

  blocker_id       UUID FK                  

  blocked_id       UUID FK                  

  reason           TEXT                     

  created_at       TIMESTAMP                
  ---------------- ------------------------ ------------------------------

reports

  ---------------- ---------------------------------------------------------- ------------------------------
  **Column**       **Type**                                                   **Notes**

  id               UUID PK                                                    

  reporter_id      UUID FK                                                    

  target_type      ENUM(user,post,comment,group,message)                      

  target_id        UUID                                                       

  reason           ENUM(spam,harassment,misinformation,inappropriate,other)   

  details          TEXT                                                       

  status           ENUM(pending,reviewed,action_taken,dismissed)              

  created_at       TIMESTAMP                                                  
  ---------------- ---------------------------------------------------------- ------------------------------

9\. Posts & Feed Tables

posts

Full post table with all fields from user flow: category, commodity,
quality specs, visibility controls, hashtags, accuracy confirmation.

  -------------------- --------------------------------------------------- ------------------------------
  **Column**           **Type**                                            **Notes**

  id                   UUID PK                                             

  author_id            UUID FK                                             

  category             ENUM(deal_req,market_update,knowledge,discussion)   

  commodity            VARCHAR(50)                                         

  commodity_subtype    VARCHAR(100)                                        Basmati/Non-Basmati

  title                TEXT                                                

  body                 TEXT                                                

  media_urls           JSONB                                               S3 paths

  target_roles         JSONB                                               \[\'trader\',\'broker\'\] or
                                                                           \[\'all\'\]

  qty_min_mt           FLOAT                                               deal_req only

  qty_max_mt           FLOAT                                               deal_req only

  price_type           ENUM(fixed,negotiable)                              deal_req

  grain_type           VARCHAR(100)                                        Quality spec

  quality_specs        JSONB                                               {broken_pct, moisture_pct,
                                                                           color, crop_year}

  source_ref_link      VARCHAR(500)                                        External ref

  hashtags             JSONB                                               \[\'#riceexport\'\]

  city                 VARCHAR(100)                                        

  state                VARCHAR(100)                                        

  latitude             FLOAT                                               

  longitude            FLOAT                                               

  visibility           ENUM(public,my_connections,select_groups)           

  visible_group_ids    JSONB                                               Group UUIDs if select_groups

  allow_comments       BOOLEAN DEFAULT true                                

  accuracy_confirmed   BOOLEAN DEFAULT false                               Required true to publish

  is_active            BOOLEAN DEFAULT true                                

  expires_at           TIMESTAMP                                           Category-based

  partition            ENUM(hot,warm,cold)                                 

  like_count           INTEGER DEFAULT 0                                   

  comment_count        INTEGER DEFAULT 0                                   

  save_count           INTEGER DEFAULT 0                                   

  share_count          INTEGER DEFAULT 0                                   

  created_at           TIMESTAMP                                           

  updated_at           TIMESTAMP                                           
  -------------------- --------------------------------------------------- ------------------------------

post_embeddings

  ---------------------- ------------------------ -----------------------
  **Column**             **Type**                 **Notes**

  post_id                UUID PK FK               

  embedding              VECTOR(18)               18-dim post vector

  partition              ENUM(hot,warm,cold)      

  created_at             TIMESTAMP                
  ---------------------- ------------------------ -----------------------

> Partial HNSW indexes per partition: WHERE partition = \'hot\',
> \'warm\', \'cold\'

Also includes:

-   post_comments --- id, post_id, author_id, body, parent_comment_id,
    is_deleted, created_at

-   popular_posts --- post_id, commodity, velocity_score,
    last_calculated_at

-   post_engagements --- id, user_id, post_id, action, dwell_ms,
    created_at

-   user_post_taste --- user_id, deal_req_score, market_update_score,
    knowledge_score, discussion_score, interactions_count

-   hashtags --- id, tag (unique), usage_count, created_at

10\. News Tables

-   news_sources --- id, name, source_type, credibility_weight,
    feed_url, is_active

-   news_articles --- id, source_id, external_url, title,
    summary_oneliner, summary_bullets, cluster_id (1-10), severity,
    commodities, scope, regions, direction_tags, horizon, story_id,
    image_url, published_at, ingested_at, is_active

-   news_engagements --- id, user_id, article_id, action, dwell_ms,
    created_at

-   user_cluster_taste --- (user_id, cluster_id) PK, taste_score,
    interaction_count, updated_at

-   trending_articles --- (article_id, segment_role, segment_commodity,
    segment_state) PK, velocity_score, unique_users, calculated_at

Indexes: published_at DESC, GIN on commodities, btree on cluster_id and
story_id.

11\. Groups Tables

-   groups --- id, name, description, group_rules, icon_url, commodity
    (JSONB), target_roles, region_lat/lon, region_market, category,
    accessibility, posting_perm, chat_perm, invite_link_token,
    created_by, member_count, created_at

-   group_embeddings --- group_id PK, embedding VECTOR(11), updated_at

-   group_members --- (group_id, user_id) PK, role (admin/member),
    is_frozen, is_muted, is_favorite, joined_at

-   group_activity_cache --- group_id PK, messages_24h,
    unique_senders_24h, active_members_7d, member_growth_7d, updated_at

-   group_posts --- id, group_id, author_id, body, media_urls, likes,
    comments, saves, created_at

12\. Chat & Messaging Tables

conversations

  ---------------- ------------------------ ------------------------------
  **Column**       **Type**                 **Notes**

  id               UUID PK                  

  type             ENUM(dm)                 Future: channel

  created_at       TIMESTAMP                

  updated_at       TIMESTAMP                Updated on new message
  ---------------- ------------------------ ------------------------------

conversation_members

  ------------------ ---------------------- ------------------------------
  **Column**         **Type**               **Notes**

  conversation_id    UUID FK                

  user_id            UUID FK                

  last_read_at       TIMESTAMP              Unread count calc

  is_muted           BOOLEAN DEFAULT false  

  joined_at          TIMESTAMP              
  ------------------ ---------------------- ------------------------------

> PRIMARY KEY (conversation_id, user_id)

messages

  ---------------- ------------------------------------------------------- ------------------------------
  **Column**       **Type**                                                **Notes**

  id               UUID PK                                                 

  context_type     ENUM(dm,group)                                          DM or group message

  context_id       UUID                                                    conversations.id or groups.id

  sender_id        UUID FK                                                 

  message_type     ENUM(text,image,video,document,audio,location,system)   

  body             TEXT                                                    

  media_url        VARCHAR(500)                                            S3 path

  media_metadata   JSONB                                                   {filename, size_bytes,
                                                                           duration_sec, mime_type}

  location_lat     FLOAT                                                   

  location_lon     FLOAT                                                   

  reply_to_id      UUID FK nullable                                        Quoted reply

  is_deleted       BOOLEAN DEFAULT false                                   

  created_at       TIMESTAMP                                               
  ---------------- ------------------------------------------------------- ------------------------------

> INDEX idx_messages_context ON messages (context_type, context_id,
> created_at DESC);

chat_attachments

For \'Shared Media\' gallery view. Mirrors messages but indexed for
media-type queries.

  ---------------- ---------------------------------- ------------------------------
  **Column**       **Type**                           **Notes**

  id               UUID PK                            

  message_id       UUID FK                            

  context_type     ENUM(dm,group)                     

  context_id       UUID                               

  media_type       ENUM(image,video,document,audio)   

  media_url        VARCHAR(500)                       

  created_at       TIMESTAMP                          
  ---------------- ---------------------------------- ------------------------------

13\. Notifications Tables

notifications

  ---------------- --------------------------------------------------------------------------------------------------------------------------------------------- ------------------------------
  **Column**       **Type**                                                                                                                                      **Notes**

  id               UUID PK                                                                                                                                       

  user_id          UUID FK                                                                                                                                       Recipient

  type             ENUM(connection_request,connection_accepted,post_like,post_comment,news_breaking,news_trending,group_invite,group_post,chat_message,system)   

  title            VARCHAR(200)                                                                                                                                  

  body             TEXT                                                                                                                                          

  actor_id         UUID FK nullable                                                                                                                              Who triggered it

  target_type      ENUM(post,news,user,group,conversation)                                                                                                       Navigate to

  target_id        UUID                                                                                                                                          

  is_read          BOOLEAN DEFAULT false                                                                                                                         

  is_push_sent     BOOLEAN DEFAULT false                                                                                                                         

  created_at       TIMESTAMP                                                                                                                                     
  ---------------- --------------------------------------------------------------------------------------------------------------------------------------------- ------------------------------

notification_preferences

  --------------------- ---------------------- ---------------------------
  **Column**            **Type**               **Notes**

  user_id               UUID PK FK             

  push_enabled          BOOLEAN DEFAULT true   Master toggle

  push_chat             BOOLEAN DEFAULT true   

  push_connections      BOOLEAN DEFAULT true   

  push_news             BOOLEAN DEFAULT true   

  push_quiet_start      TIME DEFAULT \'21:00\' 

  push_quiet_end        TIME DEFAULT \'05:00\' 

  updated_at            TIMESTAMP              
  --------------------- ---------------------- ---------------------------

14\. Configuration Tables

-   role_configs --- role PK, feed_weights (JSONB), news_cluster_weights
    (JSONB), connection_role_weights, search_boost_roles,
    visible_features, required_verifications

-   state_neighbours --- state, neighbour_state (for geographic
    expansion in news and trending)

**PART C --- API Contracts (93 Endpoints)**

Base URL: /api/v1 \| Auth: Bearer JWT \| Content-Type: application/json
(except file uploads: multipart/form-data)

All responses use the envelope format from Section 6. Status codes:
200/201 success, 401 unauthorized, 404 not found, 409 conflict, 422
validation error, 429 rate limited.

15\. Auth & User Creation (10 Endpoints)

Complete onboarding: Splash → Language → Login → OTP → Role → Details →
Documents → Home.

POST /api/v1/auth/otp/send

Send OTP. Rate limited: 5/phone/hour.

> Request: { \"phone\": \"+919876543210\" }
>
> Response: { \"success\": true, \"data\": { \"request_id\":
> \"otp_req_abc123\",
>
> \"expires_in\": 300, \"retry_after\": 30 } }
>
> Status: 200 OK, 429 Rate Limited, 422 Invalid Phone

POST /api/v1/auth/otp/verify

Verify OTP. Creates user if new. Returns JWT tokens.

> Request: { \"phone\": \"+919876543210\", \"otp\": \"123456\",
> \"request_id\": \"otp_req_abc123\" }
>
> Response: { \"success\": true, \"data\": {
>
> \"access_token\": \"eyJhbG\...\", \"refresh_token\": \"eyJhbG\...\",
>
> \"token_type\": \"bearer\", \"expires_in\": 900,
>
> \"user\": { \"id\": \"uuid\", \"phone\": \"+91\...\", \"role\": null,
>
> \"onboarding_state\": \"phone_verified\", \"is_new_user\": true } } }
>
> Status: 200 OK, 401 Invalid OTP, 410 Expired, 429 Max Attempts

POST /api/v1/auth/token/refresh

> Request: { \"refresh_token\": \"eyJhbG\...\" }
>
> Response: { \"data\": { \"access_token\": \"\...\", \"refresh_token\":
> \"\...\", \"expires_in\": 900 } }

PUT /api/v1/auth/language

> Request: { \"language\": \"hi\" } // en \| hi \| mr

PUT /api/v1/auth/role

Set role. Seeds user_cluster_taste + user_post_taste with role defaults.

> Request: { \"role\": \"trader\" }
>
> Response: { \"data\": { \"user\": { \"id\": \"\...\", \"role\":
> \"trader\", \"onboarding_state\": \"role_selected\" } } }
>
> Status: 200 OK, 409 Role Already Set

PUT /api/v1/auth/onboarding

Submit profile details. Builds user embedding, indexes in Meilisearch.

> Request: { \"name\": \"Rajesh Kumar\", \"business_name\": \"Kumar
> Trading Co.\",
>
> \"experience_years\": 12, \"commodities\": \[\"sugar\",\"rice\"\],
>
> \"regions\": \[\"maharashtra\",\"gujarat\"\], \"city\": \"Pune\",
> \"state\": \"maharashtra\",
>
> \"qty_min_mt\": 100, \"qty_max_mt\": 500,
>
> \"what_looking_for\": \[\"connections\",\"staying_updated\"\] }
>
> Response: { \"data\": { \"user\": { \"onboarding_state\":
> \"details_filled\" },
>
> \"profile\": { \"id\": \"\...\", \"name\": \"Rajesh Kumar\", \... } }
> }

POST /api/v1/auth/onboarding/documents

Upload KYC/GST/IEC. Multipart form: file + doc_type.

> Response: { \"data\": { \"id\": \"uuid\", \"doc_type\": \"kyc\",
> \"file_url\": \"s3://\...\", \"status\": \"uploaded\" } }

POST /api/v1/auth/onboarding/skip-docs

User taps Skip/Do it later.

POST /api/v1/auth/fcm-token

> Request: { \"fcm_token\": \"firebase_token\" }

POST /api/v1/auth/logout

> Response: { \"success\": true, \"message\": \"Logged out\" }

16\. Profile Management (11 Endpoints)

GET /api/v1/profile/me

> Response: { \"data\": { \"id\": \"uuid\", \"user_id\": \"uuid\",
> \"name\": \"Rajesh Kumar\",
>
> \"business_name\": \"Kumar Trading Co.\", \"experience_years\": 12,
>
> \"photo_url\": \"s3://\...\", \"commodities\": \[\"sugar\",\"rice\"\],
>
> \"regions\": \[\"maharashtra\"\], \"role\": \"trader\",
>
> \"verification\": { \"kyc\": {\"status\":\"verified\"}, \"gst\":
> {\"status\":\"pending\"}, \"iec\": {\"status\":\"na\"} },
>
> \"stats\": { \"connections_count\": 45, \"posts_count\": 12,
> \"groups_count\": 3 } } }

GET /api/v1/profile/:id

Public profile. Includes connection_status for Flutter action button
logic.

> Response: { \"data\": { \"name\": \"Anita Shah\", \"role\":
> \"exporter\",
>
> \"commodities\": \[\"cotton\"\], \"is_verified\": true,
>
> \"connection_status\": \"connected\", // none \| pending \| connected
> \| blocked
>
> \"is_following\": true,
>
> \"stats\": { \"connections_count\": 120, \"posts_count\": 34 },
>
> \"recent_posts\": \[{ \"id\", \"title\", \"category\", \"created_at\"
> }\] } }

PATCH /api/v1/profile

Auto-save. Send only changed fields. Rebuilds embedding if
commodity/location/qty changed.

> Request: { \"name\": \"Rajesh Kumar\", \"commodities\":
> \[\"sugar\",\"rice\",\"cotton\"\] }

PATCH /api/v1/profile/photo

Multipart upload.

POST /api/v1/profile/documents \| POST /api/v1/profile/verify/:type

GET /api/v1/profile/saved

> Query: ?type=post\|news\|all&page=1&per_page=20

GET /api/v1/profile/my-posts

PUT /api/v1/profile/language

> Request: { \"language\": \"mr\" }

POST /api/v1/profile/invite

> Request: { \"method\": \"whatsapp\"\|\"sms\"\|\"copy_link\",
> \"phone\": \"+91\...\" }
>
> Response: { \"data\": { \"invite_link\":
> \"https://vanijyaa.com/invite/abc\" } }

DELETE /api/v1/profile

> Response: { \"message\": \"Account scheduled for deletion\" }

17\. Connections & Recommendations (12 Endpoints)

GET /api/v1/connections/suggestions

Vector-based recs. pgvector HNSW + behavioral reranking.

> Response: { \"data\": \[{ \"user\": {
> \"id\",\"name\",\"role\",\"commodities\",\"photo_url\",\"is_verified\"
> },
>
> \"match_score\": 0.87, \"match_reasons\": \[\"Same
> commodities\",\"Nearby region\",\"Complementary role\"\] }\] }

GET /api/v1/connections

> Query: ?page=1&per_page=20
>
> Response: { \"data\": \[{ \"connection_id\", \"user\": {
> \"id\",\"name\",\"role\",\"photo_url\",\"is_verified\" },
>
> \"connected_at\": \"\...\" }\], \"meta\": { \"page\":1, \"total\":45 }
> }

GET /api/v1/connections/search

> Query:
> ?q=sugar+exporter&role=exporter&commodity=sugar&location=maharashtra&verified_only=true

GET /api/v1/connections/requests

> Query: ?direction=received\|sent

POST /api/v1/connections/request

> Request: { \"receiver_id\": \"uuid\", \"note\": \"Hi, I trade sugar in
> Maharashtra\...\" }
>
> Response: { \"data\": { \"request_id\": \"uuid\", \"status\":
> \"pending\" } }
>
> Status: 201 Created, 409 Already Pending/Connected, 403 User Blocked
> You

PUT /api/v1/connections/request/:id

> Request: { \"action\": \"accept\" \| \"reject\" }

DELETE /api/v1/connections/:id

POST /api/v1/connections/block

> Request: { \"user_id\": \"uuid\", \"reason\": \"spam\" }

POST /api/v1/connections/:uid/follow \| DELETE
/api/v1/connections/:uid/follow

POST /api/v1/report

> Request: { \"target_type\":
> \"user\"\|\"post\"\|\"comment\"\|\"group\"\|\"message\",
>
> \"target_id\": \"uuid\", \"reason\": \"spam\", \"details\": \"\...\" }

18\. Posts & Feed (16 Endpoints)

GET /api/v1/feed/posts

Personalised For You feed. Full recommendation pipeline.

> Query: ?category=&commodity=&page=1&per_page=25
>
> Response: { \"data\": \[{ \"id\", \"author\": {
> \"id\",\"name\",\"role\",\"photo_url\",\"is_verified\" },
>
> \"category\": \"deal_req\", \"commodity\": \"rice\", \"content\":
> \"\...\",
>
> \"media_urls\": \[\"s3://\...\"\], \"target_roles\": \[\"trader\"\],
>
> \"location\": { \"city\": \"Pune\", \"state\": \"maharashtra\" },
>
> \"engagement\": { \"likes\": 24, \"comments\": 8, \"saves\": 3,
> \"shares\": 2 },
>
> \"user_interaction\": { \"liked\": false, \"saved\": true },
>
> \"created_at\": \"\...\", \"expires_at\": \"\...\" }\], \"meta\":
> {\...} }

GET /api/v1/feed/following

POST /api/v1/feed/posts

> Request: { \"category\": \"deal_req\", \"commodity\": \"rice\",
>
> \"content\": \"Looking for 500MT basmati rice\...\", \"media_urls\":
> \[\],
>
> \"target_roles\": \[\"trader\",\"exporter\"\],
>
> \"location\": { \"city\": \"Delhi\", \"state\": \"delhi\", \"lat\":
> 28.6, \"lon\": 77.2 },
>
> \"deal_details\": { \"quantity_min\": 200, \"quantity_max\": 500,
> \"unit\": \"MT\",
>
> \"price_type\": \"negotiable\", \"grain_type\": \"Long\",
>
> \"quality_specs\": { \"broken_pct\": 5, \"moisture_pct\": 12,
> \"color\": \"White\" } },
>
> \"source_ref_link\": \"https://\...\", \"hashtags\":
> \[\"#riceexport\"\],
>
> \"visibility\": \"public\", \"allow_comments\": true,
> \"accuracy_confirmed\": true }
>
> Response: { \"data\": { \"id\": \"uuid\", \...full post\... },
> \"message\": \"Post published\" }

PATCH /api/v1/feed/posts/:id \| DELETE /api/v1/feed/posts/:id \| GET
/api/v1/feed/posts/:id

POST /api/v1/feed/posts/:id/like (toggle)

> Response: { \"data\": { \"liked\": true, \"total_likes\": 25 } }

POST /api/v1/feed/posts/:id/comment

> Request: { \"content\": \"Interested! DM me for details.\" }

POST /api/v1/feed/posts/:id/save (toggle) \| POST
/api/v1/feed/posts/:id/share

GET /api/v1/feed/posts/:id/comments \| DELETE
/api/v1/feed/posts/:id/comments/:cid

GET /api/v1/hashtags/search \| GET /api/v1/hashtags/:tag/posts

POST /api/v1/feed/engagement

Batch engagement signals for session taste engine.

> Request: { \"session_id\": \"sess_abc\", \"signals\": \[
>
> { \"item_id\": \"uuid\", \"item_type\": \"post\", \"signal\":
> \"dwell\", \"duration_ms\": 6200 },
>
> { \"item_id\": \"uuid\", \"item_type\": \"news\", \"signal\":
> \"skip\", \"duration_ms\": 800 },
>
> { \"item_id\": \"uuid\", \"item_type\": \"post\", \"signal\": \"save\"
> } \] }

19\. News (8 Endpoints)

GET /api/v1/news

Personalised news feed. Five sections or flat list with filter.

> Query:
> ?commodity=sugar&horizon=act_today&sort=trending\|latest\|most_shared&filter=breaking\|government&page=1
>
> Response: { \"data\": \[{ \"id\", \"title\": \"India halts non-basmati
> rice exports\",
>
> \"source\": { \"name\": \"PIB\", \"credibility\": 1.3 }, \"url\":
> \"https://\...\",
>
> \"summary\": \"\...\", \"bullet_points\": \[\"\...\", \"\...\",
> \"\...\"\],
>
> \"severity\": 9.5, \"commodities\": \[\"rice\"\],
>
> \"impact\": { \"trader\": \"high\", \"direction\":
> \"bullish_domestic_bearish_export\" },
>
> \"horizon\": \"act_today\",
>
> \"engagement\": { \"likes\": 45, \"comments\": 12, \"saves\": 20 },
>
> \"user_interaction\": { \"liked\": false, \"saved\": false },
>
> \"published_at\": \"\...\" }\], \"meta\": {\...} }

GET /api/v1/news/:id

Full article with comments, direction arrow per role, why_seeing_this.

GET /api/v1/news/search

> Query: ?q=export+ban&commodity=rice&sort_by=most_shared

POST /api/v1/news/:id/like \| /save \| /share \| /comment

GET /api/v1/news/:id/comments

20\. Groups & Management (18 Endpoints)

GET /api/v1/groups/suggestions

> Response: { \"data\": \[{ \...group\..., \"match_score\": 0.91,
>
> \"match_reasons\": \[\"Matches your commodities\",\"Active
> community\"\] }\] }

GET /api/v1/groups

> Query: ?commodity=&role=&accessibility=public&page=&per_page=

POST /api/v1/groups

> Request: { \"name\": \"Sugar Traders Maharashtra\", \"description\":
> \"\...\",
>
> \"group_rules\": \"No spam.\", \"primary_commodity\": \"sugar\",
> \"region\": \"maharashtra\",
>
> \"accessibility\": \"public\", \"posting_perm\": \"all_members\",
> \"chat_perm\": \"all_members\",
>
> \"role_targeting\": \[\"trader\",\"broker\"\], \"initial_member_ids\":
> \[\"uuid1\",\"uuid2\"\] }

GET /api/v1/groups/:id \| PATCH /api/v1/groups/:id \| PATCH
/api/v1/groups/:id/permissions

POST /api/v1/groups/:id/join \| DELETE /api/v1/groups/:id/leave

> Join response: { \"data\": { \"role\": \"member\", \"joined_at\":
> \"\...\" } }

GET /api/v1/groups/:id/members \| POST /api/v1/groups/:id/members/add \|
DELETE /api/v1/groups/:id/members/:uid

POST /api/v1/groups/:id/members/:uid/freeze \| DELETE \.../freeze

POST /api/v1/groups/:id/mute \| POST /api/v1/groups/:id/favorite

GET /api/v1/groups/:id/invite-link \| POST
/api/v1/groups/join-by-link/:token

GET /api/v1/groups/:id/shared-media \| POST /api/v1/groups/:id/report

21\. Home Feed Orchestration (3 Endpoints)

GET /api/v1/feed/home

Unified feed: priority queue (followed posts + breaking news) + blended
recommendations from 4 pipelines.

> Response: { \"data\": {
>
> \"priority_items\": \[
>
> { \"type\": \"post\", \"pin_reason\": \"followed_user\", \"item\":
> {\...} },
>
> { \"type\": \"news\", \"pin_reason\": \"breaking\", \"item\": {
> \"severity\": 9, \... } }
>
> \],
>
> \"feed_items\": \[
>
> { \"type\": \"post\", \"item\": {\...} },
>
> { \"type\": \"news\", \"item\": {\...} },
>
> { \"type\": \"group_activity\", \"item\": {
> \"group_id\",\"group_name\",\"latest_message\" } },
>
> { \"type\": \"connection_suggestion\", \"item\": {
> \"id\",\"name\",\"role\",\"match_score\": 0.87 } }
>
> \],
>
> \"session_id\": \"sess_abc123\" }, \"meta\": { \"page\":1,
> \"has_more\": true } }

GET /api/v1/home/suggestions

Carousels: Suggested Connections + Suggested Groups for home screen.

POST /api/v1/home/feed/seen

> Request: { \"session_id\": \"\...\", \"items\": \[{ \"id\", \"type\"
> }\] }

22\. Chat & Messaging (9 Endpoints)

GET /api/v1/chat/conversations

> Query: ?type=dm\|group&page=1
>
> Response: { \"data\": \[{ \"id\", \"type\": \"dm\",
>
> \"participant\": { \"id\",\"name\",\"photo_url\",\"is_online\": true
> },
>
> \"last_message\": { \"content\": \"What price for 100MT?\",
> \"sender_id\",\"sent_at\" },
>
> \"unread_count\": 2 },
>
> { \"id\", \"type\": \"group\",
>
> \"group\": { \"id\",\"name\",\"icon_url\",\"member_count\": 45 },
>
> \"last_message\": { \"content\",\"sender_name\",\"sent_at\" },
>
> \"unread_count\": 15 }\] }

POST /api/v1/chat/conversations

Create DM. Returns existing if already exists.

> Request (DM): { \"type\": \"dm\", \"participant_id\": \"uuid\" }
>
> Status: 201 Created, 409 DM Already Exists

GET /api/v1/chat/conversations/:id/messages

> Query: ?before=\<timestamp\>&limit=50 (cursor-based)
>
> Response: { \"data\": \[{ \"id\", \"sender\": {
> \"id\",\"name\",\"photo_url\" },
>
> \"content\": \"What price for 100MT sugar?\", \"media_url\": null,
>
> \"message_type\": \"text\", \"sent_at\": \"\...\" }\],
>
> \"meta\": { \"has_more\": true, \"oldest_timestamp\": \"\...\" } }

POST /api/v1/chat/conversations/:id/messages

Send message. Also: POST /api/v1/chat/groups/:id/messages for group
chat.

POST /api/v1/chat/conversations/:id/read

POST /api/v1/chat/upload

Pre-upload media. Returns S3 URL.

WebSocket: WSS /ws/chat?token={jwt}

**Client sends:**

> { \"type\": \"message\", \"content\": \"Hello!\", \"conversation_id\":
> \"uuid\" }
>
> { \"type\": \"typing\", \"conversation_id\": \"uuid\" }
>
> { \"type\": \"read\", \"conversation_id\": \"uuid\",
> \"last_read_message_id\": \"uuid\" }

**Server sends:**

> { \"type\": \"message\", \"data\": {
> \"id\",\"sender\":{\...},\"content\",\"sent_at\" } }
>
> { \"type\": \"typing\", \"data\": { \"user_id\",\"user_name\" } }
>
> { \"type\": \"read_receipt\", \"data\": { \"user_id\",\"last_read\":
> \"uuid\" } }
>
> { \"type\": \"online_status\", \"data\": { \"user_id\",\"is_online\":
> true } }

23\. Notifications (5 Endpoints)

GET /api/v1/notifications

> Query: ?limit=20&offset=0&unread_only=true

GET /api/v1/notifications/unread-count

> Response: { \"data\": { \"unread_count\": 12 } }

POST /api/v1/notifications/:id/read \| POST
/api/v1/notifications/read-all

PATCH /api/v1/notifications/preferences

> Request: { \"push_enabled\": true, \"push_chat\": false,
> \"push_quiet_start\": \"22:00\" }

24\. Engagement Tracking (2 Endpoints)

POST /api/v1/feed/engagement

Covered in Section 18. Batch signals for taste engine.

POST /api/v1/engagement/dwell

Lightweight dwell-only signals.

**PART D --- Recommendation Engine Internals**

25\. Vector Search (pgvector)

25.1 User Embeddings (Connections)

11 dimensions: 3 commodity + 3 role + 3 geo + 2 quantity. Asymmetric
IS/WANT encoding. Single SQL combines vector search + behavioral
reranking:

> SELECT u.\*, (1 - (ue.is_vector \<=\> \$1)) \* 0.80
>
> \+ LN(1+bs.follower_count) \* 0.07 + bs.engagement_score \* 0.06
>
> \+ bs.screentime_score \* 0.04 + EXP(-0.1\*days_inactive) \* 0.03 AS
> final_score
>
> FROM user_embeddings ue JOIN profiles u \... JOIN
> user_behavioral_scores bs \...
>
> WHERE ue.user_id NOT IN (blocked/connected users)
>
> ORDER BY final_score DESC LIMIT 20;

25.2 Post Embeddings

18 dimensions. Partial HNSW indexes per partition (hot/warm/cold).
Sequential search: hot first, warm if needed, cold for knowledge only.

25.3 Group Embeddings

11 dimensions. Same structure as user embeddings. Activity reranking
from group_activity_cache.

26\. Background Jobs (14 Cron Tasks)

  --------------------------- --------------- ----------------------------------------
  **Job**                     **Frequency**   **Description**

  news_ingestion              15-30 min       Fetch RSS, classify via Gemini,
                                              deduplicate, insert

  popular_posts_recalc        15 min          Velocity score, top 50 per commodity

  trending_articles_recalc    5-10 min        Segment-level trending (5 users,
                                              severity \>= 4)

  post_shelf_migration        1 hour          Expire, migrate hot→warm→cold,
                                              hard-delete \>30d

  user_post_taste_update      1 hour          Recompute from post_engagements with log
                                              scaling

  user_cluster_taste_update   1 hour          Recompute from news_engagements

  behavioral_scores_update    30 min          Followers, engagement, screentime,
                                              recency

  group_activity_update       15 min          messages_24h, unique_senders, growth

  user_category_affinity      1 hour          Category dims for group recs

  news_archive                Daily 2AM       Move \>30d to archive

  push_check                  5 min           Trending + breaking → FCM push
                                              (respecting prefs)

  meilisearch_sync            5 min           New/updated profiles to search index

  hashtag_cleanup             Daily 3AM       Reset counts, remove orphans

  session_cleanup             1 hour          Delete expired Redis sessions
  --------------------------- --------------- ----------------------------------------

27\. Redis Cache Architecture

  ---------------------- ------------- --------- --------------------------------
  **Key**                **Type**      **TTL**   **Purpose**

  user_vector:{uid}      JSON          24h       Cached embedding + profile

  user_taste:{uid}       HASH          24h       Post taste scores

  user_follows:{uid}     SET           1h        Following list

  seen_posts:{uid}       SET           30d       Dedup shown posts

  seen_news:{uid}        SET           7d        Dedup shown news

  session:{uid}:{sid}    HASH          2h        Home feed session taste

  popular:{commodity}    SORTED SET    15m       Top 50 popular posts

  otp:{phone}:{req}      STRING        5m        OTP code

  rate_limit:{ip}:{ep}   STRING        1m        Rate limiting

  chat:{type}:{id}       PUB/SUB       N/A       Real-time chat delivery

  online:{uid}           STRING        5m        WebSocket heartbeat

  unread:{uid}           HASH          24h       {conv_id: count}
  ---------------------- ------------- --------- --------------------------------

28\. WebSocket Architecture (Chat)

**Message flow:**

-   User A sends via REST: POST /chat/conversations/{id}/messages

-   Backend inserts into Postgres messages table

-   Backend publishes to Redis channel: chat:{type}:{id}

-   All FastAPI workers receive via Redis Pub/Sub

-   Workers push to connected WebSocket clients

-   Offline members get FCM push (respecting mute + quiet hours)

**Connection management:**

-   On connect: validate JWT, subscribe to all user conversation
    channels

-   Heartbeat: client pings every 30s. No ping for 60s = disconnect

-   On disconnect: unsubscribe, mark offline after 5min TTL

**PART E --- Deployment & Sprint Plan**

29\. Production Server Setup

> VPS (4GB+ RAM, 4-core)
>
> ├─ Nginx/Caddy (SSL + reverse proxy + WSS upgrade)
>
> │ ├─ api.vanijyaa.com → FastAPI :8000
>
> │ └─ wss://api.vanijyaa.com/ws → WebSocket
>
> ├─ FastAPI + Celery Worker + Celery Beat (Docker)
>
> ├─ PostgreSQL 16 + pgvector (Docker, persistent volume)
>
> ├─ Redis 7 (Docker)
>
> ├─ Meilisearch (Docker, persistent volume)
>
> └─ MinIO (Docker, persistent volume)

30\. Scaling Path

-   **Phase 1 (current):** Single VPS, Docker Compose. Handles \~5K
    users.

-   **Phase 2:** Managed Postgres + read replica. Separate server for
    workers. \~50K users.

-   **Phase 3:** Split Chat to own service. Load balancer. \~200K users.

-   **Phase 4:** Full microservices only when monitoring shows need.

31\. CI/CD Pipeline

Push to main → GitHub Actions: lint → test → build Docker image → push
to registry → SSH deploy → docker-compose up -d → alembic upgrade head.

**API Versioning:**

All endpoints under /api/v1/. Breaking changes go to /api/v2/. Old
version supported 3 months minimum. Flutter checks API version on
startup.

**Adding Modules Post-Launch:**

-   Backend: Create folder in modules/ with domain/data/presentation.
    Register router in main.py. Write Alembic migration. Zero changes to
    existing modules.

-   Frontend: Create folder in features/ with domain/data/presentation.
    Register routes in app_router.dart. Zero changes to existing
    features.

32\. Four-Day Sprint Board

Team: YOU (Flutter + Architect 80/20), DEV B (Senior Backend: Auth,
Profile, Feed, News), DEV C (Senior Backend: Connections, Chat, Groups,
Reco).

  --------- --------------------- --------------------- ------------------------
  **Day**   **YOU (Flutter)**     **DEV B (Backend)**   **DEV C (Backend)**

  1 AM      Scaffold both repos.  Auth domain+data:     Connections domain+data:
            docker-compose.yml.   User, OTP entities,   entities,
            Push to GitHub.       IAuthRepository,      IConnectionRepository,
                                  models, migrations.   models, migrations.

  1 PM      Flutter core: Dio,    Auth presentation:    Connections: GET
            Riverpod, GoRouter,   /otp/send,            /connections, GET
            Theme. Onboarding     /otp/verify,          /search (Meilisearch),
            screens.              /refresh, /role,      POST /request. pgvector
                                  /onboarding. JWT +    scaffold.
                                  Redis.                

  2 AM      Onboarding form, doc  Profile module: PATCH Reco engine: 11-dim
            upload, profile       /profile, POST        vectors, IS/WANT
            screens. Integrate    /documents, POST      asymmetric, pgvector
            Auth APIs.            /verify. Feed start:  HNSW. GET /suggestions.
                                  Post entity.          Chat start.

  2 PM      Connections list,     Feed: POST /posts,    Chat: GET
            search, filters,      GET /posts,           /conversations, GET
            bottom nav. Integrate like/comment/save.    /messages, POST
            Profile.              18-dim vectors, 3     /conversations, WS
                                  partitions. News      handler. Groups: all
                                  start.                layers.

  3 AM      Feed screen, news     News complete:        ALL reco engines: Posts
            screen. Integrate     ingestion, Gemini     reranking, Groups
            Connections + Feed    classify, scoring.    2-stage. All
            APIs.                 GET /news. Tasks.py.  /suggestions endpoints.

  3 PM      Chat (DM, WebSocket). Home Feed: priority   Groups reco. Bug fixes.
            Groups. Home feed     queue + mixer + taste Seed data script.
            aggregator. Integrate engine. GET           Integration support.
            News.                 /feed/home. POST      
                                  /engagement.          

  4 AM      Polish UI, connect    VPS setup, Docker     Seed data on prod.
            carousels, build APK, deploy, Nginx+SSL,    Verify recs on real
            test full flow 3x.    Alembic migrate,      data. Final bug fixes.
                                  Sentry. Smoke test.   

  4 PM      Point APK to prod.    Monitor logs. GitHub  API docs verify (FastAPI
            Final integration     Actions CI/CD. Fix    /docs). Final QA.
            test. Critical bugs   500s.                 Support deploy.
            only. Ship.                                 
  --------- --------------------- --------------------- ------------------------

**End of Day 4: App deployed. Login → Profile → Feed → News → Connect →
Chat works end-to-end.**

33\. Complete API Summary (93 Endpoints)

  -------- --------------------------- ---------------------------------- ----------------------
  **\#**   **Method**                  **Endpoint**                       **Module**

  1-10     POST/PUT                    auth/otp/send, otp/verify,         Auth
                                       token/refresh, language, role,     
                                       onboarding, onboarding/documents,  
                                       onboarding/skip-docs, fcm-token,   
                                       logout                             

  11-21    GET/PATCH/POST/PUT/DELETE   profile/me, profile/:id, profile,  Profile
                                       profile/photo, profile/documents,  
                                       profile/verify/:type,              
                                       profile/saved, profile/my-posts,   
                                       profile/language, profile/invite,  
                                       profile (delete)                   

  22-33    GET/POST/PUT/DELETE         connections/suggestions,           Connections
                                       connections, connections/requests, 
                                       connections/search,                
                                       connections/request,               
                                       connections/request/:id,           
                                       connections/:id,                   
                                       connections/block,                 
                                       connections/:uid/follow (x2),      
                                       report                             

  34-49    GET/POST/PATCH/DELETE       feed/posts, feed/following,        Posts
                                       feed/posts (create),               
                                       feed/posts/:id (x3),               
                                       posts/:id/like, save, share,       
                                       comment, comments, comments/:cid,  
                                       hashtags/search,                   
                                       hashtags/:tag/posts,               
                                       feed/engagement                    

  50-57    GET/POST                    news, news/:id, news/search,       News
                                       news/:id/like, save, share,        
                                       comment, news/:id/comments         

  58-75    GET/POST/PATCH/DELETE       groups/suggestions, groups, groups Groups
                                       (create), groups/:id, groups/:id   
                                       (patch), groups/:id/permissions,   
                                       join, leave, members, members/add, 
                                       members/:uid (remove), freeze      
                                       (x2), mute, favorite, invite-link, 
                                       join-by-link, shared-media, report 

  76-78    GET/POST                    feed/home, home/suggestions,       Home Feed
                                       home/feed/seen                     

  79-87    GET/POST/WSS                chat/conversations (x2),           Chat
                                       conversations/:id/messages (x2),   
                                       conversations/:id/read,            
                                       chat/groups/:id/messages (x2),     
                                       chat/upload, ws/chat               

  88-92    GET/POST/PATCH              notifications,                     Notifications
                                       notifications/unread-count,        
                                       notifications/:id/read,            
                                       notifications/read-all,            
                                       notifications/preferences          

  93       POST                        engagement/dwell                   Engagement
  -------- --------------------------- ---------------------------------- ----------------------

**--- End of Architecture & API Contracts ---**
