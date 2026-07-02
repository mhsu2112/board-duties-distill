# B0 — Banking M0: Calculus Closure over the MVP Clusters

**Task:** hand-express every "minimum reform lever" bearing on the three MVP clusters (risk-governance framework/strategy · audit committee & independence · capital planning & stress testing, plus the entangled risk-committee-architecture and ICFR clusters they operate on) as compositions of the 14 StatuteDistill primitives with the two Lex-Balanus profile adaptations (`RELATE_OBLIGATION`, `ASSIGN_DUTY_STANDARD`). Residual = candidate missing primitives.

**Inputs:** `Synthesis/gsib-board_duties-combined_inventory.xlsx` — 62 duty rows in the MVP clusters ("All Board Duties"), 5 relevant "Duplicate Clusters" rows, 12 "Reform Roadmap" rows. Machine-readable extract: `b0_decompositions.json` (companion file; seeds B2 fixtures).

**Verdict (summary):** **The set closes at 15, not 14.** All profile primitives fire. One genuine residual: **`DEEM_SATISFIED` is confirmed** — it appears independently in five levers, including the corpus's largest structural reform, and cannot be expressed as a composite without losing exactly the relational content a reviewer needs. One marginal residual (cadence amendment) is proposed as a *generalization of `ASSIGN_DUTY_STANDARD`*, not a new primitive. Per checkpoint discipline (engine AGENTS §14.2): **proposed, not added** — see TODO(human) items at end.

---

## Notation

`OP(operands → output)`; operand IDs are inventory row IDs (Layer prefix `b:`/`s:` = binding/supervisory row where the same ID exists in both layers, e.g., `b:CAP-02` = 12 CFR 225.8(e)(1)(iii), `s:CAP-02` = SR 15-18 restatement). Effect classes per §7.4 of the PRD; every `change` and every cross-stratum operation defaults `needs_review`.

---

## D1 — "One enterprise framework approval with an IDI addendum"

