# B6_TASKS.md — The RBI Master-Directions rediscovery benchmark (held-out research result)

**Audience:** an autonomous coding agent (Claude Code terminal). All prior contracts remain binding: `AGENTS.md`, `B1_TASKS.md` §3 (cache discipline), `B3_TASKS.md` §2 (LLM harness), plus the B5 residual-closure outcomes (`specs/B5_residual-closure.md`): the three approved composites and the held-out-dial rule. **Requires `ANTHROPIC_API_KEY`.**

**Human authority (M. Hsu, 2026-07-02):** benchmark approved; sample-based design (5–10 Master Directions) approved.

**The research question (banking PRD §13):** given only pre-consolidation RBI circulars, does the calculus engine independently recover the *structural* moves of the RBI's 2021–2025 consolidation — which circulars group into which consolidated instrument, what is repealed, what survives and relates — scored against RBI's published mapping as the held-out answer key, **with RBI's substantive policy choices never scored**. This is the rediscovery benchmark the engine PRD (§3, §13) reserved from day one; a strong result is the citable evidence that the calculus generalizes across regulators and jurisdictions, and a weak result is a finding about where it doesn't. **Both outcomes are reportable; do not optimize toward agreement.**

---

## 1. Benchmark design (read before building)

**1.1 Sample.** 5–10 Master Directions chosen by criteria, not convenience: (a) a published traceability appendix (the repealed/consolidated circular list); (b) moderate corpus size (roughly 10–80 source circulars each); (c) domain spread (at least: one KYC/AML-type, one prudential/exposure-type, one deposits/interest-rate-type, one governance/fit-and-proper-type); (d) circulars publicly retrievable from rbi.org.in or web.archive.org. Record the selection rationale; rejected candidates listed with reasons (sample-bias transparency).

**1.2 The pooled-blind protocol (the core design).** For each sampled MD, its traceability appendix defines *which circulars are in scope* — that is unavoidable and acceptable (corpus definition). What is **held out** is everything else: the MD's text, its structure, and the *grouping*. To make grouping a real test, **pool all sampled MDs' source circulars into one mixed corpus** (~150–350 documents). The engine's task on the pooled corpus: propose consolidation groupings and operations (`MERGE` targets, `REPEAL`s, `CANONICALIZE_DEFINITION`s, `RELATE_OBLIGATION`s, `RESOLVE_CROSS_REFERENCE`s, `ELEVATE_GENERAL_RULE`s) with span evidence, exactly as the Lex-Balanus pipeline does — under a prompt that **forbids any reference to Master Directions or the RBI consolidation program**.

**1.3 Leakage controls (honest, not perfect).** The model may carry parametric knowledge of the MDs. Mitigations, all mandatory: (a) prompts never name Master Directions, the RRA, or the consolidation program; (b) circular identifiers are **pseudonymized** in the LLM-facing corpus (stable random IDs; real citations restored only at scoring); (c) an automated leakage scan over all LLM outputs for MD names/numbers/RRA references — any hit is a checkpoint and that output is quarantined; (d) the report carries a standing **leakage caveat**: parametric familiarity cannot be eliminated, only made harder to use and detectable when overt — state this plainly, mirroring the corpus README's LLM-as-judge caveat.

**1.4 Scoring (structural only; dials held out).**
- **Grouping agreement:** proposed merge-clusters vs. the actual circular→MD assignment — pairwise precision/recall/F1 and Adjusted Rand Index over the pooled corpus.
- **Survival/repeal agreement:** proposed `REPEAL` vs. circulars the appendices list as repealed; precision/recall.
- **Operation-mix check:** share of proposed ops in {MERGE, REPEAL, CANONICALIZE_DEFINITION, RESOLVE_CROSS_REFERENCE} — the engine PRD §18 prediction, tested on the jurisdiction that inspired it.
- **Never scored:** RBI's substantive content choices, thresholds, or drafting (held-out dials).
- **Baseline (mandatory):** a plain-LLM run — same pooled pseudonymized corpus, same model, one prompt: "propose how to consolidate these instruments" — scored identically. The benchmark's claim is the *delta* the calculus scaffold adds, not the absolute number.
- Disagreements with the answer key are **characterized, never reconciled** — some may be places the engine's proposal is arguably cleaner than RBI's; record those symmetrically.

