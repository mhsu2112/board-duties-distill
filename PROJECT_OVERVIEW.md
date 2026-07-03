# BoardDistill — Project Overview Memo

**To:** Mike Hsu · **Date:** July 2, 2026 · **Status:** ~~Slice one built and verified~~ → **MVP arc complete (B0–B4)**

> **Addendum — end of day, July 2, 2026.** Since this memo was written, four further phases ran and closed: **B1** citation verification (21/72 verified, 0 contradicted), **B2** appendix/SR/manual resolvers + instrument graph (50/72 verified; 6 actor retags), **B3** the LLM layer (three consolidation packages; 0 hallucinated citations; caught 10 mispinned rows and the two-duplication-families result), and **B4** review-disposition write-back + defect closure (all 10 re-pins fixed, concept-node graph, **8/9 B0 effect-class agreement**, zero unresolved). All 28 human dispositions recorded via `REVIEW_PACKET_B3.md`. Headline empirical findings: zero fabricated/invented duties after four audit passes; 41/50 duties state no board-action standard; duplication has two distinct structures (`mirror_pair` vs `restatement`). Full trail: `boarddistill/B1_TASKS.md`–`B4_TASKS.md` and `boarddistill/outputs/b1–b4/`. **Remaining arcs (not started):** scale-out to ~27 clusters; RBI Master-Directions rediscovery benchmark; minor carry-forwards (10-row re-distill needs API key; D9 characterized disagreement; D7 disposition rule refinement).

---

## 1. What's been done

This project applies the Transformation Calculus from the StatuteDistill/Lex-Allium work (criminal-code recodification) to a new domain: consolidating the ~230 accreted board duties of Category I U.S. GSIBs. Five stages, in order:

**Feasibility (memo).** Mapped the 15 engine primitives onto the bank-board corpus. Verdict: portable, and easier than the criminal case in key respects — the case-law authority graph is replaced by a simpler supervisory-instrument hierarchy, and the existing inventory is already a proto-canonical-schema. Three adaptations identified: an instrument hierarchy with rescission tracking, banking-typed relations and duty standards, and a multi-agency authority-to-act field.

**PRD.** A cold-start-replicable spec framing the project as the first non-criminal *adapter* over the shared StatuteDistill engine (profile name: Lex-Balanus). Key domain-specific commitments: the binding-vs-non-binding fork (no silent guidance↔rule conversion), a statutory floor no consolidation may touch, "parallel-but-justified" as a first-class outcome, and honesty about the confidential-supervisory-information gap.

**B0 — calculus closure test.** Hand-decomposed every reform lever in the three biggest duplicate clusters (risk governance, audit committee, capital planning; 62 duty rows) into primitive compositions. Result: the set closes with **one genuine addition — `DEEM_SATISFIED`** ("compliance with X deemed compliance with Y"), which fires in five independent levers and is the *only* primitive able to express the corpus's largest reform (vertical HC/IDI rationalization, where both duties must legally survive). One generalization: `ASSIGN_DUTY_PARAMETER` (covers verb-standard and cadence changes). Both were human-approved. Final enum: **16 primitives**.

**Build contract (AGENTS.md).** A precise Claude Code build order: profile-parameterized core, 12 in-code invariants (8 inherited + binding-force conservation, statutory floor, APA pathway, DEEM_SATISFIED survival), three fixtures drawn from B0, 11 required behavioral tests, tasks T0–T9.

**The build (Claude Code, T0–T9, 11 commits).** Complete. Independently re-verified today in a clean environment:

- `make`-gate green: **84/84 tests pass**, ruff clean.
- `eval-fixture` on the primary fixture: **100% agreement** on operations, effect classes, and dispositions vs. gold labels; **zero residuals**.
- All three fixtures run end-to-end; the rendered `package.md` correctly shows the findings table, authority-to-act table, claim verification, review queue, and a final-status blocker summary that **blocks finalization** on the two open normative items — the central guardrail, working.
- T8 adapter imported **227 draft DutySpecs** from the inventory, every claim marked unverified and none finalizable — as designed.

## 2. Where things stand

The deterministic skeleton is proven: schema → fixtures → instrument graph → diagnostics → operations → invariants → classification → verification → review gates → rendered package, all reproducible, with the normative and verification gates enforced in code rather than prose. Nothing probabilistic has been introduced yet — no LLM, no retrieval — which is exactly the slice-one contract.

**Open items — ALL RESOLVED July 2, 2026** (decisions via `REVIEW_CHECKLIST.md`: items 1 & 3 confirmed as drafted; item 2 confirmed with DFA §165(d) added to the statutory floor; items 4–5 executed — prose counts reconciled across all docs, everything committed to git). Original list retained for the record:

