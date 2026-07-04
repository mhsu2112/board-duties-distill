# PRD — BoardDistill (StatuteDistill × Lex-Balanus)

**An evidence-backed regulatory-consolidation *workbench* for bank-board duties: make the case for (and against) consolidating each board obligation explicit, reviewable, and reproducible — with the Category I U.S. GSIB board-duty corpus as the reference implementation.**

| | |
|---|---|
| **Status** | Draft v0.1 |
| **Owner** | Mike Hsu |
| **Engine** | *StatuteDistill* (shared; see companion PRD `statutedistill-prd-v0.2.md`) |
| **This project** | The first non-criminal **jurisdiction/domain adapter** (StatuteDistill PRD §15) + a banking domain profile, *Lex-Balanus* (provisional name; *balanus* = barnacle, after the accretion metaphor) |
| **Reference corpus** | GSIB board duties inventory, this repository (June 2026) |
| **Parent projects** | `statute-distill_lex-allium/` (engine, calculus, build conventions) · `bank boards_cumulative-sludge/` (corpus, eval harness, synthesis) |
| **Posture** | Assistive workbench, not automated deregulation (see §3) |

---

## In plain English (for a policymaking audience)

**The problem.** Every statutory obligation and supervisory expectation placed on a large-bank board looks prudent on its own. But they accrete — across five agencies, four decades, and three legal strata (statute, regulation, guidance) — until a GSIB board carries ~200+ distinct duties, many restating the same underlying expectation ("approve a framework, review it annually, receive reports") in parallel instruments. This is *cumulative policy sludge*: burden that comes not from any one rule but from the pile.

**The idea.** A prior project (StatuteDistill) reverse-engineered how the D.C. Criminal Code Reform Commission rewrote a criminal code, and found that thousands of individual reform edits reduce to a small fixed repertoire of basic moves — merge two overlapping provisions, retire an obsolete one, give one term one definition, lift a recurring rule into a single general section — called the *Transformation Calculus*. This project applies that same calculus to bank-board duties. Instead of a 67-page narrative report, the output is a set of typed, citation-anchored *findings*: each proposed consolidation named as a specific move, tagged with whether it merely restates current requirements or actually changes them, tagged with which agency has the legal authority to make it, and checked against the statutes that no consolidation may touch.

**The guardrail that matters most.** The tool does not decide policy. It will never conclude that a safeguard should be weakened, resolve whether a duplicative-looking duty in fact serves a distinct statutory purpose, or convert a supervisory expectation into (or out of) a binding rule on its own. Wherever a judgment like that is required, it stops and routes the question to a human, with the evidence attached and the decision logged.

**Why it matters.** The Reserve Bank of India spent 40+ staff over a year compressing 9,445 circulars into 244 Master Directions. U.S. agencies have historically not attempted the equivalent because the analytical staff cost was prohibitive. This project's premise is that the inventory-and-analysis phase is now cheap, *if* the analysis is trustworthy — and trustworthiness is exactly what a typed calculus with citation-level verification provides that a fluent AI-written report does not.

---

## 1. TL;DR (technical)

The GSIB board-duty corpus is a legacy codebase with five maintainers and no merge policy: statutes, regulations, enforceable guidelines, non-binding-but-supervisorily-enforced guidance, and exam manuals, layered since the 1980s, with rescissions often unlogged. A prior horserace project produced a ~230-row, two-layer (binding obligation vs. supervisory expectation), citation-checked inventory of these duties, plus an integrity-weighted LLM-judge evaluation harness.

BoardDistill retypes that corpus into StatuteDistill's canonical schema and runs the Transformation Calculus over it: diagnostics → operations → invariants → effect classification, with every finding citation-anchored, effect-classified against an as-built baseline, normative-flagged, and gated through human disposition. The case-law authority graph is replaced by a **supervisory-instrument hierarchy graph** (a structurally simpler baseline source, with one honest gap: confidential supervisory information). Two profile-level primitive adaptations are made and one new primitive is pre-registered as an M0 hypothesis. Validation targets: (a) closure of the primitive set over the corpus's top duplicate clusters, and (b) a rediscovery benchmark against the RBI Master Directions consolidation mapping.

This is a **legibility and review system, not automated deregulation.** Feasibility analysis: `lex-allium_feasibility_board-duties.md` (this folder).

---

## 2. Honest framing of normativity