## 2. Build order (commit per task)

- **B6-T0 Housekeeping (small).** Apply the B5-residual outcomes to the repo: add the three approved composites to `composites.py`; relax `validate_composition()` to accept any validated composition of enum members (named composites as sugar); re-run the B5 lever pass — the six residuals should now validate against `specs/b5_residual_decompositions.json`; codify the held-out-dial rule in the profile docs; tests. *DoD:* zero residuals in the lever pass; suite green.
- **B6-T1 Sample + acquisition.** Select per §1.1 (checkpoint the selection for human sign-off before mass download); fetch each sampled MD's traceability appendix (answer key — stored under `data/benchmark/answer_key/`, **never readable by the proposal pipeline**; enforce with a path guard in code) and the source circulars (cache/manifest discipline; rbi.org.in + web.archive.org added to the allowlist **for this benchmark only**). OCR/parse failures documented; a circular that cannot be retrieved is dropped from scope *and from the answer key* symmetrically. *DoD:* pooled corpus + sealed answer key + selection memo.
- **B6-T2 RBI adapter-lite.** Circular parser (RBI citation format, dates, addressees, subject lines), pseudonymizer (stable map, stored outside the LLM-facing corpus), instrument strata for RBI (Act → directions/regulations → circulars/notifications). No full Lex profile — benchmark-grade only. *DoD:* pooled corpus normalized into DutySpec-like `InstrumentSummary` records; round-trip tests.
- **B6-T3 Engine run.** The calculus pipeline over the pooled corpus: diagnostics (restatement/mirror/undefined-term) → proposed groupings and operations with span evidence, LLM under harness rules (temp-0 semantics via cache, span-anchored, budget guard ~300 calls, hard-stop 500). Leakage scan on every output. *DoD:* proposal set with zero unanchored claims and zero unquarantined leakage hits.
- **B6-T4 Baseline run.** §1.4 plain-LLM baseline, same corpus, same budget class, same leakage scan. *DoD:* baseline proposal set.
- **B6-T5 Score.** Unseal the answer key (path guard lifted only here); compute all §1.4 metrics for engine and baseline; characterize every major disagreement (a table: cluster, engine said, RBI did, plausible reason). *DoD:* `outputs/b6/scores.json` + disagreement table.
- **B6-T6 Report.** `outputs/b6/B6_report.md`: design, sample memo, metrics with baseline delta, disagreement characterization, leakage caveat, limitations (sample size, English-only, parse losses), and a **publishable summary paragraph** suitable for the PRD §13 slot and a Substack write-up. Update README + PRD §13 status. *DoD:* suite green from cache; all committed.

## 3. Checkpoints (stop, `TODO(human)`, leave a draft)

1. **Sample selection (T1) — human sign-off required before download.**
2. Any leakage-scan hit; any evidence the proposal pipeline touched the answer key.
3. Retrieval/OCR failures affecting >15% of a sampled MD's corpus (drop the MD, don't limp).
4. Any scoring-metric judgment call not settled by §1.4 (e.g., partial-credit rules for split-across-two-MDs circulars) — propose, don't decide.
5. Anything suggesting the answer key itself is wrong or incomplete (RBI appendix errata) — record as a finding.

## 4. Definition of done

Sealed-key discipline held end to end; engine and baseline scored on identical corpora; metrics + characterized disagreements + leakage caveat in the report; publishable summary drafted; B6-T0 housekeeping green; all committed.

**This is the final planned arc. After B6, the project state is: full US-GSIB corpus product (B5) + validated cross-jurisdiction benchmark (B6) — write-up territory.**

---

**Begin at B6-T0. Stop for human sign-off at the T1 sample selection.**
