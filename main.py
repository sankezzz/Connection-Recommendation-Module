# main.py
from fastapi import FastAPI
from sqlalchemy import text
from app.db.postgres import engine
from app.db.postgres import engine
from app.db.chromadb import get_chroma_collection

app = FastAPI()


@app.get("/health")
async def health():
    # Test Postgres
    async with engine.connect() as conn:
        await conn.execute(text("SELECT 1"))

    # Test ChromaDB
    collection = get_chroma_collection()
    count = collection.count()

    return {
        "postgres": "connected",
        "chromadb": "connected",
        "vectors_in_db": count
    }
# @app.get("/test-chromadb")