FROM python:3.11-slim

WORKDIR /app

# System dependencies some packages need to build
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY *.py .
COPY data/faiss_index.bin data/faiss_index.bin
COPY data/chunk_metadata.pkl data/chunk_metadata.pkl

EXPOSE 8000

CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]