*(Risk-governance cluster lever; Roadmap "Single consolidated risk-appetite statement." Note the lever's own text: it "expands the existing OCC Appendix D reliance accommodation, under which a covered bank may use the parent's framework in its entirety where … risk profiles are substantially the same.")*

| # | Operation | Operands | Effect | Flags |
|---|---|---|---|---|
| 1 | `RELATE_OBLIGATION(entity_level_mirror)` | RGC-02 (Reg YY 252.33(a)(1), BHC) ↔ RGC-07 (OCC App. D II.A, IDI) — **both survive** | clarify | — |
| 2 | **`DEEM_SATISFIED`** | RGC-07 *satisfied by* RGC-02 (parent enterprise framework), conditional | change (expands existing accommodation's scope) | `policy_choice`, `interagency_coordination` |
| 3 | `FACTOR_EXCEPTION` | conditions: risk profiles substantially the same; IDI addendum for bank-specific limits | — (rider on #2) | — |
| 4 | `RESOLVE_CROSS_REFERENCE` | s:GOV-15, s:GOV-20, s:FDR-01/02 (SR/manual restatements → cite the rule) | codify | — |

`actor_with_authority`: FRB+OCC · `instrument_required`: interagency rule/joint statement + safe harbor · `statutory_floor`: bank board's independent legal responsibility survives (the deem is conditional satisfaction, not deletion — which is exactly why `MERGE` is the *wrong* primitive here).

**Residual note.** Without `DEEM_SATISFIED` this forces into either `MERGE` (false: RGC-07 survives; the bank board remains legally responsible) or bare `FACTOR_EXCEPTION` (loses the cross-instrument satisfaction edge — the thing the reviewer must see). Same structure as the criminal M0's `RELATE_OFFENSE` argument.

## D2 — "One risk-committee standard at the consolidated level + streamlined IDI certification"

*(Risk-committee-architecture lever; Roadmap row 2.)*

| # | Operation | Operands | Effect | Flags |
|---|---|---|---|---|
| 1 | `RELATE_OBLIGATION(implements)` | RGC-02..05 (Reg YY) → RGC-01 (DFA 165(h) statute) | codify | — |
| 2 | `MERGE` | Reg YY committee standard + OCC App. D committee expectations → one consolidated standard | change | `statutory_constraint` (165(h) BHC committee is a floor — MERGE survivor must preserve it), `interagency_coordination` |
| 3 | **`DEEM_SATISFIED`** | bank-level committee expectations *satisfied by* consolidated committee + IDI certification | change | `policy_choice` |
| 4 | `FACTOR_EXCEPTION` | streamlined IDI certification; bank-specific risk limits retained (the "legally distinct" content) | — | — |
| 5 | `RESOLVE_CROSS_REFERENCE` | "OCC App. D cross-references Reg YY" (roadmap's own instrument text) | codify | — |

`actor`: FRB+OCC · `instrument`: joint rulemaking · invariants exercised: `statutory_floor` (165(h)), `binding_force_conservation` (guideline↔rule strata cross — flagged, declared).

## D3 — "Single 'independent director' definition; one audit committee satisfies all regimes"

*(Audit cluster lever; Roadmap row 3.)*

| # | Operation | Operands | Effect | Flags |
|---|---|---|---|---|
| 1 | `CANONICALIZE_DEFINITION` | "independent director" across Part 363 App. A (AUD-02), SOX 301, App. D, NYSE/Nasdaq → 1 | **change** where tests materially differ (the survivor formulation narrows/widens someone's test); clarify only if reconciliation is provably a superset | `interagency_coordination` (FRB+OCC+FDIC+SEC), `statutory_constraint` (SOX 301 test is statutory; Part 363 "outside director" is rule-level under FDI Act §36) |
| 2 | `RELATE_OBLIGATION(parallel_distinct_purpose)` | FDICIA audit-committee regime (AUD-01..03) ↔ SOX regime — **both survive**; deposit-insurance vs. investor-protection interests | clarify | — |
| 3 | **`DEEM_SATISFIED`** | one committee, properly composed, *satisfies* Part 363 + SOX 301 + exchange requirements | change | `policy_choice` |
| 4 | `RESOLVE_CROSS_REFERENCE` | s:BCG-14, s:GOV-12 restatements → cite the canonical definition | codify | — |

Note #1's effect-class subtlety: the roadmap claims "independence substance unchanged; one test" — that is a *claim to be verified by the classifier* (diff each regime's test against the survivor), not an assumption. This is the calculus catching optimistic reform language — working as intended.

## D4 — "SOX 404(b) satisfies FDICIA ICFR by cross-reference; align cycles"

*(ICFR cluster lever; Roadmap row 4. The pre-registered DEEM_SATISFIED test case.)*

| # | Operation | Operands | Effect | Flags |
|---|---|---|---|---|
| 1 | **`DEEM_SATISFIED`** | Part 363 ICFR assessment *satisfied by* SOX 404(b) attestation | change | `policy_choice` |
| 2 | `FACTOR_EXCEPTION` | FDICIA's distinct content (designated safety-and-soundness laws compliance) retained as annex | clarify | — |
| 3 | `RELATE_OBLIGATION(parallel_distinct_purpose)` | the surviving FDICIA annex ↔ SOX regime | clarify | — |
| 4 | *cadence alignment* (calendar → fiscal year) | b:AUD rows' annual cycle parameter | change | `institutional_discretion` |

`actor`: FDIC alone · `instrument`: Part 363 amendment · **Residual note (marginal):** #4 amends an explicit duty *parameter* (cadence). `SUBSTITUTE_TERM` is barred (meaning-preserving only); `NORMALIZE_ELEMENTS` types, it doesn't amend; `ASSIGN_DUTY_STANDARD` assigns where implicit. Proposal: **generalize `ASSIGN_DUTY_STANDARD` to `ASSIGN_DUTY_PARAMETER`** over the parameter set `{verb_standard, cadence}` — assignment where implicit (effect: codify/clarify) and re-assignment where explicit (effect: change). No new primitive needed. → TODO(human) 2.

## D5 — "Separate board capital-action decisions from technical methodology reporting"

*(Capital cluster lever — intra-level, single-agency; the cleanest `SPLIT`/`ASSIGN_DUTY_STANDARD` exercise.)*

| # | Operation | Operands | Effect | Flags |
|---|---|---|---|---|
| 1 | `SPLIT` | the board capital-planning duty bundle (b:CAP-02/03, s:CAP-01..09) → (a) capital-action decision duties, (b) methodology-information duties | clarify | — |
| 2 | `ASSIGN_DUTY_STANDARD(approve)` | capital plan, capital policy, capital actions (b:CAP-02, b:CAP-03, s:CAP-02, s:CAP-05) | codify (rule already says approve) | — |
| 3 | `ASSIGN_DUTY_STANDARD(receive_report)` | methodology robustness, scenario design, model limitations (s:CAP-03, s:CAP-06, parts of b:CAP-04) | **clarify** where SR 15-18's own board/management split already points there; **change** where it reallocates review work from board to management | `supervisory_value_judgment` |
| 4 | `RESOLVE_CROSS_REFERENCE` | SR 15-18 elaborations → cite 12 CFR 225.8 rather than restate | codify | — |
| 5 | `REPEAL` | s:CAP-11 (SR 09-4 remnant, already superseded for GSIBs by SR 15-18 fn.5) — formalize with a logged signal | codify | — |

`actor`: FRB alone · `instrument`: guidance action + conforming rule note · `statutory_floor`: b:CAP-01 (12 U.S.C. 5365(i) board oversight of stress testing) survives the SPLIT untouched. Non-op noted: s:CAP-10 (no board attestation on FR Y-14A) is a *negative finding* — record as diagnostic evidence, no operation.

## D6 — "Codify SR 12-17 governance content into Reg YY; retire the letter"

*(Roadmap row 7; operates on the risk-governance cluster's supervisory layer, GOV-02..13.)*

| # | Operation | Operands | Effect | Flags |
|---|---|---|---|---|
| 1 | `RELOCATE` | SR 12-17 attribute content (s:GOV-02..13) → Reg YY | **change (per-se: guidance → regulation is a binding-force conversion)** | `policy_choice`, `interpretive_ambiguity` |
| 2 | `ASSIGN_DUTY_STANDARD` | resolve the "ensure" vs. "oversee" tension per duty | clarify/change per duty | `interpretive_ambiguity` |
| 3 | `REPEAL` | SR 12-17 (with formal rescission signal) | — (rider on #1) | — |

Invariant exercise: `binding_force_conservation` fires on #1 by design — the reform's stated purpose ("clarifies mandatory vs. guidance") *is* a declared force conversion, so the invariant requires the declaration rather than blocking it. `apa_pathway`: notice-and-comment, recorded. This case is the proof that the per-se rule and the invariant produce the right behavior on a reform whose whole point is crossing the line.

## D7 — "Single interagency board-effectiveness assessment"

*(Roadmap row 10; App. D III.F ↔ SR 21-3.)*

`MERGE`(App. D III.F self-assessment + SR 21-3 assessment → one) + `RESOLVE_CROSS_REFERENCE`. Effect: codify (substance unchanged, one document — and unlike D3, the two source texts are near-identical, so codify is defensible). Flags: `interagency_coordination` only. Cross-stratum operands (enforceable guideline + guidance) ⇒ `needs_review` despite codify class — the default rule doing its job on the "easy" reform.

## D8 — "Vertical HC/IDI rationalization via expanded reliance accommodation"

*(Roadmap row 11 — "largest structural lever; removes the most pervasive overlap.")*

This is D1's pattern applied as a **schema**, per entity-level-mirror pair across the whole corpus:

```
for each (BHC_duty, IDI_duty) with relation entity_level_mirror:
    RELATE_OBLIGATION(entity_level_mirror)(BHC_duty, IDI_duty)
    DEEM_SATISFIED(IDI_duty ← BHC_duty | conditions)      # change-class, needs_review each
    FACTOR_EXCEPTION(documented-reliance conditions; bank-specific content retained)
```

`statutory_floor` (stated by the inventory itself): "bank-level independent legal responsibility is statutory; reliance can be expanded but not eliminated" — so `DEEM_SATISFIED` is the *only* primitive that can express this lever at all. `MERGE` is legally unavailable. **This is the decisive evidence for first-class adoption: the corpus's largest reform is inexpressible without the fifteenth primitive.**

## D9 — Recurring meta-duty → General Part *(hypothesis from the PRD, tested here)*

The pattern "board approves framework/policy X, reviews annually, receives reports on X" recurs across ≥6 of the 62 rows' families (RGC-07/10, CAP-02/05, STR-02, IAU-01, BCG-02/03/04, FDR-02).

`INTRODUCE(scope=general_part)`(general board-governance section: approval/review/reporting mechanics stated once) + `ELEVATE_GENERAL_RULE`(the recurring mechanics, from each domain instrument) + `RESOLVE_CROSS_REFERENCE`×n (domain rules state only the object and any stricter cadence). Effect: codify where mechanics are identical; clarify/change where cadence or verb differs across instruments (→ `ASSIGN_DUTY_PARAMETER` per D4's proposal). Confirms the PRD §7.3 hypothesis: `ELEVATE_GENERAL_RULE` is the highest-leverage single primitive in this corpus by row count touched.

## D10 — Non-operations (boundary discipline)

- **Roadmap row 12 ("tiered feasibility principle: harmonization is selection, not deletion")** is not an operation — it is a *sequencing policy over operations*, expressed in the schema as an ordering on `instrument_required`. Recorded the way "clarification is not a primitive" is recorded in the engine.
- **s:GOV-19** (rating-framework "ascetic principle" repeal — a consequence re-tiering that already happened) is historical evidence that `REGRADE` has a real referent in this domain (re-tiering supervisory consequence), even though no current lever proposes one.

---

## Closure table (which primitives fired)

| Primitive | Fired? | Where |
|---|---|---|
| MERGE | ✔ | D2, D7 |
| SPLIT | ✔ | D5 |
| INTRODUCE | ✔ | D9 (general_part) |
| REPEAL | ✔ | D5, D6 |
| RELOCATE | ✔ | D6 |
| RELATE_OBLIGATION | ✔ | D1, D2, D3, D4, D8 (all four relation types except `shares_term`; `shares_term` fires trivially on definition rows) |
| CANONICALIZE_DEFINITION | ✔ | D3 |
| DEFINE_TERM | ✔ (weak) | implied by D3 where a divergent test must be *newly* defined; also "risk appetite" (RGC cluster, not decomposed here) |
| SUBSTITUTE_TERM | ✘ | no lever in these clusters is a pure meaning-preserving rename — expected; fires in modernization-type cleanups |
| NORMALIZE_ELEMENTS | ✔ | precondition of every decomposition (the retyping itself) |
| ASSIGN_DUTY_STANDARD | ✔ | D5, D6 (and D4's proposed generalization) |
| FACTOR_EXCEPTION | ✔ | D1, D2, D3, D4, D8 |
| REGRADE | (observed, not proposed) | D10 / GOV-19 |
| ELEVATE_GENERAL_RULE | ✔ | D9 |
| RESOLVE_CROSS_REFERENCE | ✔ | D1–D7, D9 — the workhorse, as the engine PRD §18 predicted |
| **DEEM_SATISFIED (residual)** | **5 independent levers** | D1, D2, D3, D4, D8 (+ fiduciary: 12 CFR 9.9 already lets the audit committee serve as fiduciary audit committee — an *existing* deem-satisfied in current law, FID-02/BCG-06) |

## Residuals & proposals — TODO(human)

1. **TODO(human): adopt `DEEM_SATISFIED` as the 15th primitive** (profile-level; candidate for engine-level). Signature: `DEEM_SATISFIED{ satisfied_ref, satisfying_ref, conditions: list[str] }`; both operands **survive** (distinct from MERGE); decomposition into `RESOLVE_CROSS_REFERENCE + FACTOR_EXCEPTION` loses the satisfaction edge (same argument as RELATE_OFFENSE, engine PRD §7.5). Evidence: five independent levers incl. the corpus's largest; an instance already exists in current law (12 CFR 9.9). Effect class is *not* fixed: expanding an accommodation = change; restating an existing one = codify.
2. **TODO(human): generalize `ASSIGN_DUTY_STANDARD` → `ASSIGN_DUTY_PARAMETER`** over `{verb_standard, cadence}` (assignment where implicit; re-assignment where explicit = change-class). Alternative rejected: a separate SET_CADENCE primitive (too narrow; violates basis minimality).
3. **TODO(human): confirm operand row-ID mappings** in `b0_decompositions.json` against the inventory before B2 fixture authoring (per engine AGENTS §14.1 — these are hand-authored labels the eval will later grade against; they must be marked as such).
4. No other residual. With #1 and #2 approved, **the set is closed over the MVP clusters**: exit criterion met in the amended-set branch.

## What B0 changes downstream

- **PRD §7.3**: `DEEM_SATISFIED` moves from pre-registered hypothesis to approved primitive (pending TODO 1); its M0 prediction is confirmed.
- **B2 fixtures**: the natural deterministic fixture is **D4** (single-agency, two operands, exercises DEEM_SATISFIED + FACTOR_EXCEPTION + parallel_distinct_purpose + the cadence parameter) with **D7** as the codify-class contrast case and **D6** as the binding-force-invariant test.
- **Banking AGENTS.md**: `PrimitiveOp` enum = 15 members; `validate_composition()` must assert DEEM_SATISFIED-not-decomposable and both-operands-survive; new behavioral test: a force-stratum-crossing operation without a declared conversion fails `binding_force_conservation`.
