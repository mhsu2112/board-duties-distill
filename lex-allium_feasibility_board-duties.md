# Feasibility: Applying the Lex-Allium Transformation Calculus to GSIB Board-Duty Cleanup

**Assessment of porting the StatuteDistill/Lex-Allium primitives (statute-distill_lex-allium) to the bank-board cumulative-sludge corpus (bank boards_cumulative-sludge).**

*Draft — July 2, 2026*

---

## Verdict

**Feasible, and in several respects easier than the criminal-code reference implementation.** The PRD already anticipated this move (§18: banking consolidation is "the same calculus — predominantly MERGE + CANONICALIZE-DEFINITION + REPEAL + RESOLVE-CROSS-REFERENCE"), and the bank-board corpus turns out to be unusually well-prepared: the combined inventory is already a proto-canonical-schema, the Duplicate Clusters sheet is already a diagnostics pass, and the Reform Roadmap rows are already informal operation records. The work is less "build a new pipeline" than "type-check an existing analysis against the calculus and see what breaks."

Three genuine adaptations are required: (1) replace the case-law authority graph with a **supervisory-instrument hierarchy** (a *simpler* problem, with one hard residual — confidential supervisory information); (2) extend the primitive set with two or three banking-native moves (**ASSIGN-DUTY-STANDARD**, **DEEM-SATISFIED**, and typed **RELATE-OBLIGATION** edges); and (3) add a **multi-agency authority-to-act** field to every operation, since unlike the DC Council there is no single actor who can execute a MERGE.

---

## 1. Why the corpus fits

The unit of analysis translates cleanly. An `OffenseSpec` element is `{conduct, result, circumstance} × mens rea`; a board duty is `{actor, verb, object} × intensity × cadence`. The inventory's columns — Board level, duty nature, Source, Legal force, Cadence, Director-type distinction, Supervisory consequence — are the fields `NORMALIZE-ELEMENTS` would produce. Row RGC-02 ("Risk committee approves ERM framework, 12 CFR 252.33(a)(1), Regulation, Quarterly") is already a normalized element; it just isn't typed yet.

Scale favors the banking pilot. The MVP criminal scope was 10–20 offenses requiring a hand-built case-law graph. Here the whole corpus is ~230 duty-rows across ~30 clusters, citations already collected and confidence-rated, with the eval rounds having already stress-tested citation integrity.

And the constitutional posture is *more* permissive. The PRD's legible-vs-executable fork (§6.3) holds criminal law on the non-executable side because liability executes on people. Prudential and reporting rules are the PRD's own example of the *other* side of the fork — so the banking application has fewer hard limits, not more.

## 2. Primitive-by-primitive mapping

