# REPLICATION.md — reproduce, audit, or extend this project

Everything below lives in this repository (`bank boards_cumulative-sludge/`). The pipeline replays **offline** from committed caches — no API key or network needed to verify any result; keys/network are required only to extend it.

## Read in this order (cold start)

| # | File | What it gives you |
|---|------|-------------------|
| 1 | `release/method_summary_3-pages.docx` | The whole method in 3 pages |
| 2 | `release/method_from-227-to-26_policymaker-edition.docx` | Full non-technical narrative, chapter per stage |
| 3 | `README.md` | Stage 1: the inventory horserace — producers, judges, rubric |
| 4 | `Tools/policy-sludge-rubric-v2.md` + `policy-sludge-llm-judge-prompt-v2.md` + `sludge-report-evaluation-instructions.md` | Stage 1 harness: reproduce the evaluation end to end |
| 5 | `Synthesis/gsib-board_duties-combined_inventory.xlsx` | The 227-row two-layer inventory (primary data input) |
| 6 | `boarddistill/specs/statutedistill-prd-v0.2.md` | Stage 2: the engine PRD (calculus, effect classes, gates) |
| 7 | `lex-allium_feasibility_board-duties.md` → `boarddistill-prd-v0.1.md` | Stage 3: the banking port — feasibility, then the project PRD |
| 8 | `B0_calculus-closure.md` + `b0_decompositions.json` | Stage 4: the closure test; DEEM_SATISFIED evidence |
| 9 | `boarddistill/AGENTS.md` | Stage 5 build contract: 12 invariants, tests, tasks T0–T9 |
| 10 | `boarddistill/B1_TASKS.md` … `B6_TASKS.md` | Stages 6–9 instruction files (verification, dispositions, AI layer, scale, benchmark) — each self-contained |
| 11 | `B5_residual-closure.md` + `b5_residual_decompositions.json` | Corpus-scale closure result; 3 named composites |
| 12 | `boarddistill/outputs/b1 … b6/` | Every stage's results, reports, and eval artifacts |
| 13 | `REVIEW_CHECKLIST.md`, `REVIEW_PACKET_B3.md`, `REVIEW_PACKET_B5.md` | The human decision record (~60 dispositions) |
| 14 | `release/` | The product: proposal, crosswalk (xlsx + HTML explorer), dual-track roadmap, graphics — all regenerable from `release_data.json` |

## Verify the results yourself (offline, ~5 minutes)

```
cd boarddistill
uv sync
make check                     # ruff + mypy + full test suite, replayed from committed caches
uv run boarddistill eval-fixture data/fixtures/us-gsib/icfr    # 100% agreement vs gold labels
```

Key artifacts to spot-check: `outputs/b2/verification.json` (every verified claim's pinned verbatim quote + source URL/hash) · `data/llm_cache/` (every model call, keyed by prompt hash) · `outputs/b6/scores.json` (benchmark scoring; answer key under `data/benchmark/answer_key/`).

## Requirements to extend (not to verify)

Python 3.11+ with `uv` · Node (for release-document generation) · `ANTHROPIC_API_KEY` for live LLM passes · network restricted to the allowlist in `boarddistill/B1_TASKS.md` §3 (primary legal sources only).

## To port to another corpus (the adapter recipe)

1. Build/obtain a citation-level inventory (Stage 1 harness is corpus-agnostic).
2. Run a hand closure test (B0 pattern) against the 16 primitives; residuals are proposals, never silent additions.
3. Write the profile: instrument-hierarchy strata, statutory-floor list (human-owned), normative kinds, adapters for the corpus's source formats.
4. Follow AGENTS.md discipline: deterministic fixtures first; AI only behind proven interfaces; every claim span-anchored; every judgment human-gated.

Precedents for step 3: `boarddistill/profiles/lex_balanus/` (banking) and `profiles/lex_allium/` (criminal-law stub). The RBI benchmark (`B6_TASKS.md`) is the template for validating a new port against a real consolidation.
