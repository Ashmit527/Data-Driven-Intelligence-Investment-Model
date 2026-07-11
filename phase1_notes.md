# Phase 1: RAG Pipeline — Detailed Notes

This document covers everything built in Phase 1 (Days 1-7): PDF ingestion through evaluation. It records what was built, problems encountered along the way, how they were fixed, and what remains a known limitation going into Phase 2.

## What Phase 1 Built

A retrieval-augmented generation (RAG) pipeline over 5 NSE-listed companies' annual reports (Adani, Infosys, Reliance, SBI, Tata Motors):

```
PDFs → text extraction → chunk-level table filtering → chunking →
local embeddings (MiniLM) → FAISS vector index → retrieval →
prompt construction → local LLM generation (Llama 3.2 3B via Ollama) → answer
```

Entirely free and local — no paid APIs used anywhere in this phase.

## Problems Encountered and Fixes Applied

### 1. Repeated headers/footers polluting extracted text
**Problem:** Every page's extracted text included repeating boilerplate (e.g., "Infosys Integrated Annual Report 2025-26"), adding noise to every chunk.
**Status:** Identified during manual inspection (Day 2). Not yet actively stripped — deprioritized since it didn't measurably hurt retrieval/generation quality in evaluation. Candidate for future cleanup.

### 2. Jumbled tables mixed with narrative text on the same page
**Problem:** `pdfplumber`'s default `extract_text()` flattens tables into unstructured, column-agnostic text (e.g., financial subsidiary tables became unreadable strings of numbers and labels with no row/column structure).
**First fix attempted:** Page-level heuristic filtering (drop whole pages that look table-heavy). Result: severely under-filtered (1-7 pages skipped out of 200-500+ per company) because most pages mix narrative and tabular content together.
**Second fix (current state):** Moved filtering to the **chunk level** instead of page level, using a heuristic combining digit density, symbol density (`–`, `%`, `()`), and sentence-structure detection (regex-based period+capital-letter frequency). This meaningfully improved filtering (45-90 chunks skipped per company vs. single digits before) and was verified by manual spot-checking.
**Remaining limitation:** This is a heuristic filter, not true table extraction — flagged table-like chunks are simply **dropped**, not preserved in usable form. This means numeric data inside tables is largely unavailable to the RAG pipeline. Confirmed directly via Day 7 evaluation (see below).

### 3. Citation/source misattribution in generated answers
**Problem:** The LLM (Llama 3.2 3B) sometimes cited the wrong source number for a claim (e.g., attributing a fact to "Source 1" when it actually came from "Source 2").
**Fix:** Strengthened the prompt with an explicit instruction to double-check that cited source numbers match their actual labeled content before including them. This measurably reduced (but did not eliminate) mismatches — citation accuracy in formal evaluation was 48% (12/25), with most remaining errors concentrated in the same questions that also had numeric/table-based answer failures (see below), suggesting the underlying cause is garbled retrieved content rather than a purely separate citation bug.

### 4. Local LLM hallucination when ungrounded
**Observed directly:** Asking `llama3.2:3b` a general knowledge question ("What is RAG?") with no retrieved context produced a fluent but entirely fabricated answer. This was a deliberate sanity check (not part of the actual pipeline) and served as a concrete demonstration of why grounding via retrieval matters — the same model, when given real retrieved context and instructed to answer only from it, performs far more reliably.

## Formal Evaluation Results (Day 7)

25 hand-written questions across factual, narrative, financial, operational, and risk categories, run through the full pipeline and manually scored against ground truth read directly from the source PDFs.

| Metric | Result |
|---|---|
| Retrieval accuracy | 18/25 (72%) |
| Answer accuracy | 7/25 (28%) |
| Citation accuracy | 12/25 (48%) |

**Key finding — the gap between retrieval accuracy (72%) and answer accuracy (28%) is the central result of this evaluation.** Breaking down *why* answers failed even when retrieval succeeded:

- **Retrieval correct, but model declined to answer anyway: 7 cases** — the right page was retrieved, but the answer within it was too garbled (from table-jumbling during extraction) for the model to extract confidently. The model behaved honestly here (declining rather than hallucinating), but the pipeline still failed to deliver value.
- **Retrieval failed, model correctly declined: 4 cases** — expected, honest behavior when the right content genuinely wasn't retrieved.
- **Retrieval failed, model answered anyway: 3 cases** — the more concerning failure mode (possible hallucination), worth closer review.

**Failure pattern by question type:** nearly all answer failures were on specific numeric/financial figures (revenue, EBITDA, net profit, dividends, NPA ratios, net debt, employee counts) — i.e., exactly the kind of data that lives in financial summary tables. Narrative/qualitative questions (e.g., risk framework descriptions, strategic commentary) performed considerably better, though not perfectly (2 narrative-type failures out of the 25).

**Conclusion:** the current RAG pipeline is reasonably reliable for qualitative/narrative questions about these filings, but is not a good fit — as currently built — for precise numeric lookups, because the chunk-level table filter discards rather than properly structures tabular data.

## Path Forward: Why Table Extraction Is Deferred, Not Abandoned

Two options existed to fix the numeric-answer weakness:
1. Build proper table extraction (`pdfplumber.extract_tables()`, reformatted as markdown before embedding)
2. Route numeric/financial-metric questions to a structured data source (OpenBB) instead of RAG, in Phase 2's agentic layer

**Decision: pursue option 2 first.** Numeric figures like revenue, EBITDA, dividends, and financial ratios are exactly the kind of structured data OpenBB is designed to serve directly and reliably — arguably a more architecturally correct fit than asking an LLM to extract numbers from re-flattened PDF text at all. Phase 2 will add OpenBB as an agent tool for exactly these question types.

**Table extraction (option 1) remains on the roadmap** and will be revisited if, after Phase 2, numeric questions not covered by OpenBB (e.g., specific report-only tables without a live-data equivalent) still show poor accuracy. This is a deliberate, evidence-based sequencing decision — not a dropped requirement.

## Known Limitations Going Into Phase 2

- Repeated headers/footers not yet stripped from extracted text (minor, low priority)
- Financial tables inside PDFs are filtered out rather than properly extracted — affects numeric-question accuracy specifically
- Citation accuracy (48%) needs improvement; largely tied to the table/numeric issue above, expected to improve indirectly once numeric queries are routed away from RAG
- Local 3B-parameter LLM generation is noticeably weaker than larger models on complex multi-source reasoning; acceptable trade-off given zero-cost/local constraint
