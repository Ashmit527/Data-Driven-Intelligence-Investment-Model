import faiss
import pickle
from sentence_transformers import SentenceTransformer

# Load everything back
print("Loading model and index...")
model = SentenceTransformer('all-MiniLM-L6-v2')
index = faiss.read_index("data/faiss_index.bin")

with open("data/chunk_metadata.pkl", "rb") as f:
    metadata = pickle.load(f)

print("Ready.\n")


def search(query, k=5):
    """Embed the query, search FAISS, return top-k matching chunks."""
    query_embedding = model.encode([query]).astype("float32")
    
    distances, indices = index.search(query_embedding, k)
    
    results = []
    for idx, dist in zip(indices[0], distances[0]):
        chunk_info = metadata[idx]
        results.append({
            "company": chunk_info["company"],
            "page_number": chunk_info["page_number"],
            "text": chunk_info["text"],
            "distance": float(dist)
        })
    return results


if __name__ == "__main__":
    test_query = "What is the company's digital transformation strategy?"
    
    results = search(test_query, k=5)
    
    for i, r in enumerate(results):
        print(f"\n--- Result {i+1} (company: {r['company']}, page: {r['page_number']}, distance: {r['distance']:.3f}) ---")
        print(r['text'][:300])