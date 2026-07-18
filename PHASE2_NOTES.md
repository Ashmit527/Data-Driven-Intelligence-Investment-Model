# Phase 2: Agentic Layer — Detailed Notes

Covers Days 9-13: building live-data, calculator, and document-search tools, then wiring them into a tool-calling agent.

## What Was Built

Three independent tools, unified under one agent that decides which to call per question:

- **`tools_live_data.py`** — live price, TTM metrics, and fiscal-year-specific financial metrics via `yfinance`
- **`tools_calculator.py`** — 10 deterministic financial calculations (P/E, YoY growth, margins, ROE, ROA, CAGR, etc.), so the LLM never does arithmetic itself
- **`tools_document_search.py`** — the Phase 1 RAG search, repackaged as a standalone callable tool with company filtering
- **`agent.py`** — the orchestration loop: LLM reads the question, decides which tool(s) to call, executes them, and synthesizes a final answer
- **`tool_sanitizer.py`** — validates and grounds every tool call before it executes (details below)
- **`Modelfile`** — custom Ollama model definition (base model, temperature/top_p, system prompt) built via `ollama create`

## Key Architectural Decision (carried over from Phase 1)

Numeric/financial-metric questions are routed to live data (`yfinance`) instead of extracting tables from PDFs, since Phase 1 evaluation showed PDF table extraction was the main source of failure for exactly this question type. This was validated during Phase 2 — live data tools returned clean, reliable figures across all 5 companies without needing table-extraction work.

## Debugging Journey — Problems Found and Fixes Applied

### 1. Ticker mapping went stale (real-world data lesson)
Tata Motors underwent a corporate demerger (commercial vs. passenger vehicles now separately listed). The old ticker `TATAMOTORS.NS` no longer resolved; corrected to `TMCV.NS`. Documented as a maintenance consideration: ticker mappings require periodic review as corporate actions occur.

### 2. Malformed tool arguments from the LLM
Initial testing (with `llama3.2:3b`) showed the model frequently passing invalid arguments to calculator tools — literal string `"null"` instead of real numbers, empty bracket strings like `"[[]]"`, and invented parameters not accepted by the function (e.g., an extra `"year"` field, or passing a tool's *name* as if it were a numeric value).
**Fix:** built `tool_sanitizer.py` — validates arguments against each tool's expected parameter set before execution, rejecting malformed/unexpected values with a clear error fed back to the model, rather than crashing or silently producing wrong results.

### 3. Field misuse producing mathematically impossible results
Most serious bug found in early testing: the agent computed "SBI's net profit margin" using `diluted_eps` (a per-share earnings figure) as if it were a full margin calculation, producing a nonsensical 219.6% margin (margins cannot exceed 100%) — stated with full confidence, no calculator tool called at all.
**Fix:** tightened tool descriptions to explicitly warn against field substitution (e.g., "diluted_eps is NOT net profit margin"), and added a hard system-prompt rule requiring the calculator tool to be called for any percentage/ratio claim.

### 4. Model writing fake tool-call JSON as plain text instead of using real function-calling
After a sanitizer rejection, `llama3.2:3b` would sometimes respond by describing the next tool call in its text output (e.g., `{"name": "get_financial_metrics", ...}` as a printed string) rather than actually invoking the function-calling mechanism again — leaving the task incomplete.
**Fix (two-layered):**
- Prompt-level: explicit instruction never to write tool calls as text.
- Code-level: `looks_like_fake_tool_call()` regex detector in `agent.py`, which catches this pattern and sends a corrective nudge back to the model (capped at 2 retries) rather than accepting the broken response as final.

### 5. Model capability ceiling — upgraded from llama3.2:3b to qwen2.5:7b
After applying sanitization, tightened schemas (including `enum` constraints on company keys), lowered temperature (0.2) and top_p (0.8) for more deterministic output, and the fake-tool-call detector, `llama3.2:3b` still struggled to reliably complete multi-step tool chains (fetch → fetch → calculate). Switched the underlying model to `qwen2.5:7b` via a custom Ollama Modelfile (same system prompt and generation parameters, larger base model). This meaningfully improved multi-step chaining — correct, fully-grounded answers for net profit margin and YoY growth calculations, each involving 2-3 correctly sequenced tool calls with real, correctly-typed arguments.

### 6. Silent numeric fabrication in single-step calculator calls (found after upgrading to qwen2.5:7b)
Even after fixes 1-5, a new and more concerning failure appeared: when asked for Adani's P/E ratio, the agent called `calculate_pe_ratio` directly with plausible-looking but entirely fabricated `price` and `eps` values — without ever calling `get_live_price` or `get_financial_metrics` first. The result was clean, confidently stated, and structurally well-formed (unlike earlier bugs), which made it harder to catch — the sanitizer's format checks passed, since the numbers were valid floats, just not real ones.

**Fix:** added a "grounding" verification layer to `tool_sanitizer.py`:
- `extract_numeric_values()` recursively scans every successful data-tool result (get_live_price, get_financial_metrics) and builds a running pool of every real number actually returned so far in the conversation.
- `verify_calculator_grounding()` checks, before any calculator tool executes, that every numeric argument matches (within a small tolerance for rounding) something genuinely present in that pool. If not, the call is blocked with an error instructing the model to fetch real data first.
- This closes the specific gap the format-only sanitizer could not catch: well-formed but invented numbers.

## Evaluation Summary (informal, based on repeated targeted testing rather than a full scored set)

- Single-tool questions (live price, document search): reliable across both models tested
- Multi-tool sequential chains (fetch two periods → calculate): unreliable on `llama3.2:3b`, notably improved on `qwen2.5:7b`
- Single calculator call with silently fabricated inputs: caught and blocked after adding the grounding verification layer (fix #6)

**This phase's honest conclusion:** tool-calling reliability scales meaningfully with model size for multi-step chains, but even a capable model is not guaranteed to ground every single-step calculation in real data — defensive verification of tool inputs against actual retrieved values (not just format validation) is necessary for a trustworthy agent, and was added as a core part of the architecture rather than left as a documented gap.

## Remaining Known Limitations Going Into Phase 3

- Grounding verification uses a tolerance-based numeric match — in rare cases, a legitimately recalculated or rounded value might be incorrectly flagged; this hasn't caused issues in testing so far but is worth monitoring
- Ticker mappings are hardcoded and will require manual updates if further corporate actions occur (demergers, renames, delistings)
- No formal, scored evaluation set for the agent yet (Day 7-style rigor) — current validation is targeted, repeated manual testing against known problem cases, not a comprehensive scored benchmark
