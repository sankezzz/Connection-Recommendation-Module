# app/routes/connections.py
from fastapi import APIRouter, Query
from pydantic import BaseModel
from app.modules.connections.db import connections as db

router = APIRouter(prefix="/connections", tags=["connections"])


# ─── Schemas ──────────────────────────────────────────────────────────────────

class ActorBody(BaseModel):
    me: int   # acting user's id (replace with auth token once auth is added)

class RespondBody(BaseModel):
    me: int   # must be the receiver


# ─── Follow ───────────────────────────────────────────────────────────────────

@router.post("/follow/{user_id}")
async def follow(user_id: int, body: ActorBody):
    """Follow a user. Idempotent — returns 409 if already following."""
    return await db.follow_user(follower_id=body.me, following_id=user_id)


@router.delete("/follow/{user_id}")
async def unfollow(user_id: int, me: int = Query(...)):
    """Unfollow a user. Returns 404 if not currently following."""
    return await db.unfollow_user(follower_id=me, following_id=user_id)


@router.get("/followers/{user_id}")
async def list_followers(user_id: int):
    """Everyone who follows this user."""
    followers = await db.get_followers(user_id)
    return {"user_id": user_id, "total": len(followers), "followers": followers}


@router.get("/following/{user_id}")
async def list_following(user_id: int):
    """Everyone this user follows."""
    following = await db.get_following(user_id)
    return {"user_id": user_id, "total": len(following), "following": following}


@router.get("/follow/status/{user_id}")
async def follow_status(user_id: int, me: int = Query(...)):
    """
    Am I following this person?
    Use to drive the Follow / Unfollow button state on the frontend.
    """
    following = await db.is_following(me=me, target=user_id)
    return {"me": me, "target": user_id, "following": following}


# ─── Message Requests ─────────────────────────────────────────────────────────

@router.post("/message-request/{user_id}")
async def send_request(user_id: int, body: ActorBody):
    """Send a message request to a user. Returns 409 if one already exists."""
    result = await db.send_message_request(sender_id=body.me, receiver_id=user_id)
    return {"status": "sent", **result}


@router.delete("/message-request/{user_id}")
async def withdraw_request(user_id: int, me: int = Query(...)):
    """Withdraw a pending message request. Returns 404 if no pending request exists."""
    return await db.withdraw_message_request(sender_id=me, receiver_id=user_id)


@router.patch("/message-request/{request_id}/accept")
async def accept_request(request_id: int, body: RespondBody):
    """Accept a message request. Only the receiver can accept."""
    return await db.respond_to_request(request_id=request_id, me=body.me, action="accepted")


@router.patch("/message-request/{request_id}/decline")
async def decline_request(request_id: int, body: RespondBody):
    """Decline a message request. Only the receiver can decline."""
    return await db.respond_to_request(request_id=request_id, me=body.me, action="declined")


@router.get("/message-requests/received")
async def received_requests(me: int = Query(...)):
    """Pending message requests waiting on me to accept or decline."""
    requests = await db.get_received_requests(me=me)
    return {"me": me, "total": len(requests), "requests": requests}


@router.get("/message-requests/sent")
async def sent_requests(me: int = Query(...)):
    """All message requests I have sent, with their current status."""
    requests = await db.get_sent_requests(me=me)
    return {"me": me, "total": len(requests), "requests": requests}


# ─── Search ───────────────────────────────────────────────────────────────────

@router.get("/search/suggestions")
async def suggestions(q: str = Query(..., min_length=2)):
    """
    Fuzzy 'did you mean?' suggestions using trigram similarity (pg_trgm).
    Matches against city, commodity, and role. Handles typos.
    """
    results = await db.search_suggestions(q=q)
    return {"q": q, "total": len(results), "suggestions": results}


@router.get("/search")
async def search(
    me:        int         = Query(...),
    q:         str | None  = Query(default=None, description="Text search across city, state, commodity, role"),
    role:      str | None  = Query(default=None),
    commodity: str | None  = Query(default=None),
    city:      str | None  = Query(default=None),
):
    """
    Filtered user search. All query params except `me` are optional.
    Filters stack with AND logic. Returns up to 50 results.
    """
    results = await db.search_users(me=me, q=q, role=role, commodity=commodity, city=city)
    return {"total": len(results), "results": results}
