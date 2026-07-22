# AI Trading Research Assistant

A RAG + agentic AI system for answering questions about NSE-listed companies using their financial filings and live market data — built as a fully local, free pipeline from raw PDFs to a deployed API.

## Status: Complete (Phases 1-3)

## What This Is

Ask a plain-English question about Adani, Infosys, Reliance, SBI, or Tata Motors, and get a grounded answer that pulls from:
- **Annual report filings (PDFs)** — for qualitative questions (risk factors, strategy, management commentary)
- **Live market data (yfinance)** — for numeric questions (price, revenue, ratios)
- **A calculator layer** — for any derived metric (P/E, YoY growth, margins, ROE, ROA, etc.), so the LLM never does arithmetic itself

An agent (running locally via Ollama) decides which tool(s) to call per question, chains them when needed, and the whole thing is exposed as a FastAPI service with request logging and experiment tracking.

## Why This Project

Started as an attempt to make sense of overlapping buzzwords (RAG, agentic AI, MLOps, LLMOps) by building one system that touches all of them in a coherent pipeline, rather than five disconnected tutorials. Also doubles as an early prototype toward a longer-term goal: a quant-driven platform for sharing and evaluating trading strategies.

## Architecture

```
                        ┌─────────────────────┐
                        │   FastAPI (/ask)      │
                        │   + request logging    │
                        └──────────┬───────────┘
                                   │
                        ┌──────────▼───────────┐
                        │   Agent (qwen2.5:7b)  │
                        │   decides which        │
                        │   tool(s) to call        │
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
                        │  format + grounding    │
                        │  verification           │
                        └──────────┬───────────┘
                                   │
                        ┌──────────▼───────────┐
                        │   Grounded answer +     │
                        │   sources, logged        │
                        └───────────────────────┘
```

**Phase 1 (RAG) pipeline detail:**
```
PDFs → text extraction (pdfplumber) → chunk-level table filtering →
chunking → local embeddings (MiniLM) → FAISS vector index →
retrieval → prompt construction → local LLM generation → grounded answer
```

## Roadmap

- [x] **Phase 1: RAG pipeline** (Days 1-7) — see [`PHASE1_NOTES.md`](./PHASE1_NOTES.md)
- [x] **Phase 2: Agentic layer** (Days 9-13) — see [`PHASE2_NOTES.md`](./PHASE2_NOTES.md)
- [x] **Phase 3: MLOps / deployment** (Days 14-16, 18)
  - [x] FastAPI wrapper (`/ask`, `/`)
  - [x] Request logging (JSONL)
  - [x] Experiment tracking (config + metrics comparison)
  - [x] Docker containerization (host-networked Ollama)
  - [x] Final documentation

## Evaluation Summary

**Phase 1 (RAG, 25-question set):**

| Metric | Result |
|---|---|
| Retrieval accuracy | 72% (18/25) |
| Answer accuracy | 28% (7/25) |
| Citation accuracy | 48% (12/25) |

Numeric questions failed disproportionately due to table filtering during PDF extraction — this directly motivated Phase 2's live-data routing decision.

**Phase 2 (Agent, targeted testing across two models):**

| Model | Multi-step tool chains | Notable issues found |
|---|---|---|
| llama3.2:3b | Unreliable | Malformed arguments, field misuse, fake tool-call text |
| qwen2.5:7b | Reliable in testing | Silent numeric fabrication (fixed via grounding verification) |

Six distinct failure modes were found, debugged, and fixed or documented across Phase 2 — see `PHASE2_NOTES.md` for the full journey, including the grounding-verification layer that catches fabricated calculator inputs before they can produce confidently-wrong answers.

## Tech Stack

- **PDF processing:** pdfplumber
- **Embeddings:** sentence-transformers (`all-MiniLM-L6-v2`) — local, free
- **Vector search:** FAISS (CPU, exact search)
- **LLM (agent + generation):** qwen2.5:7b via Ollama — local, free, custom Modelfile
- **Live financial data:** yfinance
- **API:** FastAPI + Uvicorn
- **Logging/tracking:** custom JSONL-based request and experiment logs

## Known Limitations (honest, not hidden)

- PDF table extraction discards rather than structures tabular data — numeric PDF-only questions (not covered by live data) remain unreliable
- Ticker mappings are hardcoded and require manual updates after corporate actions (e.g., the Tata Motors demerger encountered during this build)
- Grounding verification uses tolerance-based numeric matching — could rarely misflag a legitimate recalculated value
- No formal, scored evaluation set for the agent yet (Phase 1 had this rigor; Phase 2 validation was targeted/manual)
- Docker setup runs the app in a container but relies on Ollama running on the host machine (via `host.docker.internal`) rather than being fully self-contained — a reasonable middle ground for a local project, not a full production deployment pattern
- Local 7B-parameter generation is capable but not infallible — occasional fabrication risks remain even with grounding checks, particularly for failure modes not yet encountered in testing

## Project Structure

```
data/                          # PDFs, extracted text, chunks, embeddings, FAISS index (not tracked)
logs/                          # request + experiment logs (not tracked)

# Phase 1 — RAG
check_pdfs.py, extract_text.py, chunk_text.py, generate_embeddings.py,
build_index.py, generate_answer.py, eval_questions.json,
run_evaluation.py, summarize_eval.py, PHASE1_NOTES.md

# Phase 2 — Agentic layer
tools_document_search.py, tools_live_data.py, tools_calculator.py,
tools_schema.py, tool_sanitizer.py, Modelfile, agent.py,
agent_eval_questions.json, run_agent_evaluation.py,
summarize_agent_eval.py, PHASE2_NOTES.md

# Phase 3 — MLOps
api.py, request_logger.py, experiment_tracker.py
```

## Running This Project

1. Place annual report PDFs in `data/raw_pdfs/`
2. Run the Phase 1 pipeline in order: `extract_text.py` → `chunk_text.py` → `generate_embeddings.py` → `build_index.py`
3. `ollama create finance-agent -f Modelfile`
4. Either run directly: `uvicorn api:app --reload`
   or via Docker: `docker build -t trading-assistant .` then
   `docker run -p 8000:8000 -e OLLAMA_HOST=http://host.docker.internal:11434 trading-assistant`
   (Ollama must be running on the host machine either way)
5. Visit `http://127.0.0.1:8000/docs` to test

## Notes

Large/generated files are excluded from version control via `.gitignore`. This project prioritizes honest, documented engineering — every phase's README notes real problems encountered and how (or whether) they were resolved, rather than presenting a frictionless narrative.