Inherited from the engine PRD §2 and restated for this domain: **"sludge" is a normative lens, not a legal conclusion** (this repo's README says exactly this). Treating overlap as redundancy assumes consolidation is good; counting board duties assumes the count is a burden proxy; calling a rule-plus-guidance pair "duplicative" takes a side in a live legal debate about what guidance is. The posture is **declared, contestable commitments** surfaced through typed normative flags (§9) — never neutrality claims. Two commitments specific to this domain are declared up front:

1. **Parallel-but-justified is a real category.** Some overlapping duties serve genuinely distinct statutory interests (e.g., FDICIA ICFR protects the deposit-insurance fund; SOX 404 protects investors). The calculus must be able to *relate and preserve* duties, not only merge them — this is why `RELATE_OBLIGATION` is first-class.
2. **Binding force is load-bearing.** A consolidation that silently converts guidance into rule (or rule into guidance) is a substantive legal change, whatever it is labeled. The system treats binding-force changes as `change`-class per se (§7.4 invariant).

---

## 3. Product posture: workbench vs. pipeline

- **Product promise:** "Make the case for and against each consolidation of board duties explicit, reviewable, and reproducible — down to the citation and the agency with authority to act."
- **Not:** "Decide what to deregulate," and not "automate the RBI exercise."
- The system *frames, classifies, drafts, and evidences*; humans *decide*. Every value-laden decision is gated (§9).
- **Rediscovery** — can the engine independently recover the RBI's consolidation mapping, or the Fed's 2017–21 board-effectiveness reallocations? — is a **held-out research benchmark** (§13), separate from the product promise.
- **Deployment posture:** designed to run agency-internal. Public-source runs are honest about the confidential-supervisory-information gap (§8.3); agency-internal runs close it.

---

## 4. Goals / Non-goals

### Goals
- **G1.** Define the **Lex-Balanus profile** of the Transformation Calculus (§7): the primitive set, banking relation types, duty-standard enum, and profile invariants.
- **G2.** Distill an "as-built" duty spec from the two-layer inventory + the instrument hierarchy graph (§8), at pinned snapshot dates.
- **G3.** Classify each candidate consolidation (codify / clarify / fill_gap / change) by diffing against the as-built baseline, with claim-level verification (§10) reusing the existing eval harness.
- **G4.** Generate review artifacts: consolidation redline, duty crosswalk (old citations → consolidated instrument), burden delta, authority-to-act table, and a normative review queue.
- **G5.** Validate: M0 closure over the top duplicate clusters; rediscovery vs. RBI mapping; citation-integrity gate.
- **G6.** Keep the engine shared: everything here is an **adapter + profile** over the StatuteDistill canonical schema, so improvements flow both ways.

### Non-goals
- **NG1.** Deciding whether any safeguard should be weakened, or recommending net deregulation.
- **NG2.** Producing operative regulatory text (proposed rule language is illustrative draft only).
- **NG3.** Machine-executable compliance logic. (Prudential/reporting rules sit on the *permitted* side of the engine PRD's §6.3 fork, so executability is not forbidden in principle — it is simply out of scope for this product.)
- **NG4.** Non-U.S. corpora in v1 (PRA/FCA is an M6 adapter target, not MVP).
- **NG5.** Duties of management, or of boards outside Category I GSIBs, in v1.

---

## 5. Background (self-contained; a cold-start reader needs nothing else)

**5.1 The sludge taxonomy.** Hsu et al. (ADB, *Cleaning Up Policy Sludge*) distinguish horizontal sludge (rules overlap/conflict), vertical sludge (implementation balloons obligations), and cumulative sludge (accretion over time). This project targets cumulative sludge in one corpus: GSIB board duties. Write-up: `https://mhsu2112.substack.com/p/cumulative-policy-sludge`.

**5.2 The corpus (this repository).** A "horserace" gave the same research brief — compile a citation-level inventory of all in-force board obligations for Category I GSIBs across FRB/OCC/FDIC/CFPB/interagency sources — to multiple frontier AI systems; three LLM judges graded each report against an integrity-weighted rubric (`Tools/policy-sludge-rubric-v2.md`) with evidence-required flags for fabrication, misattribution, staleness, invented obligations, false exhaustiveness, scope evasion, and unsupported conclusions. The graded outputs were synthesized into:
- `Synthesis/gsib-board_duties-combined_inventory.xlsx` — the **primary input**: ~230 duty rows in two layers (binding obligation / supervisory expectation), with columns for ID, domain, cluster, duty nature, source, citation, agency, entity (BHC/IDI), board level, director-type distinction, legal force, supervisory consequence, cadence, redundancy type, currency status, confidence, last-checked date, and overlap notes; plus sheets for duplicate clusters (with "minimum reform lever" per cluster), a burden model, and a reform roadmap (with actor / authority / instrument / difficulty / statutory obstacle per reform).
- `Synthesis/gsib-board_duties-combined_report.docx` — the 67-page narrative companion.
- `Reports/round-2-followups/codex_supervisory-expectations-inventory/sources/` — primary-source documents.

**5.3 The engine.** StatuteDistill (see `statute-distill_lex-allium/statutedistill-prd-v0.2.md` and `AGENTS.md`) provides: a versioned canonical schema (Pydantic v2, JSON source of truth); the 14-primitive Transformation Calculus with effect classes and composition validation; snapshot-date enforcement; claim-level verification records; the typed normative flag and disposition state machine; invariant gates on `final` status; and a deterministic fixtures-first build discipline. Its criminal-law profile is Lex-Allium; its PRD §18 predicted the banking application.

**5.4 The precedent.** RBI compressed 9,445 circulars into 244 Master Directions (2021–2025) via as-is consolidation with full traceability. Reverse-engineered as the `policy-sludge-cleanup` skill (`https://github.com/mhsu2112/policy-sludge-cleanup`). RBI's published old→new mapping is this project's nearest analog to the CCRC's labeled record, and the rediscovery benchmark target (§13). Nearer-domain partial references: the Fed's 2017–21 board-effectiveness review (SR 16-11 lineage) and EGRPRA reviews.

**5.5 Key legal context a cold-start reader must know.**
- **Instrument strata.** Statute (e.g., Dodd-Frank §165(h), 12 U.S.C. 5365(h)) > regulation (e.g., Reg YY, 12 CFR 252) > enforceable guidelines (e.g., OCC heightened standards, 12 CFR 30 App. D — guideline in form, enforceable under FDI Act §39) > supervisory guidance (SR letters etc. — non-binding per the 2021 interagency guidance rule, yet supervisorily consequential) > examination manuals.
- **Two entity levels.** Duties attach at the holding company (BHC) and at the insured depository subsidiary (IDI), often in mirrored pairs from different agencies.
- **Rescission opacity.** Guidance is frequently retired without formal signal; the corpus's currency data partly rests on archival reconstruction. This is itself a finding (the "navigability and verifiability" problem) and a design driver for §8.

---

## 6. Conceptual model

### 6.1 Canonical schema is the source of truth (inherited)
As in the engine PRD §6.1: a versioned, typed canonical JSON schema is the source of truth; any rendered views (Allium or otherwise) are derived and round-tripped. This project **extends** the schema with a `DutySpec` (§7.1) alongside `OffenseSpec`; shared types (`SnapshotDates`, `SourceSpan`, `LegalClaim`, `Operation`, `Finding`, verification and review models) are reused unchanged wherever possible, extended by profile where not (§7).

### 6.2 The mechanical / normative boundary (inherited, hard requirement)
Operations and classifications *surface and propose*; they never *decide* whether an overlap is redundant or justified — that is a supervisory-policy judgment. Every finding carries typed normative flags (§9); flagged findings route to human disposition; no finding reaches `final` with an open flag.

### 6.3 The binding-force fork (this domain's version of §6.3)
The criminal profile's hard fork was legible-vs-executable. This profile's hard fork is **binding vs. non-binding**: the corpus is stratified by legal force, and the single most dangerous failure mode is a "consolidation" that silently moves content across that line. Binding force is therefore a first-class typed field on every duty and every operation output, conserved by invariant (§7.4) unless a finding explicitly declares the conversion as `change`-class with a `statutory_constraint`/`policy_choice` flag.

---

## 7. The Lex-Balanus Transformation Calculus (spine)

Four layers, kept distinct, exactly as in the engine (diagnostics → operations → invariants → effect classes).

### 7.1 Unit of analysis: `DutySpec`
The profile analog of `OffenseSpec`. One record per duty (matching the inventory's row grain), per layer (`as_built` / `intended`):

- `duty_id`, `label`, `layer`, `snapshot_dates` (§8.4)
- **Actor:** `board_level ∈ {full_board, audit_committee, risk_committee, compensation_committee, governance_committee, other_committee}` · `director_class ∈ {any, independent, outside, non_management, none_specified}` · `entity ∈ {BHC, IDI, both}`
- **Duty elements** (the `NORMALIZE_ELEMENTS` output): `verb_standard` (§7.3a), `object` (what is approved/reviewed/received), `cadence ∈ {annual, semiannual, quarterly, event_driven, ongoing, none_specified}`, `trigger` (if event-driven)
- **Force & consequence:** `legal_force ∈ {statute, regulation, enforceable_guideline, guidance, manual}` · `consequence ∈ {enforcement, rating, examination, reputational, none_specified}`
- **Provenance:** `instrument_id` (→ §8 graph), `source_citations`, `claims: list[LegalClaim]`, `confidence`, `currency_status ∈ {active, rescinded, superseded, stale_unverified}`

The existing inventory columns map onto this near-1:1; retyping is mechanical (M1).

### 7.2 Diagnostics (detect → trigger)
Profile diagnostic set: duplicate duty (same actor+verb+object across instruments), rule-guidance restatement, undefined supervisory term, conflicting definitions across agencies (e.g., director independence), dead reference (cites rescinded guidance), stale currency, entity-level mirror (BHC/IDI pair), recurring meta-duty (the "approve framework / review annually / receive reports" pattern), cadence conflict, actor ambiguity ("the board" where committee/delegation is accepted), binding-force ambiguity, orphan expectation (guidance with no rule or statute above it).

### 7.3 Operations (the primitives)

**The starting basis is the engine's closed 15-primitive set**, with two profile-level adaptations (renamings-with-extension, not new semantics) and one pre-registered candidate addition:

| Family | Primitive | Banking reading |
|---|---|---|
| Structure | `MERGE` (n→1) | Consolidate parallel duties/instruments into one (e.g., single risk-appetite approval satisfying Reg YY + OCC App. D) |
| | `SPLIT` (1→n) | Separate distinct duties bundled in one provision (e.g., board capital-action decision vs. technical methodology reporting) |
| | `INTRODUCE` (0→1) | Create a consolidated instrument (Master-Direction-style) or a new express duty |
| | `REPEAL` (1→0) | Formally rescind — with a logged signal (fixing the silent-retraction pattern is part of the point) |
| | `RELOCATE` | Move a duty between instruments/agencies' rulebooks |
| | `RELATE_OBLIGATION` *(profile adaptation of `RELATE_OFFENSE`)* | Typed edge between two **surviving** duties: `relation ∈ {implements, elaborates, parallel_distinct_purpose, entity_level_mirror, shares_term}` |
| Terminology | `CANONICALIZE_DEFINITION` (n→1) | One definition across agencies (e.g., "independent director") |
| | `DEFINE_TERM` (0→1) | Define an undefined supervisory term ("risk appetite," "credible challenge") |
| | `SUBSTITUTE_TERM` (1→1) | Strictly meaning-preserving modernization only |
| Duty content | `NORMALIZE_ELEMENTS` | Type a duty as actor / verb / object / cadence / force (§7.1) |
| | `ASSIGN_DUTY_STANDARD` *(profile adaptation of `ASSIGN_MENS_REA`)* | Make the implicit intensity of a duty explicit: `standard ∈ {approve, review_and_challenge, receive_report, be_informed, certify}` — the banking analog of implicit mens rea, and the core of the board-vs-management allocation question |
| | `FACTOR_EXCEPTION` | Carve-outs, IDI addenda, tailoring thresholds, safe-harbor conditions |
| Consequence | `REGRADE` | Re-tier the supervisory consequence attached to a duty — retained, highest normative load, expected to fire rarely |
| General Part | `ELEVATE_GENERAL_RULE` | Lift the recurring meta-duty ("approve framework, review annually, receive reports") into a single general governance section — hypothesized to be the highest-value move in this corpus |
| | `RESOLVE_CROSS_REFERENCE` | Guidance/manual cross-references the rule instead of restating it |

**Pre-registered candidate 16th primitive — `DEEM_SATISFIED`** *(hypothesis, not yet in the enum)*: "compliance with X is deemed compliance with Y" (e.g., SOX 404(b) attestation satisfying FDICIA ICFR by cross-reference). Decomposable as `RESOLVE_CROSS_REFERENCE + FACTOR_EXCEPTION`, but the decomposition loses the cross-regime relational intent — the same argument that made `RELATE_OFFENSE` first-class in the criminal M0. **Discipline (engine AGENTS §14):** it is added to the enum only if the banking M0 (§17, phase B0) produces it as a residual; the M0 prediction is that it will.

Operation records carry the engine's full envelope — `operands[]`, `arity`, `inverse?`, `scope ∈ {duty_level, general_part}`, `diagnostics_triggering[]`, `normative_load` — **plus two profile fields**: `actor_with_authority` (which agency/agencies can execute the operation) and `instrument_required ∈ {rule (APA), joint_rulemaking, interagency_statement, guidance_action, statutory_amendment}`. An operation whose `instrument_required = statutory_amendment` is automatically `normative_load = high`.

**Composites decompose** (basis-minimality check, engine §7.2): Consolidation = `MERGE + CANONICALIZE_DEFINITION + RESOLVE_CROSS_REFERENCE`; Master-Direction build = `INTRODUCE(general_part) + MERGE×n + REPEAL×n + RESOLVE_CROSS_REFERENCE×n`; Board-role clarification = `ASSIGN_DUTY_STANDARD + SPLIT`. "Streamlining" is not an operation; "burden reduction" is not an effect class.

### 7.4 Effect classification (label, contextual)
`codify | clarify | fill_gap | change | unresolved` — identical semantics to the engine, computed **only** by diffing against the as-built baseline from the §8 graph; no baseline ⇒ `unresolved`, never a guess. Domain calibration examples:
- `MERGE` of a rule-approval and its guidance restatement → `codify` **iff** the surviving text imposes nothing the rule didn't; otherwise `change`.
- `ASSIGN_DUTY_STANDARD(receive_report)` where the provision said "board oversight" → `codify` if supervisory practice already accepted reporting-level engagement, `clarify` if ambiguous, `change` if it reallocates work between board and management.
- **Per-se rule:** any output whose `legal_force` differs from all of its operands' is `change`-class, mechanically (the §6.3 fork).
- Reference labels: the inventory's "Redundancy type" / "What is legally distinct" / "Minimum reform lever" columns and the Reform Roadmap rows are the hand-authored near-labels — **treated as contestable, not ground truth**; disagreement is a first-class output.

### 7.5 Invariants (validate; block `final` absent a recorded reviewer exception)
- `total_assignment` — every duty in an `intended` spec has explicit actor, `verb_standard`, cadence, and `legal_force` (profile analog of `total_mens_rea`).
- `referential_integrity` — no duty cites a `rescinded`/`superseded` instrument (dead references to retracted guidance are a live failure mode in this corpus).
- `definitional_uniqueness` — one canonical definition per term per consolidated instrument set.
- `statutory_floor` — no composition of operations deletes or dilutes a duty mandated by statute (§165(h) risk committee; SOX 301; FDI Act §36/Part 363; BSA program statutes). Checked against a maintained statutory-floor list; violations are hard blocks.
- `binding_force_conservation` — `legal_force` is conserved through every operation unless the finding explicitly declares the conversion (`change`-class + flags). The per-se rule of §7.4, as a gate.
- `apa_pathway` — every `change`-class finding records a lawful pathway in `instrument_required` (notice-and-comment or equivalent); "just update the manual" is not a lawful pathway for a binding change.
- `consequence_proportionality` *(soft, warn-only in v1)* — profile analog of penalty monotonicity.

**Pipeline reads as compiler passes** (unchanged): diagnostic pass → operation pass → invariant pass → classification pass.

---

## 8. Instrument hierarchy graph (replaces the case-law authority graph)

The engine's hardest problem was recovering the judicially-supplied layer. The banking baseline source is **structurally simpler** — no holding/dicta problem, mostly formal effective dates — but has its own required properties per instrument:

- **8.1 Hierarchy & force:** `stratum ∈ {statute, regulation, enforceable_guideline, guidance, manual}` and issuing agency; controlling-vs-persuasive maps to binding-vs-non-binding, with `enforceable_guideline` as the explicitly modeled middle case.
- **8.2 Treatment & currency:** `treatment_status ∈ {active, amended, superseded, rescinded_formal, rescinded_informal, stale_unverified}` with dates. `rescinded_informal` (retired without signal, recovered archivally) is first-class — it is this corpus's version of negative treatment, and building this index *is* part of the product's value.
- **8.3 The as-enforced layer (declared gap).** True supervisory expectations also live in MRAs, exam findings, and horizontal reviews — confidential supervisory information, unobservable from public sources. **Rule: mark `unresolved` over guess.** Public-source runs carry a standing banner that the as-built spec is the *as-published* spec; agency-internal deployment closes the gap (§3).
- **8.4 Snapshot freeze (mandatory, inherited).** Three pinned dates per run: `inventory_as_of` (the vintage of the duty inventory — June 2026 for the reference corpus), `consolidation_as_of` (the proposed consolidated instrument's reference date), `current_as_of` (live-law check). The as-built spec is distilled at `inventory_as_of`; effect classification runs against that vintage, or the eval measures regulatory drift instead of method fidelity. Additionally every instrument node carries its own effective/rescission dates so `baseline_for(target, as_of)` is answerable for any target duty.

`GraphStore.baseline_for(duty_ref, as_of)` returns the highest-stratum, active-treatment, as-of-valid instrument text bearing on the duty — the exact interface the engine already defines.

---

## 9. Normative flag (typed kind + disposition state)

Two axes, inherited mechanics, profile-extended kinds:

- **Kind:** `policy_choice` · `supervisory_value_judgment` (analog of penalty judgment: how much board attention a risk deserves) · `statutory_constraint` (analog of constitutional risk: a floor Congress set) · `interpretive_ambiguity` (analog of doctrinal ambiguity) · `institutional_discretion` · **`interagency_coordination`** (new: the operation is lawful but requires actors to agree — e.g., a joint independence definition needs FRB+OCC+FDIC+SEC).
- **Disposition state:** `auto_ok → needs_review → reviewer_accepted | reviewer_rejected | reviewer_modified`, with reviewer id, timestamp, rationale — unchanged.

Defaults to `needs_review`: any `REGRADE`; any `change`-class finding; any binding-force conversion; any finding touching the statutory-floor list; any `parallel_distinct_purpose` relation proposed for merging anyway. No finding reaches `final` with an open kind and unresolved disposition.

---

## 10. Claim-level verification (reuse what this repo already built)

Every legal claim emits the engine's verifier record (`claim`, `source_span`, `support_type`, `authority_type`, `as_of_valid`, `confidence`, `verifier_status`). **This project's differentiator: the verification harness already exists and has been run.** The horserace eval stack — integrity-weighted rubric (`Tools/policy-sludge-rubric-v2.md`), judge prompt (`Tools/policy-sludge-llm-judge-prompt-v2.md`), reviewer protocol, F1–F7 evidence-required flags, sampled citation checking, and the multi-judge design — is adopted as the claim-verification layer, with flags mapped to `verifier_status` (`F1 fabricated`/`F2 misattributed` → `contradicted`; `F3 stale-as-current` → `as_of_valid = false`; `F7 unsupported conclusion` → `unverified`). Two obligations follow:

1. **Verify the inventory before trusting it as L1.** The ~230 rows are LLM-synthesized and confidence-rated but not row-by-row verified; a full-coverage (not sampled) verification pass over the MVP clusters is an M1 exit criterion.
2. Hallucinated-citation rate remains a release gate, unchanged.

---

## 11. Architecture (layers; deltas from the engine in bold)

```
L0  Sources + Adapters       eCFR/US Code parsers · agency guidance registries ·
                             **archival rescission reconstruction (Wayback)** ·
                             **existing inventory xlsx adapter** · citation formats ·
                             **statutory-floor list** (+ snapshot dates §8.4)
L1  Distill → as-built spec  DutySpecs populated via instrument hierarchy graph;
                             **bootstrap: retype the combined inventory** (M1)
L2  Intent → intended spec   the proposed consolidated instrument set
                             (Master-Direction-style), or imported reform proposal
L3  Calculus                 Diagnostics → Operations (**+ actor_with_authority,
                             instrument_required**) → Invariants (**+ statutory_floor,
                             binding_force_conservation, apa_pathway**) → Effect classes
L4  Render + Verify          consolidation redline · duty crosswalk · burden delta ·
                             **authority-to-act table** · claim-level verification
                             (**adopting the Tools/ eval harness**)
L5  Review Workbench         typed normative flags · disposition state machine · audit log
OUT per-cluster consolidation package — audit-grade, citation-anchored, reviewable
```

Build conventions inherited wholesale from the engine's `AGENTS.md`: Pydantic v2 canonical models with `extra="forbid"`, deterministic fixtures-first slice one (no LLM/network), closed primitive enum, effect-class-needs-baseline, normative and verification gates on `final`, checkpoint discipline (never add a primitive or resolve a review item autonomously).

---

## 12. MVP scope (credible)

Not the full 230-row corpus. MVP covers the **top three duplicate clusters** (~60 duty rows):
1. **Risk-governance framework / strategy** (21 duties; DFA 165(h), Reg YY 252.33, OCC App. D, SR 12-17/21-3/95-51) — exercises `MERGE`, `RELATE_OBLIGATION(entity_level_mirror)`, `ELEVATE_GENERAL_RULE`, the statutory floor.
2. **Audit committee & independence** (21 duties; SOX 301, FDICIA/Part 363, OCC App. D, exchange rules, SR 13-1) — exercises `CANONICALIZE_DEFINITION`, `RELATE_OBLIGATION(parallel_distinct_purpose)`, the `DEEM_SATISFIED` hypothesis, `interagency_coordination`.
3. **Capital planning & stress testing** (20 duties; DFA 165(i), 12 CFR 225.8, Reg YY 252.44/.54, SR 15-18) — exercises `SPLIT`, `ASSIGN_DUTY_STANDARD`, intra-level rule-vs-guidance classification.

Plus: the instrument hierarchy graph for those clusters only; hand-built gold findings for a held-out slice; full-coverage claim verification of the ~60 rows.

---

## 13. Evaluation

**Product (workbench) metrics:** expert-adjudicated precision/recall on duty extraction (actor/verb/object/cadence/force), duplicate-cluster detection vs. the hand-built Duplicate Clusters sheet, effect-class agreement vs. hand labels (reported as agreement; disagreements characterized), citation-integrity rate via the §10 harness, Pass^K stability.

**Baselines (mandatory, engine §13):** plain LLM with the original three-sentence prompt; plain LLM with the Caffrey-expanded prompt (both already exist in `Reports/`!); RAG-only over the source corpus; the existing synthesis itself as a strong human-plus-AI baseline. The horserace already demonstrated prompt-harness effects of ~2×; the claim to beat is that *typed calculus + verification* adds trustworthiness beyond what prompt engineering achieved.

**Research benchmark (held out):** **RBI rediscovery** — given a sample of pre-consolidation RBI circulars, how much of the published Master-Direction mapping (which circulars merged where, what was repealed, what was preserved-and-related) does the engine recover, scored on operation-set agreement, with RBI's substantive policy choices held out. Secondary: Fed 2017–21 board-effectiveness reallocations as an `ASSIGN_DUTY_STANDARD` reference set.

> **Result (B6, executed 2026-07; `boarddistill/B6_TASKS.md`, report `outputs/b6/B6_report.md`).** Pooled-blind over 163 pseudonymized circulars from 4 Master Directions. Engine grouping: pairwise F1 0.52 (precision 0.92, recall 0.36), ARI 0.43 — **~0 delta vs. a plain-LLM baseline**. The calculus scaffold's distinctive output was 131 span-anchored consolidation *operations*, 75% in the {MERGE, REPEAL, CANONICALIZE_DEFINITION, RESOLVE_CROSS_REFERENCE} set this PRD predicted (§18). Disagreements were clean bank-type/sub-topic splits that RBI's own 2025 consolidation independently adopted. Conclusion: the calculus generalizes cross-jurisdiction as a *structuring/auditing* discipline, not as a better clusterer than an LLM. Standing leakage caveat applies (parametric familiarity mitigated, not eliminated).

---

## 14. Risks & mitigations

| Risk | Mitigation |
|---|---|
| Model silently resolves "duplicative vs. parallel-but-justified" | `RELATE_OBLIGATION(parallel_distinct_purpose)` as first-class alternative to `MERGE`; normative gate; hard block on `final` |
| Consolidation silently converts guidance↔rule | `binding_force_conservation` invariant + per-se `change` rule (§7.4) |
| Consolidation deletes a statutory duty | `statutory_floor` invariant against a maintained floor list; hard block |
| As-enforced layer (CSI) unobservable publicly | Declared gap (§8.3); `unresolved` over guess; agency-internal deployment posture |
| Inventory rows are LLM-synthesized, not ground truth | Full-coverage §10 verification of MVP rows before L1 trust (M1 exit) |
| Rescission opacity corrupts currency data | `rescinded_informal` treatment status; archival reconstruction as an L0 adapter; `referential_integrity` invariant |
| No CCRC-grade labeled record | RBI mapping + Fed review + inventory reform columns as partial references; report agreement not accuracy; disagreement is output |
| Multi-agency: no single actor can execute operations | `actor_with_authority` + `instrument_required` on every operation; `interagency_coordination` flag |
| "Sludge" framing smuggles deregulation | Declared commitments (§2); NG1; burden delta always paired with "risk control preserved" statement (as the Reform Roadmap already does) |
| Primitive-set drift (adding banking primitives casually) | Engine checkpoint discipline: additions only via M0 residual, human-approved (§7.3) |
| Source rights | US statutes/regs/agency guidance are public; exchange listing standards and any licensed databases flagged in procurement; retrieval-only comparators |

---

## 15. Portability (adapters, honest)

This project *is* the engine's §15 adapter model exercised for the first time. The banking adapter supplies: eCFR/US Code/guidance-registry parsers; the instrument hierarchy (in place of court hierarchy); rescission/treatment tracking (in place of a citator); agency-authority metadata; the statutory-floor list; snapshot conventions. Next adapter candidates: **UK PRA/FCA** (Rulebook/Handbook structure is cleaner; SS/DP guidance strata analogous), other US agency corpora (the supervisory-guidance stock analyzed in the Substack post), and state insurance regulation. Each requires its own floor list and force taxonomy; the calculus and schema core stay shared.

---

## 16. Worked slice — risk-appetite approval (illustrative)

- **as-built (`inventory_as_of`):** the risk committee must approve and periodically review the enterprise risk-management framework (12 CFR 252.33(a)(1), regulation, BHC level); the bank board must approve a written risk-governance framework (OCC 12 CFR 30 App. D II.A, enforceable guideline, IDI level); SR letters restate framework-approval expectations (guidance); cadences differ; "risk appetite" is undefined in one instrument and defined differently in another.
- **intended:** one enterprise risk-appetite/framework approval at the consolidated level, an IDI addendum certification, one canonical "risk appetite" definition, guidance cross-referencing the rule rather than restating it.
- **Finding 1.** `MERGE` (Reg YY approval + SR restatements → single approval) + `RESOLVE_CROSS_REFERENCE`. Effect: **codify** (guidance imposed nothing beyond the rule; binding force conserved — the survivor is the regulation). `actor_with_authority`: FRB. `instrument_required`: guidance_action + conforming rule note. Disposition: `auto_ok` candidate, but `needs_review` because operands span force strata.
- **Finding 2.** `RELATE_OBLIGATION(entity_level_mirror)` (Reg YY BHC duty ↔ OCC App. D IDI duty — **both survive**) + `FACTOR_EXCEPTION` (IDI addendum). Effect: **clarify**. Normative kind: `interagency_coordination` (FRB+OCC). Disposition: `needs_review`.
- **Finding 3.** `CANONICALIZE_DEFINITION` ("risk appetite"). Effect: **clarify** if the surviving definition matches supervisory practice; **change** if it narrows either instrument's scope — classifier must diff both. Disposition: `needs_review` (`interpretive_ambiguity`).
- **Non-finding (guardrail demo).** Merging the OCC App. D duty *into* Reg YY and repealing App. D would trip `binding_force_conservation` review (guideline→regulation conversion), `statutory_floor` check (§39 guideline authority), and `interagency_coordination` — surfaced, never auto-resolved.

---

## 17. Implementation phases

- **B0 — Banking M0: calculus closure (1 wk, largely manual).** Hand-express every "minimum reform lever" in the three MVP clusters as compositions of the 14 primitives (+ profile adaptations). Residual = missing primitives; test the `DEEM_SATISFIED` hypothesis. *Exit:* set closed, or an amended set proposed for human approval. *(Mirrors engine M0; checkpoint discipline applies.)*
- **B1 — Corpus retype + verification (1–2 wk).** Inventory-xlsx adapter → `DutySpec`s; instrument hierarchy graph for MVP clusters; full-coverage claim verification (§10); statutory-floor list v1. *Exit:* ~60 verified `DutySpec`s + graph + floor list.
- **B2 — Schema extension + fixtures (1–2 wk).** `DutySpec`, profile enums, profile invariants in the shared canonical schema; a deterministic risk-appetite fixture (the §16 slice) in the engine's fixtures-first style, gold findings included. *Exit:* engine test suite green with the banking profile; fixture round-trips.
- **B3 — Calculus engine over MVP clusters (2–3 wk).** Diagnostics → operations (with authority/instrument fields) → invariants → effect classes; LLM-assisted steps only behind the interfaces the fixture slice proved, temperature 0, every claim span-anchored. *Exit:* findings for all three clusters; agreement vs. hand labels measured.
- **B4 — Render + workbench (1–2 wk).** Per-cluster consolidation package: redline, crosswalk, burden delta, authority-to-act table, review queue, final-status blocker summary. *Exit:* full packages + working disposition loop.
- **B5 — Evaluation (1–2 wk).** §13 incl. baselines and the RBI rediscovery spike. *Exit:* eval report + error taxonomy.
- **B6 — Scale + second adapter (scoping).** Remaining ~27 clusters; PRA/FCA adapter spec.

---

## 18. Open questions

1. **Naming.** *Lex-Balanus* / *BoardDistill* are provisional; also unresolved whether the profile should be scoped as "prudential-supervision duties" (wider than boards) from the start.
2. **Label unit.** Duty-row vs. duty-element vs. cluster? (Lean: duty-row keyed to element-level operands, mirroring the engine's dual-key lean.)
3. **Statutory-floor list governance.** Who maintains it, and is "dilute" (vs. "delete") detectable mechanically or always a review item?
4. **Burden quantification.** The inventory's Burden Model (board-hours) is attractive but soft — include as annotation only, or as a ranked prioritization signal?
5. **RBI benchmark data.** Confirm the old→new traceability mapping is published at sufficient granularity for §13 scoring (the `policy-sludge-cleanup` analysis suggests yes).
6. **`DEEM_SATISFIED` scope.** If confirmed by B0, does it subsume safe harbors generally, or only cross-regime satisfaction?
7. **Engine repo relationship.** Monorepo profile vs. separate repo importing the engine as a package? (Lean: same repo as the engine until B3, then decide.)

---

## 19. Appendix — cold-start file map & glossary

**To replicate from nothing, read in this order:**
1. This PRD.
2. `statute-distill_lex-allium/statutedistill-prd-v0.2.md` — engine rationale (calculus, effect classes, gates).
3. `statute-distill_lex-allium/AGENTS.md` — build discipline, canonical models, non-negotiable invariants (§2 there is binding here too).
4. `bank boards_cumulative-sludge/README.md` — corpus provenance and eval methodology.
5. `Synthesis/gsib-board_duties-combined_inventory.xlsx` — the L1 input (sheets: All Board Duties, Duplicate Clusters, Reform Roadmap, Burden Model, Currency Log, Verification).
6. `Tools/policy-sludge-rubric-v2.md` + `policy-sludge-llm-judge-prompt-v2.md` — the §10 verification harness.
7. `lex-allium_feasibility_board-duties.md` — the mapping analysis this PRD operationalizes.
8. External: the Substack write-up (context), the `policy-sludge-cleanup` skill repo (RBI method), `statute-distill_lex-allium/FIXTURE_NOTES.md` (fixture conventions to mirror in B2).

**Glossary:** *cumulative sludge* (accreted low-value obligation stock) · *duty* (one actor–verb–object–cadence obligation from one instrument) · *two-layer* (binding obligation vs. supervisory expectation) · *instrument hierarchy* (statute > regulation > enforceable guideline > guidance > manual) · *as-built / intended* (current duty stock at snapshot / proposed consolidated stock) · *effect class* (codify / clarify / fill_gap / change / unresolved) · *statutory floor* (duties no consolidation may remove) · *binding-force conservation* (no silent guidance↔rule conversion) · *rediscovery* (held-out benchmark: recover RBI's mapping) · *CSI gap* (confidential supervisory information excluded from public-source runs).
