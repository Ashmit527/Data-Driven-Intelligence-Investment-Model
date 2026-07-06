import json
import os
from sentence_transformers import SentenceTransformer

# Load the model once - this downloads it the first time, then uses local cache
print("Loading embedding model...")
model = SentenceTransformer('all-MiniLM-L6-v2')
print("Model loaded.\n")


def embed_company_chunks(chunks_path, output_path, batch_size=64):
    with open(chunks_path, "r", encoding="utf-8") as f:
        chunks = json.load(f)

    texts = [chunk["text"] for chunk in chunks]

    print(f"  Embedding {len(texts)} chunks...")
    # encode() handles batching internally - just give it the full list
    embeddings = model.encode(texts, batch_size=batch_size, show_progress_bar=True)

    # embeddings is a numpy array; convert each row to a plain list for JSON saving
    for chunk, embedding in zip(chunks, embeddings):
        chunk["embedding"] = embedding.tolist()

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(chunks, f, ensure_ascii=False)

    print(f"  Saved {len(chunks)} embedded chunks to {output_path}")


if __name__ == "__main__":
    chunks_folder = "data/chunks"
    output_folder = "data/embeddings"
    os.makedirs(output_folder, exist_ok=True)

    for filename in os.listdir(chunks_folder):
        if filename.endswith("_chunks.json"):
            company_name = filename.replace("_chunks.json", "")
            print(f"\nProcessing {company_name}...")

            chunks_path = os.path.join(chunks_folder, filename)
            output_path = os.path.join(output_folder, f"{company_name}_embedded.json")

            embed_company_chunks(chunks_path, output_path)