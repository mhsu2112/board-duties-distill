# B3 Decision Packet — the first real review pass

> **✅ RESOLVED — July 2, 2026.** M. Hsu accepted all recommendations (via chat): all nine levers advance as evidence-backed roadmap candidates (D4, D5 ranked most feasible); AUD-07 resolved as board oversight of management's certification; the 10 re-pins, the mirror_pair/restatement diagnostic split, all 18 diagnostics, and the B4 engineering items are approved. Executed via `boarddistill/B4_TASKS.md`. Retained as the decision record.

**For:** Mike Hsu · **Date:** July 2, 2026 · **What this is:** every open item from the B3 run (27 findings + 4 cross-cutting issues), in plain English with a recommendation on each. Reply in chat — item numbers + your call ("accept all recommendations" also works, and every deviation is one line). Full evidence sits in `boarddistill/outputs/b3/<cluster>/package.md`; nothing here finalizes anything — your dispositions get written back with your name and rationale, and remain reversible.

---

## Part 1 — The nine consolidation findings (f-D1…f-D9)

These are your B0 reform levers, now run through the full pipeline with evidence attached. The disposition here is **not** "adopt this reform" — it is "advance this finding as a properly-framed candidate for the reform roadmap" (`reviewer_accepted` as draft direction) vs. modify vs. reject. Note: five show `effect_class: unresolved` — that's the classifier refusing to guess where the instrument graph lacks concept-level nodes (a B4 engineering fix, Part 6), not a substantive problem.

| # | Finding | Proposes | Effect | Key flags | Recommendation |
|---|---|---|---|---|---|
| 1.1 | f-D1 | One enterprise risk-framework approval + IDI addendum (expanded App. D reliance) | change | policy_choice, interagency | **Advance** — your inventory's own "minimum lever," now evidence-anchored |
| 1.2 | f-D2 | One consolidated risk-committee standard + streamlined IDI certification | change | statutory_constraint (165(h) floor holds), interagency | **Advance** |
| 1.3 | f-D3 | Single "independent director" definition; one committee satisfies all regimes | unresolved | interagency + SEC, statutory_constraint | **Advance, flagged hardest** — 4-regulator + SEC coordination; classifier must later prove the reconciled test is a superset |
| 1.4 | f-D4 | SOX 404(b) deemed to satisfy FDICIA ICFR; cycles aligned | unresolved | policy_choice | **Advance, rank first for feasibility** — single agency (FDIC), one rule amendment |
| 1.5 | f-D5 | Separate board capital decisions from methodology reporting | clarify | supervisory_value_judgment | **Advance, rank second** — FRB alone, mostly guidance action |
| 1.6 | f-D6 | Codify SR 12-17 into Reg YY; retire the letter | unresolved | policy_choice, interpretive_ambiguity | **Advance** — the declared guidance→rule conversion; the binding-line decision is the point |
| 1.7 | f-D7 | Single interagency board-effectiveness assessment | unresolved | (interagency) | **Advance, quick win** |
| 1.8 | f-D8 | Vertical HC/IDI rationalization via expanded reliance accommodation | unresolved | policy_choice | **Advance — largest lever**; floor preserved by design (reliance, not deletion) |
| 1.9 | f-D9 | Recurring meta-duty → one General-Part governance section | fill_gap | — | **Advance** — highest row-count impact |

**Your call on 1.1–1.9:** *(accept recommendations / list exceptions)*

## Part 2 — The one conflict: b:AUD-07 (SOX 302 certification)

The distiller read the source as `verb_standard: certify`; your B2 retag moved the actor to CEO/CFO. Both can't describe the board. **Recommendation:** the certification duty belongs to the CEO/CFO (retag stands); the board-side residual is *oversight of the certification process via the audit committee* — recorded as `review_and_challenge` in the oversight note, not `certify`. **Your call:** confirm / different treatment.

## Part 3 — The ten mispinned rows

The LLM refused to distill 10 rows whose B1/B2-pinned excerpt doesn't support the stated duty (e.g., b:AUD-08's CAE-appointment duty pinned to a concentration-risk paragraph): `b:AUD-08, b:CAP-02, b:RGC-05, s:BCG-03, s:CAP-07, s:CAP-09, s:GOV-03, s:GOV-04, s:GOV-08, s:GOV-12`. The duties themselves aren't in doubt — the *pins* are wrong. **Recommendation:** approve a B4 re-pin pass (re-run targeted retrieval for these 10, LLM re-distill after). **Your call:** approve / hold.

## Part 4 — Two kinds of duplication (B0 vs. LLM divergence)

B0's hand labels found **cross-layer mirror pairs** (BHC↔IDI, rule↔guideline — 11 pairs); the LLM found **within-cluster restatements** (same text repeated across rows — 35 pairs). Zero overlap: they are different, both real, and they take different reform levers (mirrors → DEEM_SATISFIED/reliance; restatements → MERGE/RESOLVE_CROSS_REFERENCE). **Recommendation:** adopt both as distinct diagnostic kinds (`mirror_pair`, `restatement`) so packages report them separately. **Your call:** approve / prefer one lens.

## Part 5 — The eighteen diagnostics (accept as investigation items?)

These are findings-to-investigate, not decisions. Recommendation: **accept all as diagnostics** (they seed future operations); notable content below.

**Duplicates/restatements (9):** RGC-07↔RGC-10 identical approval text; GOV-27 restating RGC-10 verbatim (rule-guidance restatement — RESOLVE_CROSS_REFERENCE candidate); four nominee-process duties from one passage; AUD-01/02/03 identical composition text; CAP-02/03 + s:CAP-02/09 same capital-policy excerpt; six s:CAP rows restating one escalation expectation; STR-01/03/04 same use-the-results expectation.

**Actor ambiguities (5):** RGC-07, RGC-10, GOV-27 (board vs. risk committee unsettled), s:CAP-01, s:STR-04 (board vs. management split unassigned) — the `ASSIGN_DUTY_PARAMETER` worklist, consistent with the headline stat that **41 of 50 duties state no board-action standard at all**.

**Undefined terms (5):** "independent risk management," "material activities," "prudent credit underwriting practices," "real-time targeted capital level"/"early warning metric," "Category I standards" — the `DEFINE_TERM` worklist.

**Your call:** accept all 18 / exceptions.

## Part 6 — Engineering approvals for B4 (mechanical; blanket yes suggested)

(a) Re-pin the 10 rows (Part 3) and re-distill. (b) **Concept-node graph extension** — add instrument-graph nodes for concept-level operands (`SOX-404b-attestation`, `AppD-committee-expectations`, …) so the classifier can reach the five `unresolved` levers. (c) Split the duplicate diagnostic into `mirror_pair`/`restatement` kinds (Part 4). (d) Apply the AUD-07 resolution (Part 2). (e) Write back all Part 1/5 dispositions under your name. **Your call:** approve all / exceptions.

---

**Bottom line if you accept everything:** all nine levers advance as evidence-backed roadmap candidates (D4 and D5 ranked most feasible), the pipeline's known defects get a targeted B4 fix pass, and the system's two headline empirical findings — pervasive unstated board-action standards, and two distinct duplication structures — become official, citable results of the project.
