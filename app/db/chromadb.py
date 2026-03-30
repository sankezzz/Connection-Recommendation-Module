# app/db/chromadb.py
import os
import chromadb
from dotenv import load_dotenv

load_dotenv()

def get_chroma_collection():
    client = chromadb.HttpClient(
        ssl=True,
        host=os.getenv("CHROMA_HOST"),
        tenant=os.getenv("CHROMA_TENANT"),
        database=os.getenv("CHROMA_DATABASE"),
        headers={"x-chroma-token": os.getenv("CHROMA_API_KEY")}
    )

    collection = client.get_or_create_collection(
        name="commodity_users",
        metadata={"hnsw:space": "cosine"}
    )

    return collection
