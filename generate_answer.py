import ollama
import faiss
import pickle
from sentence_transformers import SentenceTransformer

# Load model and index once
print("Loading embedding model and FAISS index...")
embed_model = SentenceTransformer('all-MiniLM-L6-v2')
index = faiss.read_index("data/faiss_index.bin")

with open("data/chunk_metadata.pkl", "rb") as f:
    metadata = pickle.load(f)

print("Ready.\n")


def retrieve_chunks(query, k=5):
    """Same retrieval logic from Day 5."""
    query_embedding = embed_model.encode([query]).astype("float32")
    distances, indices = index.search(query_embedding, k)

    results = []
    for idx, dist in zip(indices[0], distances[0]):
        chunk_info = metadata[idx]
        results.append(chunk_info)
    return results


def build_prompt(query, retrieved_chunks):
    context_text = ""
    for i, chunk in enumerate(retrieved_chunks):
        context_text += f"\n[Source {i+1} - {chunk['company']}, page {chunk['page_number']}]\n{chunk['text']}\n"

    prompt = f"""You are a financial research assistant. Answer the question using ONLY the information provided in the sources below.

IMPORTANT: When you reference a source, carefully match the source number to its actual label above (e.g., if information came from "[Source 2]", cite it as Source 2, not any other number). Double-check each citation before including it.

If the sources don't contain enough information to answer, say so clearly instead of guessing. Do not add information from general knowledge that isn't supported by the sources.

SOURCES:
{context_text}

QUESTION: {query}

ANSWER:"""
    return prompt


def generate_answer(query, k=5):
    """Full RAG pipeline: retrieve, build prompt, generate."""
    retrieved_chunks = retrieve_chunks(query, k)
    prompt = build_prompt(query, retrieved_chunks)

    response = ollama.chat(
        model='llama3.2:3b',
        messages=[{'role': 'user', 'content': prompt}]
    )

    answer = response['message']['content']
    return answer, retrieved_chunks


if __name__ == "__main__":
    query = "What is the main source of revenue of tata motors"
    
    answer, sources = generate_answer(query)

    print(f"QUESTION: {query}\n")
    print(f"ANSWER:\n{answer}\n")
    print("--- Sources used ---")
    for i, s in enumerate(sources):
        print(f"[{i+1}] {s['company']}, page {s['page_number']}")