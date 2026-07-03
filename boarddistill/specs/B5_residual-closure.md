# B5 Residual Closure — hand decomposition of the six residual levers

**Task:** the B5 closure test flagged six reform levers as residuals. Decompose each by hand (B0 method) and determine whether the 16-primitive set genuinely fails to express them. **Authority:** M. Hsu, 2026-07-02 (REVIEW_PACKET_B5, all recommendations accepted; residuals assigned to hand decomposition).

**Verdict up front: closure holds — no new primitive is needed.** The B5 harness applied a stricter test than the closure claim requires: it demanded each lever be a *single primitive or one of four named composites*, whereas B0's claim (and the engine's) is that levers are **compositions** of primitives. Five of the six residuals decompose cleanly into multi-primitive compositions; the sixth (incentive compensation) is not an operation at all but a *policy disjunction whose branches each decompose* — the same non-operation category as the tiering principle in B0's D10. Two byproducts: three new named **composites** proposed for `composites.py` (compositions, not primitives — no enum change), and one held-out-dial rule made explicit.

Notation as in B0. All findings default `needs_review`; nothing here is a reform decision.

---

## R1 — CRO/CRE appointment & compensation
*"Consolidate into Reg YY; OCC incorporates by reference." (Reg YY 252.33(b) CRO appointment/comp, BHC · OCC App. D I.E.7 CRE, IDI)*

| # | Operation | Operands | Effect | Flags |
|---|---|---|---|---|
| 1 | `RELATE_OBLIGATION(entity_level_mirror)` | Reg YY CRO duty ↔ App. D CRE duty — both survive | clarify | — |
| 2 | `MERGE` | the duplicated board approval of the same individual's appointment/pay at two levels → one consolidated approval (Reg YY home) | change | `interagency_coordination` |
| 3 | `RESOLVE_CROSS_REFERENCE` | OCC App. D I.E.7 → Reg YY 252.33(b) (the "incorporates by reference") | codify | — |
| 4 | `FACTOR_EXCEPTION` | OCC-specific CRE-independence-from-front-line structure retained as distinct element | clarify | — |

`actor`: FRB+OCC · `instrument`: joint rulemaking. **Expressible** — the "retained distinct control" that stumped the harness is just `FACTOR_EXCEPTION` riding a `MERGE`, the same shape as B0's D2.