1. Confirm the fixture placeholder labels/citations (three fixture `sources.json` files) — required before B1.
2. Confirm `statutory_floor.json` v1 anchors (draft: DFA 165(h)/(i), SOX 301, FDI Act §36/Part 363, BSA program statutes).
3. Confirm the T8 column mappings (Layer→legal_force, cadence, entity, confidence) before trusting the 227 drafts.
4. Reconcile the primitive-count prose in the four parent docs (they say "fourteen/fifteen"; the enum's ground truth is 16).
5. Housekeeping: the git repo root is the corpus folder, and several project docs are still uncommitted there (`AGENTS.md`, `boarddistill-prd-v0.1.md`, `B0_calculus-closure.md`, `b0_decompositions.json`, the feasibility memo, this memo) plus modified `README.md`/Evals workbook — worth a commit to preserve provenance.

## 3. Suggested next steps (in order)

1. **Adjudicate the five open items above** (~an hour of your review; items 1–3 gate everything downstream).
2. **B1 — full-coverage claim verification** of the ~60 MVP-cluster rows against primary sources, reusing the existing judge harness behind the built `verify` interface. This is the first step requiring retrieval, and it converts the inventory from "LLM-synthesized draft" to trusted L1 input.
3. **Instrument-graph ingestion**: eCFR/US Code parsing plus the archival rescission reconstruction (`rescinded_informal`) — the navigability problem your Substack post identified becomes a first-class data product here.
4. **Introduce the LLM layer** behind the proven interfaces (distill/diagnose/classify; temperature 0, span-anchored claims) and run the three MVP clusters end-to-end for real — producing the first reviewable consolidation packages.
5. **Scale + benchmark**: remaining ~27 clusters; then the RBI Master-Directions rediscovery benchmark and baselines (the horserace reports already serve as plain-LLM baselines).
6. Later: `lex_allium` criminal profile build (proves the core is genuinely shared); PRA/FCA adapter scoping.

## 4. Document map

**Corpus folder (`bank boards_cumulative-sludge/`)**

| Document | What it is |
|---|---|
| `README.md` | Original study: horserace methodology, rubric, results |
| `Synthesis/gsib-board_duties-combined_inventory.xlsx` | The ~230-row two-layer duty inventory — primary data input |
| `Synthesis/gsib-board_duties-combined_report.docx` | 67-page narrative companion |
| `Tools/` | Eval harness (rubric v2, judge prompt, protocol, workbook) — becomes the claim-verification layer |
| `Reports/`, `Evals/` | Raw AI reports and judge outputs — the future baselines |
| `lex-allium_feasibility_board-duties.md` | Feasibility assessment (primitives → board duties mapping) |
| `boarddistill-prd-v0.1.md` | The project PRD (cold-start replicable) |
| `B0_calculus-closure.md` + `b0_decompositions.json` | B0 closure test: 10 decompositions, DEEM_SATISFIED evidence, approved amendments |
| `AGENTS.md` | Build contract (authoring copy; the operative copy is in the repo) |
| `PROJECT_OVERVIEW.md` | This memo |

**Build repo (`bank boards_cumulative-sludge/boarddistill/`)**

| Path | What it is |
|---|---|
| `AGENTS.md` | Operative build contract (T0–T9, invariants, checkpoints) |
| `README.md` | Quickstart, CLI, roadmap, dormant guardrails |
| `specs/` | Frozen copies of all parent specs (both PRDs, B0, engine conventions) |
| `distillcore/` | Profile-independent engine: canonical models + pipeline stages |
| `profiles/lex_balanus/` | Banking profile: 16-primitive enum, DutySpec, invariants §2.9–12, `statutory_floor.json` (draft, human-owned) |
| `profiles/lex_allium/` | Criminal-profile stub (future) |
| `data/fixtures/us-gsib/` | The three B0 fixtures (`icfr`, `sr12-17`, `board-effectiveness`) + `_calculus` mirror stub — all openly placeholder |
| `outputs/run/`, `outputs/final/` | Rendered consolidation packages (`package.md` = the reviewable artifact) |
| `outputs/import/imported_duties.json` | 227 draft DutySpecs from T8 (all unverified by design) |
| `tests/` | 84 tests incl. the 11 required behavioral tests |

**External:** engine folder `statute-distill_lex-allium/` (parent PRD + AGENTS + theft fixture) · Substack post (context) · `policy-sludge-cleanup` skill repo (RBI method) — the rediscovery-benchmark source.

---

*Everything above the LLM layer is deterministic and re-runnable: `uv sync && make check` reproduces the verification in §1.*
