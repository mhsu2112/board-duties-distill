# B3_TASKS.md — The LLM layer: distill · diagnose · classify → first real consolidation packages

**Audience:** an autonomous coding agent (Claude Code terminal). `AGENTS.md`, `B1_TASKS.md` §3 (retrieval rules), and `B2_TASKS.md` remain binding. This file lifts the last slice-one restriction: **LLM calls are now permitted**, under the §2 harness rules only.

**Human dispositions recorded (M. Hsu, 2026-07-02, via chat — authority for this file):**
1. The **22 B2 residuals are accepted as documented residuals** — no further anchor-matching work; they stay `unverified` with reasons and do not block B3.
2. **s:CAP-11 is reclassified**: it is a supersession/currency record (SR 09-4 superseded per SR 15-18 fn.5), **not a duty row**. Remove the placeholder actor-retag; mark the row `record_type: supersession_note`, excluded from duty counts and packages but retained in the instrument graph as treatment evidence.
3. **SR 95-51 treatment** is to be resolved *from the Fed's SR-letter index/page* (B3-T0), not from memory.

**Mission:** introduce LLM-based distillation, diagnostics, and effect classification behind the interfaces slice one proved, run the three MVP clusters end-to-end, and render the first evidence-backed, reviewable **per-cluster consolidation packages** — then measure agreement against the B0 gold decompositions.

---

## 1. What the LLM may and may not do

- **May:** propose duty-element structure from cached source text; draft consolidated duty language; propose diagnostics, operations, and effect classes; draft rationales.
- **May not:** assert any legal claim without a `SourceSpan` into the **cached corpus** (`data/sources/`) — retrieval-only authority, no model-memory citations; resolve a normative flag; touch effect classes governed by mechanical rules (the per-se force rule stays in code); finalize anything. Every LLM output lands as `draft`, flows through the same invariant/verification/review gates as everything else.

## 2. LLM harness rules (build first, `distillcore/llm.py`)

- Pinned model + version string in one config constant; **temperature 0**; structured output validated against the Pydantic schemas (reject-and-retry once on schema failure, then hard-fail).
- **Response cache**: every call keyed by `(model, prompt_sha256)` and stored under `data/llm_cache/`; replay is the default. `make check` runs entirely from cache — deterministic, no keys needed. Live calls require `--live` and `ANTHROPIC_API_KEY`; **if the key is absent, stop and write `TODO(human): export ANTHROPIC_API_KEY` — do not improvise another provider.**
- Prompt templates live in `profiles/lex_balanus/prompts/` as versioned files, not inline strings. Each template states the span-anchoring requirement and the "unresolved over guess" rule verbatim.
- A per-run budget guard (max calls, max tokens) with a visible counter in the run log.

## 3. Build order (each ends green on `make check`; commit per task)

- **B3-T0 Apply dispositions + SR 95-51.** Items 1–3 above: accept-residual dispositions (reviewer "mhsu"); s:CAP-11 reclassification; fetch the Fed's SR-letter index / SR 95-51 page (allowlisted), determine its current treatment status from what the page says, update the instrument node with the evidence quote. If the page is ambiguous, record candidates and checkpoint. *DoD:* dispositions persisted; s:CAP-11 excluded from duty counts (now 71 target rows); SR 95-51 node evidenced or checkpointed.
- **B3-T1 LLM harness.** §2 in full, plus unit tests: schema-reject path, cache round-trip, budget guard, missing-key stop. *DoD:* replay-mode tests green with an empty cache (harness never silently calls live).
- **B3-T2 Distill (as-built).** For the 50 verified rows: LLM refines each draft DutySpec against its cached source text — precise verb/object, cadence, definitions used, intra-duty structure — every field span-anchored; anything the text doesn't support stays `unresolved`. Cross-check: `verb_standard` proposals that contradict a B2 retag are flagged, never overwritten. *DoD:* 50 distilled as-built DutySpecs, all claims `verified` against existing spans; diff-vs-draft report.
- **B3-T3 Intended layer.** Express the B0 decompositions (D1–D9, as amended by B2/B3 dispositions) as full intended DutySpecs + Operation records: LLM drafts the consolidated duty text (illustrative draft, marked as such — NG2) with citations to every operand; operations scaffolded from `b0_decompositions.json`, not re-derived. *DoD:* intended specs for the three MVP clusters; every operation resolves its operands; composition validation passes.
- **B3-T4 Diagnose + classify.** LLM-assisted diagnostics over the distilled corpus (duplicate duty, rule-guidance restatement, undefined term, actor ambiguity…), each with span evidence; effect classification per finding via `baseline_for` diffs, with the mechanical rules (per-se force conversion; no-baseline ⇒ unresolved) applied **in code after** the LLM proposal. Where the LLM's diagnostic set diverges from the Duplicate Clusters sheet, record the divergence — both directions are findings. *DoD:* findings for all three clusters with effect classes, normative kinds, dispositions defaulting per the §2 rules of AGENTS.md.
- **B3-T5 Render the packages.** Three per-cluster consolidation packages (`outputs/b3/<cluster>/package.md`): the full §9 AGENTS.md contents — findings table, duty crosswalk, authority-to-act, claim verification, normative review queue, blocker summary. **Expected state: everything blocked pending human review — that is success, not failure.** *DoD:* three packages render; zero findings `final`.
- **B3-T6 Eval.** (a) Agreement vs. B0 gold: operation-set and effect-class agreement per decomposition, disagreements characterized (never reconciled). (b) Stability: 3 live samples per pipeline stage on one cluster, agreement across samples (then cached). (c) Citation integrity: hallucinated-citation rate must be **zero** — any span that doesn't resolve to the cache is a release-gate failure. (d) Baseline comparison: the same cluster's rows from the raw synthesis inventory, scored with the same checks. *DoD:* `outputs/b3/eval_report.md` with all four.
- **B3-T7 Report + README.** `outputs/b3/B3_report.md`: what the LLM layer added beyond the deterministic pipeline, agreement/disagreement summary, the human review queue (this is now the main artifact for M. Hsu), budget spent. *DoD:* full suite green from cache; all committed.

## 4. Checkpoints (stop, `TODO(human)`, leave a draft)

1. Any LLM output with an unanchorable claim (span missing or not resolving to cache) — this is a bug *and* a gate; record and fix the harness, never pass it through.
2. LLM-vs-B0-gold disagreement on an operation or effect class — record as a characterized disagreement; do not edit the gold.
3. Any newly proposed operation type beyond the 16-primitive enum (§14.2 discipline — propose only).
4. SR 95-51 ambiguity (B3-T0); any normative disposition; any budget-guard breach; missing API key.
5. Consolidated-duty draft language that changes substance relative to its operands (the classifier should catch it as `change`; if the LLM argues `codify`, surface the conflict, don't resolve it).

## 5. Definition of done

Three reviewable consolidation packages with every finding evidence-anchored and gated; eval report with B0 agreement, stability, zero hallucinated citations, and the baseline comparison; s:CAP-11 and SR 95-51 resolved or checkpointed; `make check` deterministic from cache; all committed.

**After B3, the human review pass over the packages is the next event — the packages queue is built for exactly that. Scaling to all clusters and the RBI benchmark are separate future files; do not start them.**

---

**Begin at B3-T0.**
