"""
Connections module — HTTP layer (thin wrappers only, zero business logic).

Two sub-routers:
  connections_router      /connections/...
  recommendations_router  /recommendations/...

URL convention
--------------
{user_id}   — the ACTING user (you). Explicit in every path for backend testability.
{target_id} — the OTHER user being followed / messaged.

No auth token required — user_id is passed in the URL path.

Import into main.py:
  from app.modules.connections.router import connections_router, recommendations_router
"""
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.modules.connections.schemas import SearchPayload
from app.modules.connections import service


# ═══════════════════════════════════════════════════════════════════════════════
# 1. Connections router   /connections/...
# ═══════════════════════════════════════════════════════════════════════════════

connections_router = APIRouter(prefix="/connections", tags=["connections"])


# ── Search suggestions (no user context — register BEFORE /{user_id} routes) ──

@connections_router.get("/search/suggestions")
def suggestions(
    q: str = Query(..., min_length=2),
    db: Session = Depends(get_db),
):
    """Name / business_name prefix suggestions. Returns top 8. No user context needed."""
    results = service.search_suggestions(db, q=q)
    return {"q": q, "total": len(results), "suggestions": results}


# ── Follow ────────────────────────────────────────────────────────────────────

@connections_router.post("/{user_id}/follow/{target_id}")
def follow(
    user_id: UUID,
    target_id: UUID,
    db: Session = Depends(get_db),
):
    """Follow target_id as user_id. Returns 409 if already following."""
    return service.follow_user(db, follower_id=user_id, following_id=target_id)


@connections_router.delete("/{user_id}/follow/{target_id}")
def unfollow(
    user_id: UUID,
    target_id: UUID,
    db: Session = Depends(get_db),
):
    """Unfollow target_id as user_id. Returns 404 if not currently following."""
    return service.unfollow_user(db, follower_id=user_id, following_id=target_id)


@connections_router.get("/{user_id}/followers")
def list_followers(
    user_id: UUID,
    db: Session = Depends(get_db),
):
    """Everyone who follows user_id."""
    followers = service.get_followers(db, user_id)
    return {"user_id": str(user_id), "total": len(followers), "followers": followers}


@connections_router.get("/{user_id}/following")
def list_following(
    user_id: UUID,
    db: Session = Depends(get_db),
):
    """Everyone user_id follows."""
    following = service.get_following(db, user_id)
    return {"user_id": str(user_id), "total": len(following), "following": following}


@connections_router.get("/{user_id}/follow/status/{target_id}")
def follow_status(
    user_id: UUID,
    target_id: UUID,
    db: Session = Depends(get_db),
):
    """Is user_id following target_id? Drives Follow / Unfollow button state."""
    following = service.is_following(db, me=user_id, target=target_id)
    return {"me": str(user_id), "target": str(target_id), "following": following}


# ── Message Requests ──────────────────────────────────────────────────────────

@connections_router.post("/{user_id}/message-request/{target_id}")
def send_request(
    user_id: UUID,
    target_id: UUID,
    db: Session = Depends(get_db),
):
    """Send a message request from user_id to target_id. Returns 409 if one already exists."""
    result = service.send_message_request(db, sender_id=user_id, receiver_id=target_id)
    return {"status": "sent", **result}


@connections_router.delete("/{user_id}/message-request/{target_id}")
def withdraw_request(
    user_id: UUID,
    target_id: UUID,
    db: Session = Depends(get_db),
):
    """Withdraw a pending message request. Returns 404 if no pending request."""
    return service.withdraw_message_request(db, sender_id=user_id, receiver_id=target_id)


@connections_router.patch("/{user_id}/message-request/{request_id}/accept")
def accept_request(
    user_id: UUID,
    request_id: int,
    db: Session = Depends(get_db),
):
    """Accept a message request. user_id must be the receiver."""
    return service.respond_to_request(db, request_id=request_id, me=user_id, action="accepted")


@connections_router.patch("/{user_id}/message-request/{request_id}/decline")
def decline_request(
    user_id: UUID,
    request_id: int,
    db: Session = Depends(get_db),
):
    """Decline a message request. user_id must be the receiver."""
    return service.respond_to_request(db, request_id=request_id, me=user_id, action="declined")


@connections_router.get("/{user_id}/message-requests/received")
def received_requests(
    user_id: UUID,
    db: Session = Depends(get_db),
):
    """Pending message requests waiting on user_id to accept or decline."""
    requests = service.get_received_requests(db, me=user_id)
    return {"me": str(user_id), "total": len(requests), "requests": requests}


@connections_router.get("/{user_id}/message-requests/sent")
def sent_requests(
    user_id: UUID,
    db: Session = Depends(get_db),
):
    """All message requests user_id has sent, across all statuses."""
    requests = service.get_sent_requests(db, me=user_id)
    return {"me": str(user_id), "total": len(requests), "requests": requests}


# ── Search ────────────────────────────────────────────────────────────────────

@connections_router.get("/{user_id}/search")
def search(
    user_id: UUID,
    db: Session = Depends(get_db),
    q:             str | None = Query(default=None, description="Partial match on name or business name"),
    role:          str | None = Query(default=None, description="trader | broker | exporter"),
    commodity:     str | None = Query(default=None, description="Partial match on commodity name"),
    city:          str | None = Query(default=None, description="Partial match on city"),
    verified_only: bool       = Query(default=False, description="Only return verified users"),
    page:          int        = Query(default=1, ge=1),
    limit:         int        = Query(default=20, ge=1, le=100),
):
    """Filtered user search. user_id is excluded from results. All query params optional."""
    return service.search_users(
        db, me=user_id, q=q, role=role, commodity=commodity,
        city=city, verified_only=verified_only, page=page, limit=limit,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# 2. Recommendations router   /recommendations/...
# ═══════════════════════════════════════════════════════════════════════════════

recommendations_router = APIRouter(prefix="/recommendations", tags=["recommendations"])


@recommendations_router.get("/{user_id}")
def get_recommendations(
    user_id: UUID,
    db: Session = Depends(get_db),
):
    """
    Top-20 user matches for user_id based on their profile
    (commodity, role, location, quantity). Sorted by cosine similarity descending.
    """
    return service.get_recommendations(db, user_id=user_id)


@recommendations_router.post("/search")
def custom_search(
    payload: SearchPayload,
    db: Session = Depends(get_db),
):
    """
    Ad-hoc vector search with a custom payload — no user_id needed.
    Useful for showing preview results before or during signup.
    """
    return service.custom_recommendation_search(
        db,
        commodity=payload.commodity,
        role=payload.role,
        latitude_raw=payload.latitude_raw,
        longitude_raw=payload.longitude_raw,
        qty_min_mt=payload.qty_min_mt,
        qty_max_mt=payload.qty_max_mt,
    )