| Lex-Allium primitive | Banking analog | Evidence it fires in this corpus |
|---|---|---|
| `MERGE` (n→1) | Consolidate parallel approvals/instruments | "Single consolidated risk-appetite statement" (Roadmap #1); RBI Master Directions as the reference precedent |
| `SPLIT` (1→n) | Separate board decision from technical reporting | "Separate board capital-action decisions from technical methodology reporting" (Capital cluster) |
| `INTRODUCE` (0→1) | New consolidated instrument (Master-Direction-style) | Implied by every "joint statement + safe harbor" lever |
| `REPEAL` (1→0) | Rescind stale guidance | The Substack finding that rescissions happen "without any formal signal" — REPEAL exists but is currently *unlogged* |
| `RELOCATE` | Move duty between instruments / rulebook restructuring | "OCC App. D cross-references Reg YY" (Roadmap #2) |
| `RELATE-OFFENSE` | `RELATE-OBLIGATION` — typed edge between surviving duties | The "parallel-but-justified" clusters (FDICIA vs. SOX ICFR: "distinct interests") demand exactly this — see §3 |
| `CANONICALIZE-DEFINITION` (n→1) | One definition across agencies | "Single 'independent director' definition" (Roadmap #3) is a textbook instance |
| `DEFINE-TERM` (0→1) | Define undefined supervisory terms | "risk appetite," "credible challenge," "effective oversight" |
| `SUBSTITUTE-TERM` | Meaning-preserving modernization | Lower salience; fires in guidance-manual language |
| `NORMALIZE-ELEMENTS` | Type each duty as actor/verb/object/cadence | The inventory columns *are* this — retrofit is mechanical |
| `ASSIGN-MENS-REA` | `ASSIGN-DUTY-STANDARD` — see §3 | The board-vs-management allocation problem (SR 16-11 lineage) |
| `FACTOR-EXCEPTION` | IDI addenda, carve-outs, safe harbors | "One enterprise framework approval **with an IDI addendum**" |
| `REGRADE` | Re-tier supervisory consequence (CMP/C&D/rating) | Low salience; retain but downweight — still the highest-normative-load op |
| `ELEVATE-GENERAL-RULE` | Lift recurring duty into a "General Part" of board governance | ~21 clusters each restate "board approves a written framework annually" — the single biggest sludge pattern in the corpus is a missing General Part |
| `RESOLVE-CROSS-REFERENCE` | Guidance cross-references rule instead of restating | "Cross-reference manual to the rule; avoid restating" (BSA/AML cluster) — verbatim |

All fourteen fire or have a direct analog. The PRD's §18 prediction (MERGE/CANONICALIZE/REPEAL/RESOLVE-XREF dominant) is confirmed by the Duplicate Clusters sheet, with one addition it did not predict: `ELEVATE-GENERAL-RULE` may be the highest-value single move, because the dominant redundancy pattern is the *same meta-duty* ("approve framework, review annually, receive reports") restated per domain per agency.

## 3. Required extensions (the honest gaps)

**3.1 `ASSIGN-DUTY-STANDARD` (generalizing `ASSIGN-MENS-REA`).** The criminal system's hardest recovered content is implicit mens rea. The banking analog is the implicit *intensity* of a board duty: does "oversee" mean approve, review, be informed, or challenge? Many provisions say "the board" where supervisory practice accepts committee or delegated execution. An explicit enumerated standard (`approve | review_and_challenge | receive_report | be_informed`) assigned per duty, with an effect class (codify if exam practice already treats it that way; change if it reallocates board work to management), is the direct analog — and is precisely what the Fed's 2017–21 board-effectiveness project attempted manually.

**3.2 `DEEM-SATISFIED` — a candidate sixteenth primitive.** Roadmap #4 ("SOX 404(b) satisfies FDICIA ICFR by cross-reference") is decomposable as RESOLVE-CROSS-REFERENCE + FACTOR-EXCEPTION, but the decomposition loses the relational intent — the same argument that made `RELATE-OFFENSE` first-class in M0 (§7.5). Cross-satisfaction / safe-harbor / "compliance with X deemed compliance with Y" is a recurring, legally distinctive move in multi-agency regimes and deserves first-class status. Predict it surfaces as the residual in a banking M0.

**3.3 `RELATE-OBLIGATION` edge types.** The criminal relation types (`aggravated_form_of / shares_term / merges_with`) need a banking vocabulary: `implements` (reg→statute), `elaborates` (guidance→reg), `parallel_distinct_purpose` (FDICIA vs. SOX — the "legally distinct" column of the Duplicate Clusters sheet), `entity_level_mirror` (BHC vs. IDI duty), `deemed_satisfied_by`. Note the inventory already records these relationships in prose in the "What is legally distinct" column — they need typing, not discovery.

**3.4 Authority graph → instrument hierarchy + supervisory-practice layer.** The PRD calls the case-law authority graph "the core hard problem" (§8). The banking substitute is structurally *easier*: the hierarchy is statute > regulation > enforceable guideline (e.g., OCC Part 30 App. D) > guidance (non-binding per the 2021 interagency rule) > exam manual, with no holding/dicta problem and mostly formal effective dates. Negative treatment maps to rescission/supersession — which the Substack analysis shows is the corpus's *known* weakness ("retracted without any formal signal"; the Wayback-reconstruction work is, in calculus terms, rebuilding the negative-treatment index). Two residual hard spots:

- **Legal-force ambiguity**: guidance is nominally non-binding but supervisorily consequential. The schema needs `legal_force` as a first-class typed field (the inventory already has the column) and the effect classifier must treat "guidance expectation absorbed into a rule" as a `change`-class move (it converts non-binding to binding) — a hazard with no criminal analog.
- **Confidential supervisory information**: the true as-enforced layer (MRAs, exam findings, horizontal-review expectations) is unobservable from public sources. The criminal as-built spec could be fully recovered from published case law; the banking as-built spec cannot. Mitigation: mark the CSI-dependent portion `unresolved` rather than guess (the PRD's own rule), and note that *for an agency running this internally, the gap disappears* — which is an argument for the agency-side deployment posture.

**3.5 Multi-agency authority-to-act.** The DC pipeline has one legislature; here every operation needs `actor_with_authority` and `instrument_required` (rule vs. joint statement vs. statutory amendment) — fields the Reform Roadmap already carries (Actor / Authority / Instrument / Statutory obstacle). The `normative_kind` enum extends naturally: `constitutional_risk` → `statutory_constraint` (165(h) risk committee cannot be merged away by rule; SOX 301 and FDI Act §36 are floors), plus `interagency_coordination` as a new kind. An APA-process invariant replaces `constitutional_floor`: no `change`-class finding reaches final without a notice-and-comment (or equivalent) pathway recorded.

**3.6 Invariants translate almost mechanically.** `referential_integrity` → no duty cites rescinded guidance (a live failure mode found in the eval rounds — "stale-presented-as-current" is flag F3). `definitional_uniqueness` → one "independent director" test. `total_mens_rea` → **total assignment**: every duty has an explicit actor, verb-standard, and cadence. `penalty_monotonicity` → consequence proportionate to duty tier (weak, optional). New: `statutory_floor` (consolidation never deletes a statutorily mandated duty) and `binding_force_conservation` (consolidation never silently promotes guidance to rule or vice versa).

## 4. What the bank project already supplies to the pipeline

The two projects interlock better than a generic port would:

- **L0 sources**: the round-2 Codex bundle includes the source corpus itself.
- **L1 as-built**: the combined inventory is ~80% of a populated canonical schema; the two-layer design (binding obligation vs. supervisory expectation) is exactly the `legal_force` typing §3.4 needs.
- **L3 diagnostics**: Duplicate Clusters ≈ the diagnostics pass output; "Minimum reform lever" ≈ candidate operations awaiting typing.
- **L4 claim-level verification (§10)**: the horserace's integrity-weighted rubric and F1–F7 flags are an already-built, already-run verifier — `verifier_status`, hallucinated-citation gate, sample-based checking included. This is the piece the criminal project has only specced.
- **Gold labels / rediscovery benchmark**: the criminal project has the CCRC's ~70 labeled reports; banking's nearest equivalents are the **RBI Master Directions** (9,445→244 with traceability tables — an as-is consolidation whose mapping could serve as the held-out rediscovery target, and which the policy-sludge-cleanup skill has already reverse-engineered), the Fed's 2017–21 board-effectiveness review, and EGRPRA. Weaker than CCRC but sufficient for an M0-style closure test.

## 5. Recommended next step: a banking M0 (~1 week, mirrors PRD §17)

Take the top three duplicate clusters — risk-governance framework (21 duties), audit committee & independence (21), capital planning & stress testing (20) — and hand-express every "minimum reform lever" as a composition of the fifteen primitives plus the §3 candidates. Record for each: operands (inventory row IDs), effect class, normative kind (including `statutory_constraint` where 165(h)/SOX/FDI Act binds), and `actor_with_authority`.

**Exit criteria**, exactly as in the criminal M0: the set is closed over the sample, or the residual names the missing primitives. Prediction: closure requires `DEEM-SATISFIED` and typed `RELATE-OBLIGATION` edges; `ASSIGN-DUTY-STANDARD` fires on every cluster; `REGRADE` never fires. If that prediction holds, the calculus is validated as portable and the jurisdiction-adapter model (§15) gets its first non-criminal instantiation — with the adapter supplying: eCFR/statute parsers, the instrument hierarchy in place of the court hierarchy, rescission tracking in place of negative treatment, agency-authority metadata, and the statutory-floor invariant set.

## 6. Risk summary

| Risk | Severity | Mitigation |
|---|---|---|
| CSI makes as-enforced layer unrecoverable publicly | Medium | Mark `unresolved`; position tool for agency-internal use where the gap closes |
| Guidance/rule force ambiguity smuggles `change` inside "consolidation" | High | `binding_force_conservation` invariant + effect classifier per layer |
| No CCRC-grade gold record | Medium | RBI mapping + Fed 2017–21 review as partial references; report agreement, not accuracy |
| Multi-agency: no single actor can execute ops | Structural | `actor_with_authority` on every op; roadmap already models this |
| Over-claiming: inventory rows are LLM-synthesized, some flagged in evals | Medium | Run §10 verifier over the inventory before treating it as L1; confidence column already exists |
| Normative smuggling ("overlap = bad") | Same as criminal | Same fix: declared commitments + typed flags; the README already concedes "sludge is a normative lens" |
