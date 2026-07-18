# AI Trading Research Assistant

A RAG + agentic AI system for answering questions about NSE-listed companies using their financial filings and live market data.

## Status: Phase 1 & Phase 2 complete — entering Phase 3 (MLOps / Deployment)

## Overview

This project combines two complementary data sources to answer questions about NSE-listed companies:

- **Company annual reports (PDFs)** — via a RAG pipeline, for qualitative/narrative questions (risk factors, management commentary, strategy, business outlook)
- **Live/structured financial data (yfinance)** — for numeric/quantitative questions (revenue, ratios, live prices, financial metrics)

An agentic layer sits on top of both, deciding which tool(s) to call per question and chaining them when needed (e.g., fetching two years of data before calculating growth).

The system is built entirely with free, local tools — no paid APIs required.

## Companies Covered

Adani, Infosys, Reliance Industries, SBI, Tata Motors — FY 2025-26 annual reports and live market data.

## Architecture

```
                        ┌─────────────────────┐
                        │   User Question      │
                        └──────────┬───────────┘
                                   │
                        ┌──────────▼───────────┐
                        │   Agent (qwen2.5:7b)  │
                        │   decides which       │
                        │   tool(s) to call      │
                        └──────────┬───────────┘
              ┌────────────────────┼────────────────────┐
              │                    │                     │
    ┌─────────▼────────┐ ┌─────────▼─────────┐ ┌─────────▼─────────┐
    │ search_documents   │ │ get_live_price /   │ │ calculate_* tools  │
    │ (RAG over PDFs)     │ │ get_financial_     │ │ (P/E, growth,      │
    │                     │ │ metrics (yfinance) │ │ margins, ROE, etc) │
    └─────────┬──────────┘ └─────────┬─────────┘ └─────────┬─────────┘
              │                      │                      │
              └──────────────────────┴──────────────────────┘
                                   │
                        ┌──────────▼───────────┐
                        │  tool_sanitizer.py     │
                        │  - format validation   │
                        │  - grounding check     │
                        │    (blocks fabricated  │
                        │    calculator inputs)  │
                        └──────────┬───────────┘
                                   │
                        ┌──────────▼───────────┐
                        │   Final grounded       │
                        │   answer + sources     │
                        └───────────────────────┘
```

**Phase 1 (RAG) pipeline detail:**
```
PDFs → text extraction (pdfplumber) → chunk-level table filtering →
chunking → local embeddings (MiniLM) → FAISS vector index →
retrieval → prompt construction → local LLM generation → grounded answer
```

## Roadmap

- [x] **Phase 1: RAG pipeline** (Days 1-7)
  - [x] PDF ingestion, extraction, chunk-level table filtering
  - [x] Local embeddings (MiniLM) + FAISS vector search
  - [x] Local LLM generation with source citations
  - [x] Formal evaluation (25-question set) — see [`PHASE1_NOTES.md`](./PHASE1_NOTES.md)
- [x] **Phase 2: Agentic layer** (Days 9-13)
  - [x] Live financial data tool (yfinance) — price, TTM, and fiscal-year-specific metrics
  - [x] Calculator tool — 10 financial ratio/growth functions
  - [x] RAG search wrapped as a callable tool with company filtering
  - [x] Tool-calling agent (qwen2.5:7b) with argument sanitization and grounding verification
  - [x] Debugged and documented 6 distinct failure modes — see [`PHASE2_NOTES.md`](./PHASE2_NOTES.md)
- [ ] **Phase 3: MLOps / deployment** (Days 14-18)
  - [ ] FastAPI wrapper
  - [ ] Request logging
  - [ ] Experiment tracking
  - [ ] Docker containerization
  - [ ] Final documentation and polish

## Phase 1 Evaluation Summary

25 hand-written questions, manually scored against ground truth from the source PDFs:

| Metric | Result |
|---|---|
| Retrieval accuracy | 72% (18/25) |
| Answer accuracy | 28% (7/25) |
| Citation accuracy | 48% (12/25) |

**Key finding:** RAG performs well on narrative/qualitative questions but poorly on precise numeric questions, since financial tables get filtered out during extraction rather than properly structured. This directly motivated Phase 2's decision to route numeric questions to live data instead. Full details in [`PHASE1_NOTES.md`](./PHASE1_NOTES.md).

## Phase 2 Highlights

Building the agent surfaced six distinct, real failure modes during development — from malformed tool arguments to a small model writing fake tool-call text instead of using real function-calling, to a subtler bug where the agent fabricated plausible-but-fake numeric inputs to a calculator tool without ever fetching real data. Each was debugged, fixed, and documented rather than papered over. Full debugging journey, root causes, and fixes in [`PHASE2_NOTES.md`](./PHASE2_NOTES.md).

**Key engineering addition:** a two-layer tool-call sanitizer (`tool_sanitizer.py`) that (1) validates argument format/types before execution, and (2) verifies every calculator input is *grounded* — i.e., actually matches a real number returned earlier in the conversation — rather than trusting the model's arguments at face value.

## Tech Stack

- **PDF processing:** pdfplumber
- **Embeddings:** sentence-transformers (`all-MiniLM-L6-v2`) — local, free
- **Vector search:** FAISS (CPU, exact search)
- **LLM (agent + generation):** qwen2.5:7b via Ollama — local, free, custom Modelfile with tuned temperature/top_p
- **Live financial data:** yfinance
- **Planned (Phase 3):** FastAPI, Docker, experiment tracking

## Project Structure

```
data/
  raw_pdfs/            # source annual report PDFs (not tracked)
  extracted_text/      # raw extracted text per company (not tracked)
  chunks/              # filtered, chunked text per company (not tracked)
  embeddings/          # chunk embeddings per company (not tracked)
  faiss_index.bin      # FAISS vector index (not tracked)
  chunk_metadata.pkl   # chunk metadata for retrieval lookup (not tracked)

# Phase 1 — RAG
check_pdfs.py               # PDF sanity check
extract_text.py              # PDF text extraction
chunk_text.py                 # chunk-level table filtering + chunking
generate_embeddings.py         # local embedding generation
build_index.py                  # FAISS index construction
generate_answer.py               # standalone full RAG pipeline (retrieve + generate)
eval_questions.json                # Phase 1 evaluation set
run_evaluation.py                   # Phase 1 eval runner
summarize_eval.py                    # Phase 1 eval scoring
PHASE1_NOTES.md                       # Phase 1 problems/fixes/limitations

# Phase 2 — Agentic layer
tools_document_search.py    # RAG search wrapped as a standalone tool
tools_live_data.py           # live price + financial metrics (yfinance)
tools_calculator.py           # financial ratio/growth calculators
tools_schema.py                 # tool definitions (JSON schema) passed to the LLM
tool_sanitizer.py                 # argument validation + grounding verification
Modelfile                          # custom Ollama model (qwen2.5:7b + tuned params)
agent.py                            # tool-calling orchestration loop
agent_eval_questions.json             # agent evaluation set
run_agent_evaluation.py                 # agent eval runner
summarize_agent_eval.py                   # agent eval scoring
PHASE2_NOTES.md                            # Phase 2 debugging journey + limitations
```

## Notes

Large data files (PDFs, extracted text, chunks, embeddings, the FAISS index) are excluded from version control via `.gitignore`. To reproduce: place annual report PDFs in `data/raw_pdfs/`, run the Phase 1 pipeline scripts in order, then `ollama create finance-agent -f Modelfile` before running `agent.py`.