## R2 — Director training
*"One consolidated director-training program covering all topics." (OCC App. D III.E · SR 21-3/Director's Book · BSA program rule training pillar)*

| # | Operation | Operands | Effect | Flags |
|---|---|---|---|---|
| 1 | `MERGE` | general director-training expectations → one program | change | `supervisory_value_judgment`, `interagency_coordination` |
| 2 | `DEEM_SATISFIED` | BSA training pillar (31 U.S.C. 5318(h) program element — **statutory floor**) *satisfied by* the consolidated program's BSA module, conditional on module meeting program-rule content | change | `policy_choice`; floor-adjacent ⇒ always `needs_review` |
| 3 | `RESOLVE_CROSS_REFERENCE` | guidance restatements → the consolidated program | codify | — |

**Expressible.** The floor-safe way to "cover all topics" is not to merge the BSA duty away (blocked by `statutory_floor`) but to deem it satisfied by a conforming module — the invariant *dictated* the correct decomposition, which is the system working.

## R3 — Incentive compensation (DFA §956)
*"Finalize one 956 framework or rely on guidance; SEC independence satisfies the prudential element."*

**Classification: not an operation — a policy disjunction (non-op, B0 D10 category).** The branch choice is a six-agency political decision over an unimplemented statutory mandate; the calculus expresses each branch, never the choice:

- **Branch A (finalize):** `INTRODUCE`(§956 final rule) + `RESOLVE_CROSS_REFERENCE`/`REPEAL`(2010 guidance superseded) + `DEEM_SATISFIED`(prudential comp-committee-independence element ← SEC/exchange comp-committee independence). All `change`; `statutory_constraint` (§956 is itself a statutory mandate); six-agency joint rulemaking.
- **Branch B (rely on guidance):** `REPEAL`(withdraw pending proposals) + `RESOLVE_CROSS_REFERENCE`(2010 guidance as operative framework). Flag: leaves a statutory mandate unexecuted — `statutory_constraint` + `institutional_discretion`, hard `needs_review`.
- **Branch C (statutory repeal):** legislative act — outside the calculus entirely (like B0's D10 items).

**Expressible per branch; branch selection is routed to the human by the normative gate — exactly as designed.**

## R4 — Resolution, recovery & contingency funding
*"Single 'resilience planning' board cycle; shared resolution submission with an IDI annex." (DFA 165(d)/Reg QQ · FDI Act/12 CFR 360.10 · Reg YY 252.34(b) CFP · SR 14-8 recovery)*

| # | Operation | Operands | Effect | Flags |
|---|---|---|---|---|
| 1 | `INTRODUCE(general_part)` | one "resilience planning" board review-and-approval cycle (recovery + CFP + resolution content as modules) | fill_gap | — |
| 2 | `ASSIGN_DUTY_PARAMETER(cadence)` ×n | align each plan's explicit cycle to the single cycle | change (explicit re-assignment) | `institutional_discretion` |
| 3 | `MERGE` | parent 165(d) submission + IDI 360.10 submission → shared submission | change | `statutory_constraint` (165(d) is on the floor — submission duty survives; only the *format* merges), `interagency_coordination` |
| 4 | `FACTOR_EXCEPTION` | IDI annex carrying FDIC-specific resolvability content | clarify | — |
| 5 | `RELATE_OBLIGATION(parallel_distinct_purpose)` | FDIC's insured-bank resolvability interest ↔ FRB/parent regime — **both survive** | clarify | — |

**Expressible** — "cadence + partial merge + preserved-parallel" is a five-op composition, precisely what compositions are for.

## R5 — Risk appetite statement
*"Interagency risk-appetite template + safe harbor that one board-approved statement satisfies all."*

| # | Operation | Operands | Effect | Flags |
|---|---|---|---|---|
| 1 | `INTRODUCE(general_part)` | interagency risk-appetite template | fill_gap | `interagency_coordination` |
| 2 | `DEEM_SATISFIED` ×4 | each instrument's risk-appetite approval duty ← one board-approved template-conforming statement (the safe harbor = the conditions) | change | `policy_choice` |
| 3 | `FACTOR_EXCEPTION` | liquidity tolerance vs. operational-disruption tolerance retained as distinct modules | clarify | — |
| 4 | `RESOLVE_CROSS_REFERENCE` | the four instruments → the template | codify | — |

**Expressible — the textbook safe-harbor composition.** This is B0's D8 schema plus an `INTRODUCE`; it recurs often enough (R5 here, D8, D1) to deserve a named composite (below).

## R6 — Third-party risk management
*"Quantitative 'critical activity' threshold for board attention; management approval + aggregate reporting otherwise."*

| # | Operation | Operands | Effect | Flags |
|---|---|---|---|---|
| 1 | `DEFINE_TERM` | "critical activity" — quantitative definition (currently qualitative/undefined) | change (a quantitative test moves someone's boundary) | `policy_choice`, `interagency_coordination` |
| 2 | `SPLIT` | the board third-party duty → critical-activity board duty + non-critical management duty | change (reallocates board work) | `supervisory_value_judgment` |
| 3 | `ASSIGN_DUTY_PARAMETER(verb_standard)` | board: `approve` for critical, `receive_report` (aggregate) otherwise | change | — |
| 4 | `FACTOR_EXCEPTION` | CFPB consumer service-provider concern retained, not consolidated | clarify | — |

**Expressible — with one rule made explicit:** the calculus expresses the *move* (`DEFINE_TERM` with a quantitative test); the **threshold value itself is a held-out dial** the tool never sets — the profile analog of the engine's never-set-penalties rule (NG1). The roadmap's own obstacle ("defining 'critical' quantitatively") is the human's decision, surfaced as `policy_choice`.

---

## Closure verdict and proposals

**The 16-primitive set is closed over the full corpus.** 8 clean + 8 non-targets + 5 residuals-now-decomposed + 1 policy disjunction (branches decomposed) = all 22 levers accounted for; zero new primitives.

**TODO(human) — three proposed named composites** (additions to `composites.py`; compositions of existing primitives, no enum change — approve/reject):
1. `partial_consolidation = [MERGE, FACTOR_EXCEPTION, RELATE_OBLIGATION(parallel_distinct_purpose)]` — fires in R1, R4, and retroactively D2/D4.
2. `safe_harbor_template = [INTRODUCE(general_part), DEEM_SATISFIED, FACTOR_EXCEPTION, RESOLVE_CROSS_REFERENCE]` — fires in R5; generalizes D8/D1.
3. `tiered_attention = [DEFINE_TERM, SPLIT, ASSIGN_DUTY_PARAMETER]` — fires in R6; the generic "threshold governs board vs. management attention" move.

**TODO(human) — one rule to codify in the profile docs:** quantitative parameter *values* (thresholds, cadences chosen, penalty-like dials) are held out from the tool everywhere, uniformly — the R6 principle stated once.

**Engineering note for the repo (small, next Claude Code session):** relax `validate_composition()`'s lever test from "single primitive or named composite" to "any validated composition of enum members" (with named composites as sugar), then re-run the B5 lever pass — the six residuals should validate against the decompositions in `b5_residual_decompositions.json` (companion file).
