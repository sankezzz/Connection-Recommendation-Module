# app/routes/users.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.db.postgres import AsyncSessionLocal
from app.db.chromadb import get_chroma_collection
from app.encoding.vector import build_candidate_vector
from sqlalchemy import text

router = APIRouter(prefix="/users", tags=["users"])

# ─── Schemas ──────────────────────────────────────────────────────────────────

class UserCreate(BaseModel):
    user_id:         int
    commodity:       str        # semicolon separated e.g. "rice;cotton"
    role:            str
    city:            str
    state:           str
    latitude_raw:    float
    longitude_raw:   float
    min_quantity_mt: int
    max_quantity_mt: int

class UserUpdate(BaseModel):
    commodity:       str | None = None
    role:            str | None = None
    city:            str | None = None
    state:           str | None = None
    latitude_raw:    float | None = None
    longitude_raw:   float | None = None
    min_quantity_mt: int | None = None
    max_quantity_mt: int | None = None

# ─── Register ─────────────────────────────────────────────────────────────────

@router.post("")
async def create_user(user: UserCreate):
    async with AsyncSessionLocal() as db:
        # 1. Save to Postgres
        await db.execute(text("""
            INSERT INTO "Users" (
                user_id, commodity, role, city, state,
                latitude_raw, longitude_raw,
                min_quantity_mt, max_quantity_mt
            ) VALUES (
                :user_id, :commodity, :role, :city, :state,
                :latitude_raw, :longitude_raw,
                :min_quantity_mt, :max_quantity_mt
            )
        """), user.model_dump())
        await db.commit()

    # 2. Build IS vector and upsert into ChromaDB
    commodity_list = [c.strip() for c in user.commodity.split(";")]
    vector = build_candidate_vector(
        commodity_list=commodity_list,
        role=user.role,
        lat=user.latitude_raw,
        lon=user.longitude_raw,
    )

    collection = get_chroma_collection()
    collection.upsert(
        ids=[str(user.user_id)],
        embeddings=[vector],
        metadatas=[{
            "user_id":       user.user_id,
            "role":          user.role,
            "commodity":     user.commodity,
            "city":          user.city,
            "state":         user.state,
            "latitude_raw":  user.latitude_raw,
            "longitude_raw": user.longitude_raw,
            "qty_min":       user.min_quantity_mt,
            "qty_max":       user.max_quantity_mt,
        }],
    )

    return {"status": "created", "user_id": user.user_id}

# ─── Update ───────────────────────────────────────────────────────────────────

@router.patch("/{user_id}")
async def update_user(user_id: int, update: UserUpdate):
    async with AsyncSessionLocal() as db:
        # 1. Fetch existing user
        result = await db.execute(
            text('SELECT * FROM "Users" WHERE user_id = :uid'),
            {"uid": user_id}
        )
        row = result.mappings().first()
        if not row:
            raise HTTPException(status_code=404, detail="User not found")

        # 2. Merge updates
        updated = dict(row)
        for field, val in update.model_dump(exclude_none=True).items():
            updated[field] = val

        # 3. Update Postgres
        await db.execute(text("""
            UPDATE "Users" SET
                commodity       = :commodity,
                role            = :role,
                city            = :city,
                state           = :state,
                latitude_raw    = :latitude_raw,
                longitude_raw   = :longitude_raw,
                min_quantity_mt = :min_quantity_mt,
                max_quantity_mt = :max_quantity_mt
            WHERE user_id = :user_id
        """), {
            "user_id":        user_id,
            "commodity":      updated["commodity"],
            "role":           updated["role"],
            "city":           updated["city"],
            "state":          updated["state"],
            "latitude_raw":   updated["latitude_raw"],
            "longitude_raw":  updated["longitude_raw"],
            "min_quantity_mt":updated["min_quantity_mt"],
            "max_quantity_mt":updated["max_quantity_mt"],
        })
        await db.commit()

    # 4. Rebuild IS vector and upsert into ChromaDB
    commodity_list = [c.strip() for c in updated["commodity"].split(";")]
    vector = build_candidate_vector(
        commodity_list=commodity_list,
        role=updated["role"],
        lat=float(updated["latitude_raw"]),
        lon=float(updated["longitude_raw"]),
    )

    collection = get_chroma_collection()
    collection.upsert(
        ids=[str(user_id)],
        embeddings=[vector],
        metadatas=[{
            "user_id":       user_id,
            "role":          updated["role"],
            "commodity":     updated["commodity"],
            "city":          updated["city"],
            "state":         updated["state"],
            "latitude_raw":  float(updated["latitude_raw"]),
            "longitude_raw": float(updated["longitude_raw"]),
            "qty_min":       int(updated["min_quantity_mt"]),
            "qty_max":       int(updated["max_quantity_mt"]),
        }],
    )

    return {"status": "updated", "user_id": user_id}

# ─── Delete ───────────────────────────────────────────────────────────────────

@router.delete("/{user_id}")
async def delete_user(user_id: int):
    async with AsyncSessionLocal() as db:
        await db.execute(
            text('DELETE FROM "Users" WHERE user_id = :uid'),
            {"uid": user_id}
        )
        await db.commit()

    # Remove from ChromaDB too
    collection = get_chroma_collection()
    collection.delete(ids=[str(user_id)])

    return {"status": "deleted", "user_id": user_id}