# test_search.py
import asyncio
import asyncpg
import os
from dotenv import load_dotenv
from app.modules.connections.encoding.vector import build_query_vector
from app.modules.connections.db.chromadb import get_chroma_collection

load_dotenv()

TEST_USER_ID = 68  # change this to any user_id in your Supabase

async def test_search(user_id: int):
    # 1. Fetch user from Supabase
    conn = await asyncpg.connect(
        os.getenv("DATABASE_URL").replace("postgresql+asyncpg://", "postgresql://"),
        statement_cache_size=0
    )
    row = await conn.fetchrow(
        'SELECT * FROM "Users" WHERE user_id = $1', user_id
    )
    await conn.close()

    if not row:
        print(f"User {user_id} not found.")
        return

    print("=" * 60)
    print(f"Searcher: User {row['user_id']}")
    print(f"  Role      : {row['role']}")
    print(f"  Commodity : {row['commodity']}")
    print(f"  City      : {row['city']}, {row['state']}")
    print(f"  Location  : {row['latitude_raw']}, {row['longitude_raw']}")
    print(f"  Qty range : {row['min_quantity_mt']}–{row['max_quantity_mt']}mt")
    print("=" * 60)

    # 2. Build WANT query vector
    commodity_list = [c.strip() for c in row["commodity"].split(";")]
    query_vec = build_query_vector(
        commodity_list=commodity_list,
        role=row["role"],
        lat=float(row["latitude_raw"]),
        lon=float(row["longitude_raw"]),
    )
    print(f"\nQuery vector dims : {len(query_vec)}")
    print(f"  commodity [0:3] : {[round(v,4) for v in query_vec[0:3]]}")
    print(f"  role      [3:6] : {[round(v,4) for v in query_vec[3:6]]}")
    print(f"  geo       [6:9] : {[round(v,4) for v in query_vec[6:9]]}")

    # 3. Query ChromaDB — HNSW does the work
    collection = get_chroma_collection()
    results = collection.query(
        query_embeddings=[query_vec],
        n_results=21,                          # 21 because searcher might be in results
        include=["metadatas", "distances"],
    )

    # 4. Filter out the searcher themselves and take top 20
    matches = [
        (meta, dist)
        for meta, dist in zip(results["metadatas"][0], results["distances"][0])
        if meta["user_id"] != user_id
    ][:20]

    # 5. Print results
    print(f"\nTop 20 matches:\n")
    print(f"{'#':<4} {'user_id':<10} {'role':<12} {'commodity':<25} {'city':<15} {'similarity':<10} {'qty_range'}")
    print("-" * 100)
    for i, (meta, dist) in enumerate(matches, 1):
        similarity = round(1 - dist, 4)       # ChromaDB returns distance, convert to similarity
        qty = f"{meta['qty_min']}–{meta['qty_max']}mt"
        print(f"{i:<4} {meta['user_id']:<10} {meta['role']:<12} {meta['commodity']:<25} {meta['city']:<15} {similarity:<10} {qty}")


if __name__ == "__main__":
    asyncio.run(test_search(TEST_USER_ID))