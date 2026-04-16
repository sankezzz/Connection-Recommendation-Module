from app.modules.connections.db.chromadb import get_chroma_collection

collection = get_chroma_collection()

# Fetch a specific record with its vector
result = collection.get(
    ids=["5"],
    include=["embeddings", "metadatas"]
)

print("Metadata:", result["metadatas"][0])
print("Vector dims:", len(result["embeddings"][0]))
print("Vector:", result["embeddings"][0])