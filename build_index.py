import json
import os
import numpy as np
import faiss
import pickle

def load_all_embedded_chunks(embeddings_folder):
    """Load every company's embedded chunks into one combined list."""
    all_chunks = []
    for filename in os.listdir(embeddings_folder):
        if filename.endswith("_embedded.json"):
            path = os.path.join(embeddings_folder, filename)
            with open(path, "r", encoding="utf-8") as f:
                chunks = json.load(f)
                all_chunks.extend(chunks)
    return all_chunks


def build_faiss_index(chunks):
    """Build a FAISS index from a list of chunks (each with an 'embedding' field)."""
    # Extract just the embedding vectors, stack into one big matrix
    embeddings = np.array([chunk["embedding"] for chunk in chunks]).astype("float32")
    
    dimension = embeddings.shape[1]  # 384 for MiniLM
    print(f"Building index with {len(chunks)} vectors of dimension {dimension}")

    # IndexFlatL2 = exact nearest-neighbor search using Euclidean (L2) distance
    # Simple and exact - perfect for our scale (~2500 vectors)
    index = faiss.IndexFlatL2(dimension)
    index.add(embeddings)

    return index


if __name__ == "__main__":
    embeddings_folder = "data/embeddings"
    
    print("Loading all embedded chunks...")
    all_chunks = load_all_embedded_chunks(embeddings_folder)
    print(f"Total chunks loaded: {len(all_chunks)}")

    index = build_faiss_index(all_chunks)

    # Save the FAISS index itself
    faiss.write_index(index, "data/faiss_index.bin")

    # Save the chunk metadata (text, company, page) separately, WITHOUT the embedding
    # (we don't need to keep embeddings around anymore - the index already has them)
    metadata = []
    for chunk in all_chunks:
        metadata.append({
            "company": chunk["company"],
            "page_number": chunk["page_number"],
            "text": chunk["text"]
        })

    with open("data/chunk_metadata.pkl", "wb") as f:
        pickle.dump(metadata, f)

    print("Index and metadata saved.")