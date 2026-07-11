# AI Trading Research Assistant

A RAG + agentic AI system for answering questions about NSE-listed companies using their financial filings and live market data.

## Status: Phase 1 complete — entering Phase 2 (Agentic Layer)

## Overview

This project combines two complementary data sources to answer questions about NSE-listed companies:

- **Company annual reports (PDFs)** — via a RAG pipeline, for qualitative/narrative questions (risk factors, management commentary, strategy, business outlook)
- **OpenBB (live/structured financial data)** — planned for Phase 2, for numeric/quantitative questions (revenue, ratios, live prices, financial metrics)

The system is built entirely with free, local tools — no paid APIs required.

## Companies Covered (Phase 1)

Adani, Infosys, Reliance Industries, SBI, Tata Motors — FY 2025-26 annual reports.

## Architecture (Phase 1 — RAG)

```
PDFs (data/raw_pdfs/)
  → text extraction (pdfplumber)
  → chunk-level table filtering (heuristic: digit density, symbols, sentence structure)
  → chunking (700 words, 100-word overlap)
  → local embeddings (sentence-transformers, all-MiniLM-L6-v2)
  → FAISS vector index (exact L2 search)
  → retrieval (top-k similar chunks for a given question)
  → prompt construction (context + question)
  → local LLM generation (Llama 3.2 3B, via Ollama)
  → grounded answer with source citations
```

## Roadmap

- [x] **Phase 1: RAG pipeline** (Days 1-7)
  - [x] PDF ingestion and text extraction
  - [x] Chunk-level table filtering
  - [x] Local embedding generation (MiniLM)
  - [x] FAISS vector search
  - [x] Local LLM generation (Llama 3.2 3B via Ollama)
  - [x] Formal evaluation (25-question set, scored for retrieval/answer/citation accuracy)
- [ ] **Phase 2: Agentic layer** (Days 9-13)
  - [ ] OpenBB integration as a live-data tool (routing numeric/financial-metric questions here instead of RAG)
  - [ ] Calculator tool for derived metrics (ratios, etc.)
  - [ ] RAG search wrapped as a callable tool
  - [ ] Tool-calling loop: LLM decides which tool(s) to invoke per question
- [ ] **Phase 3: MLOps / deployment** (Days 14-18)
  - [ ] FastAPI wrapper
  - [ ] Request logging
  - [ ] Experiment tracking (chunking/embedding config comparisons)
  - [ ] Docker containerization
  - [ ] Final documentation and polish

## Phase 1 Evaluation Summary

25 hand-written evaluation questions, manually scored against ground truth from the source PDFs:

| Metric | Result |
|---|---|
| Retrieval accuracy | 72% (18/25) |
| Answer accuracy | 28% (7/25) |
| Citation accuracy | 48% (12/25) |

**Key finding:** RAG performs well on narrative/qualitative questions (risk factors, strategy commentary) but performs poorly on precise numeric questions (revenue, EBITDA, dividends, ratios) — primarily because financial tables get filtered out during PDF text extraction rather than properly structured. This is a known, evidence-based limitation, not an oversight — full details and reasoning in [`PHASE1_NOTES.md`](./PHASE1_NOTES.md).

**Architectural decision:** rather than immediately building complex table-extraction logic, Phase 2 will route numeric/financial-metric questions to OpenBB's structured data instead — a better architectural fit for that class of question. Table extraction from PDFs remains a documented fallback option if gaps remain after Phase 2.

## Tech Stack

- **PDF processing:** pdfplumber
- **Embeddings:** sentence-transformers (`all-MiniLM-L6-v2`) — local, free
- **Vector search:** FAISS (CPU, exact search)
- **LLM generation:** Llama 3.2 3B via Ollama — local, free
- **Live financial data (Phase 2):** OpenBB
- **Planned (Phase 3):** FastAPI, Docker, MLflow (or similar experiment tracking)

## Project Structure

```
data/
  raw_pdfs/          # source annual report PDFs (not tracked in git)
  extracted_text/    # raw extracted text per company (not tracked)
  chunks/            # filtered, chunked text per company (not tracked)
  embeddings/        # chunk embeddings per company (not tracked)
  faiss_index.bin    # FAISS vector index (not tracked)
  chunk_metadata.pkl # chunk metadata for retrieval lookup (not tracked)

check_pdfs.py            # PDF sanity check (text extractability)
extract_text.py           # PDF text extraction
chunk_text.py              # chunk-level table filtering + chunking
generate_embeddings.py     # local embedding generation
build_index.py              # FAISS index construction
test_search.py                # standalone retrieval testing
generate_answer.py             # full RAG pipeline (retrieve + generate)
eval_questions.json              # 25-question evaluation set
run_evaluation.py                 # runs eval set through the pipeline
summarize_eval.py                  # computes accuracy metrics from scored results
PHASE1_NOTES.md                     # detailed Phase 1 problems/fixes/limitations
```

## Notes

Large data files (PDFs, extracted text, chunks, embeddings, the FAISS index) are excluded from version control via `.gitignore` to keep the repository lightweight. To reproduce, place annual report PDFs in `data/raw_pdfs/` and run the pipeline scripts in order (extraction → chunking → embeddings → indexing).
