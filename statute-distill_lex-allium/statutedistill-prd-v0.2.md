# PRD — StatuteDistill (with Lex-Allium)

**An evidence-backed statutory recodification *workbench*: make a reform commission's legal reasoning explicit, reviewable, and reproducible — with the D.C. Criminal Code Reform Commission as the reference implementation.**

| | |
|---|---|
| **Status** | Draft v0.2 (consolidated; supersedes Lex-Allium v0.1) |
| **Owner** | Mike Hsu |
| **System name** | *StatuteDistill* (the engine) |
| **Spec-language layer** | *Lex-Allium* (a criminal-statute domain profile over Allium v3) |
| **Reference implementation** | D.C. CCRC corpus, 2016–2022 |
| **Posture** | Assistive workbench, not automated recodification (see §3) |

---

## In plain English (for a policymaking audience)

**The problem.** Laws pile up over decades. New statutes get layered on top of old ones, definitions multiply and conflict, key terms go undefined, and courts quietly fill the gaps — so that what the law actually requires often can't be found by reading the statute alone. The result is a body of law that is hard for citizens to follow, hard for officials to administer, and expensive to comply with. Cleaning this up has traditionally required a law reform commission: a multi-year, labor-intensive effort by expert lawyers. The District of Columbia's recent rewrite of its criminal code is one of the most thorough examples ever produced.

**The idea.** We are building a tool that learns from how that commission did its work and helps future reform efforts do the same thing faster, more transparently, and in a way that can be repeated in other places. It takes a tangled body of law, makes its actual rules explicit, flags the inconsistencies and gaps, and proposes clearer language — with every suggestion backed by a citation to the existing law and court decisions it relies on.

**The method.** The tool starts by reverse-engineering how the DC commission actually did its work — and in doing so it uncovers something useful: however sprawling a reform looks, the thousands of individual edits almost always reduce to a small, fixed set of basic moves. Merging two overlapping offenses into one. Splitting an overloaded provision apart. Giving a vague term a clear definition. Making an unstated requirement explicit. Retiring an obsolete rule. Lifting a principle that recurs throughout the code into a single general section. We call this small repertoire the *transformation calculus*, and it is what makes the whole exercise transparent: instead of an opaque 300-page rewrite, a reviewer sees each change, what type of move it is, and the existing statute or court decision it rests on. Every move is also tagged with its effect — whether it simply restates current law, clarifies an ambiguity, fills a genuine gap, or actually changes the law — and that tag is checked against what the courts already require, so that substantive changes can't hide inside routine housekeeping. The same handful of moves is also what lets the method carry over to other areas, like banking or tax rules.

**The guardrail that matters most.** The tool does not decide policy. It will never set a criminal penalty, judge whether a law is too harsh or too lenient, or make any value-laden choice on its own. Wherever a real political or legal judgment is required, it stops and hands that decision to a human — and keeps a record of who decided what and why. It is there to do the painstaking organizing and cross-checking, so that legislators and their staff can spend their time on the choices that are genuinely theirs to make.

**Why it matters.** Done well, this makes the law easier to read, cheaper to comply with, and more honest about what it actually requires — while keeping democratic control firmly in human hands. The criminal code is the starting point because the DC commission left such a complete record to learn from, but the same approach could help simplify banking rules, tax codes, and other areas where accumulated complexity has become a burden in its own right.

---

## 1. TL;DR (technical)

A legacy criminal code is a legacy codebase: decades of accreted statutes plus court opinions that silently patch gaps, with no way to tell intended behavior from accident. The CCRC spent ~5 years doing manually what software distillation does — recovering what the code *actually does* from statute-plus-case-law, stating what it *should do*, and classifying every divergence with a rationale. Its ~70 reports are a hand-authored divergence log.

StatuteDistill reconstructs that method as a layered, citation-anchored pipeline whose changes are expressed as compositions of a small **Transformation Calculus**, validated against the CCRC's own labeled output, and surfaced through a review workbench that routes every value-laden decision to a human. It is a **legibility and review system, not "law as code."** The general engine generalizes beyond criminal law (banking regulation, tax, policy-sludge reduction); criminal law is the first reference implementation because the CCRC left an unusually complete record.

---

## 2. Honest framing of normativity

This system is **not normatively neutral, and does not claim to be.** Calling "implicit mens rea" a *defect* is a Model-Penal-Code-aligned value commitment; treating overlap as redundancy assumes consolidation is good. The honest posture is therefore not neutrality but **declared, contestable commitments**, surfaced through a typed normative flag (§9) so a reviewer can see and contest them. Making a legal corpus legible is an intervention with a viewpoint, not a mirror — and the design states its viewpoint rather than hiding it inside the word "diagnostic."

---

## 3. Product posture: workbench vs. pipeline

- **Product promise:** "Make the reform commission's legal reasoning explicit, reviewable, and reproducible."
- **Not:** "Automate what the commission did."
- The system *frames, classifies, drafts, and evidences*; humans *decide*. Every value-laden decision is gated.
- **"Rediscovery"** — can the engine independently recover the CCRC's structural moves? — is retained as a **held-out research benchmark** (§13), explicitly separated from the product promise, and scored with the normative dials held out.

---

## 4. Goals / Non-goals

### Goals
- **G1.** Define the **Transformation Calculus** (§7): the primitive operation set from which every recodification change composes.
- **G2.** Distill an "as-built" spec from statute **+ a case-law authority graph** (§8), at a pinned legal snapshot.
- **G3.** Classify each divergence (codify / clarify / fill-gap / change) by diffing against the as-built baseline, with claim-level verification (§10).
- **G4.** Generate review artifacts: redline, penalty table, commentary, crosswalk, and an Allium view.
- **G5.** Validate against held-out CCRC offenses with expert-adjudicated precision/recall **and baselines**.
- **G6.** Ship a **jurisdiction adapter** model (§15) — a shared pipeline, not a jurisdiction-agnostic engine.

### Non-goals
- **NG1.** Setting penalties or making policy/proportionality choices.
- **NG2.** Producing operative legal text.
- **NG3.** Compiling statutes to machine-executable law (§6.3).
- **NG4.** Civil-law corpora in v1 (schema assumes common-law/MPC structure).

---

## 5. Background (self-contained)

**CCRC.** Independent DC agency (est. 2016) tasked with the first comprehensive rewrite of DC's criminal statutes since 1901. Benchmarked the MPC, sister-state codes, and ALI work; analyzed Superior Court charging/sentencing data; iterated ~70 public reports under a statutory Advisory Group that commented on every draft and whose dispositions were logged. Its product (the RCC / RCCA) passed the Council, was vetoed, overridden, then **nullified by Congress (H.J.Res. 26, March 2023)** and never took effect. *Consequence:* "before" = current operative Title 22; "after" = a complete **proposed** code. All RCC artifacts are public/government works.

**Per-provision asset.** Each provision shipped with revised black-letter text (App. A), a **redline vs. current code** (App. B), a penalty table (App. C), and commentary with an *Explanatory Note* and a **"Relation to Current District Law"** section classifying the change as **codifies / clarifies / fills a gap in / changes** current law — the reference labels for §7's effect classes.

**Allium (dependency, pinned).** LLM-native behavioral spec language; **v3** (with a v2→v3 migration guide), described in terms of entities, rules, transitions, and invariants. **Pre-release; pin the version.** The `allium-tools` CLI does more than validate: `analyse` runs reachability / conflict / invariant verification; `plan` derives test obligations; `model` extracts the domain model as structured data. We use Allium as a **render-and-validate view**, not as the source of truth (§6.1).

---

## 6. Conceptual model

### 6.1 Canonical schema is the source of truth; Allium is a view

To avoid coupling to a pre-release, fast-moving language, the **source of truth is a versioned, typed canonical schema** (JSON). `.allium` is *rendered from* the canonical schema and round-tripped through `allium check`/`analyse` for validation. This survives v3→v4 churn and lets `allium model`/`plan` feed back into our structured store.

### 6.2 The mechanical / normative boundary (central constraint)

Operations and classifications can *surface and propose*; they cannot *decide* whether a divergence is a bug or a feature — that is jurisprudential/political. Every finding carries a typed normative flag (§9); flagged findings route to human disposition. This is a hard requirement.

### 6.3 The legible-and-analyzable / executable fork (corrected)

Lex-Allium is **human-legible and statically analyzable, but not machine-executable as operative law.** Allium has no runtime, yet supports invariant verification and conflict detection — so we get checkable structural invariants (§7.4) without compiling liability into something that *executes on people*. The constitutional grounding (void-for-vagueness, fair notice, rule of lenity) is what keeps criminal statutes on this side of the fork — distinguishing this work from executable policy-as-code appropriate to reporting/prudential rules.

---

## 7. The Transformation Calculus (spine)

Four layers, kept distinct:

### 7.1 Diagnostics (detect → trigger)
Undefined term, duplicate definition, implicit mens rea, overlapping offenses, dead reference, scattered exception, recurring rule, archaic term, inconsistent grade, potential vagueness, merger conflict, impossible charging combination. Each diagnostic triggers one or more candidate operations.

### 7.2 Operations (the primitives) — fifteen

The set is **fifteen primitives**, validated by a hand-run M0 over theft/robbery/obstruction (which surfaced `RELATE-OFFENSE` as the fifteenth; see §7.5). *(Count corrected 2026-07-02: earlier drafts said "fourteen" while enumerating fifteen.)*

| Family | Primitives (arity / note) |
|---|---|
| **Structure** | `MERGE` (n→1), `SPLIT` (1→n), `INTRODUCE` (0→1), `REPEAL` (1→0), `RELOCATE` (subsumes Move-Definition, Reorganize-Chapter), `RELATE-OFFENSE` (typed edge between two **surviving** offenses: `aggravated_form_of` / `shares_term` / `merges_with`) |
| **Terminology** | `CANONICALIZE-DEFINITION` (n→1), `DEFINE-TERM` (0→1), `SUBSTITUTE-TERM` (1→1, **strictly meaning-preserving** rename) |
| **Liability** | `NORMALIZE-ELEMENTS` (→ typed conduct/result/circumstance), `ASSIGN-MENS-REA` (strict = "none"), `FACTOR-EXCEPTION` |
| **Penalty** | `REGRADE` (uniform class / adjust grade) — highest normative load |
| **General Part** | `ELEVATE-GENERAL-RULE` (lift recurring rule to shared part), `RESOLVE-CROSS-REFERENCE` (inline/canonicalize; usually cleanup) |

Inverse pairs: MERGE↔SPLIT, INTRODUCE↔REPEAL (supports round-tripping diffs). Each operation record carries: `operands[]`, `arity`, `inverse?`, `scope ∈ {special_part, general_part}`, `diagnostics_triggering[]`, `normative_load ∈ {low,med,high}` (and, for `RELATE-OFFENSE` only, `relation`).

**Refinements from M0:** (1) `INTRODUCE` / `ELEVATE-GENERAL-RULE` / `RELOCATE` carry an explicit `scope` — the General Part build (culpability-distribution rule, causation, merger provision, penalty-class scheme) is these ops at `general_part` scope. (2) `SUBSTITUTE-TERM` is strictly meaning-preserving; a term swap that changes scope is `DEFINE-TERM` with a `change` effect, not `SUBSTITUTE-TERM`.

**Composites decompose** (validation that the basis is minimal): Consolidation = MERGE + CANONICALIZE-DEFINITION + RESOLVE-CROSS-REFERENCE; Codify-Common-Law = INTRODUCE/ELEVATE + ASSIGN-MENS-REA + DEFINE-TERM; Modernize = SUBSTITUTE-TERM×n. "Clarification" is **not** an operation — it is an effect class (§7.3). `RELATE-OFFENSE` is **not** a composite — it was added precisely because reconstructing offense-to-offense coupling from shared definitions + a general merger rule loses the relational intent a reviewer needs surfaced as one move.

### 7.3 Effect classification (label, contextual)
`codify | clarify | fill_gap | change`. **Determined by diffing an operation's output against the as-built baseline — which requires the §8 authority graph.** The *same* operation yields different effect classes in different contexts (e.g., `ASSIGN-MENS-REA` is `codify` if courts already required the mental state, `clarify` if ambiguous, `change` if newly imposed). CCRC "Relation to Current District Law" labels are the reference, **treated as contestable labels, not ground truth**; disagreement is a first-class output.

### 7.4 Invariants (validate)
Checked pre/post via `allium analyse`: `total_mens_rea` (every element has a mental state), `referential_integrity` (no dangling refs), `definitional_uniqueness` (one canonical definition per term), `penalty_monotonicity` (class monotonic in harm/culpability), `constitutional_floor` (no facial vagueness). Violations block "final" status absent a recorded reviewer exception.

**Pipeline reads as compiler passes:** diagnostic pass (flag) → operation pass (rewrite) → invariant pass (validate) → classification pass (label effect vs. baseline).

### 7.5 M0 validation (provenance of the fifteenth primitive)
A hand-run M0 decomposed the high-salience CCRC changes to theft, robbery, and obstruction into the primitive set. All fourteen original primitives fired; every sampled change composed **except** cross-offense *relational* moves — robbery designed as the force-bearing sibling of a theft gradation, sharing theft's canonical defined terms and de-conflicted by the general merger provision (RCC § 22E-214). That coupling is reconstructable as a composite (shared `CANONICALIZE-DEFINITION` + general-scope `ELEVATE-GENERAL-RULE`) but the reconstruction loses the relational intent, so `RELATE-OFFENSE` was adopted as a first-class fifteenth primitive for legibility. The automated M0 (T-CALCULUS, see AGENTS.md) must reproduce this over fixtures.

---

## 8. Case-law authority graph (the core hard problem)

Statute alone is not the implementation; **statute + interpreting case law** is. Recovering the judicially-supplied layer (esp. implicit mens rea) is the highest-value, hardest task and **is not ordinary RAG.** Required graph properties per authority:
- court and position in hierarchy (controlling vs. persuasive);
- date and **as-of validity** at the chosen snapshot;
- **negative treatment** (overruled / abrogated / distinguished);
- **holding vs. dicta** distinction;
- the specific statutory element/term the authority bears on.

The authority graph is what makes effect classification (§7.3) possible and is a first-class deliverable, not a retrieval afterthought.

### Snapshot freeze (mandatory)
Three pinned dates on every run, because CCRC labels were written against a historical DC code, not today's:
- `before_as_of` — the vintage of DC law the relevant CCRC report cited (per-report);
- `reform_as_of` — the RCC version;
- `current_as_of` — the live code (for present-day delta only).
The as-built spec is distilled from `before_as_of`, **not** the current code, or the eval measures statutory drift instead of method fidelity.

---

## 9. Normative flag (typed kind + disposition state)

Split into two axes (a boolean is too crude, but so is one flat enum):

- **Kind** (what makes it normative): `policy_choice` · `penalty_value_judgment` · `constitutional_risk` · `doctrinal_ambiguity` · `institutional_discretion`.
- **Disposition state** (routing/status): `auto_ok` → `needs_review` → `reviewer_accepted | reviewer_rejected | reviewer_modified`, with reviewer id, timestamp, rationale.

`REGRADE` and any `change`-class finding default to `needs_review`. No finding reaches "final" with an open normative kind and an unresolved disposition state — the Advisory-Group analog, mechanized.

---

## 10. Claim-level verification (not "citation exists")

Every legal claim emits a verifier record: `claim`, `source_span`, `support_type ∈ {quoted, paraphrased}`, `authority_type ∈ {statute, controlling_case, persuasive_case, comparator, secondary}`, `as_of_valid`, `confidence`, `verifier_status ∈ {verified, unverified, contradicted}`. Comparators are **retrieval-only** (no parametric legal authority). `contradicted` or `unverified` above threshold blocks final status. Hallucinated-citation rate is a tracked release gate.

---

## 11. Architecture (layers)

```
L0  Sources + Adapters       statute parser · case-law corpus · comparator corpus ·
                             court data · citation format · constitutional constraints
                             (+ snapshot dates §8)
L1  Distill → as-built spec  canonical schema, populated via case-law authority graph
L2  Intent → intended spec   elicited, or imported reform draft (RCC) parsed to schema
L3  Calculus                 Diagnostics → Operations → Invariants → Effect classes (§7)
L4  Render + Verify          redline · penalty table · commentary · crosswalk · .allium view
                             + claim-level verification (§10)
L5  Review Workbench         typed normative flags · disposition state machine · audit log
OUT per-offense package mirroring a CCRC report — audit-grade, citation-anchored, reviewable
```

---

## 12. MVP scope (credible)

Not "full DC offense set." MVP covers **10–20 offenses with hand-built gold labels**, spanning:
- Property: theft, robbery (+ carjacking for the penalty-controversy signal);
- Persons: one homicide and one assault offense;
- General Part: one topic (default culpability / causation).
Plus the §8 authority graph for those offenses only, and the §13 eval on a held-out slice of them.

---

## 13. Evaluation

**Product (workbench) metrics** — expert-adjudicated **precision/recall** on extracted offense elements, mens rea, defenses, gradations, and material divergences; redline overlap vs. App. B; classification agreement vs. CCRC labels (reported as agreement, disagreements characterized); citation-integrity rate (§10); Pass^K stability.

**Baselines (mandatory):** plain LLM, RAG-only, and human paralegal / law-student review. Metrics are uninterpretable without them.

**Research benchmark (held out, §3):** rediscovery — given `before_as_of` law, how much of the CCRC's *structural* move set (the Calculus operations and their effect classes) does the engine recover, **with penalties/policy dials held out**? Scored on operation-set and effect-class agreement, never on reproducing DC's specific penalty choices.

---

## 14. Risks & mitigations

| Risk | Mitigation |
|---|---|
| Model silently resolves bug-vs-feature | Typed normative flag + disposition gate (§9), hard block on final |
| "Diagnostics" smuggle normative commitments | Declared commitments (§2); each diagnostic maps to a contestable rationale |
| Case-law layer mis-extracted / stale | Authority graph with as-of validity + negative treatment (§8); mark `unresolved` over guess |
| Snapshot drift | Mandatory three-date freeze (§8); distill from `before_as_of` |
| Hallucinated authority | Retrieval-only comparators + claim-level verifier + release gate (§10) |
| **Source rights** | DC Code + CCRC docs are public/government; **MPC & ALI materials are copyrighted; citators (Shepard's/KeyCite) and some case-law services are licensed** — comparator/treatment index must use licensed or open substitutes; flagged in procurement |
| Over-portability claims | Adapter model (§15), not "jurisdiction-agnostic" |
| Allium pre-release breakage | Canonical schema is source of truth; Allium pinned as a view (§6.1) |

---

## 15. Jurisdiction adapters (portability, honest)

A **shared pipeline with per-jurisdiction adapters**, each supplying: statute parser/format; citation format; court hierarchy; case-law corpus + treatment source; comparator corpus (model/sister codes); constitutional constraints as invariants; snapshot-date conventions. Non-MPC/civil-law jurisdictions require forking the §6 canonical schema first.

---

## 16. Worked slice — Theft (illustrative)

- **as-built (`before_as_of`):** current DC theft turns on "wrongfully obtains or uses … without authority or right," with intent-to-deprive supplied/shaped by DCCA case law; mens rea for several elements is implicit and judicially construed; conduct is means-based.
- **intended (RCC):** a single normalized theft offense — typed elements (control over property; absent owner consent; intent to deprive), explicit mens rea per element, value-based gradations with strict liability "in fact" on value, merger contract with fraud.
- **Finding 1.** Operation `DEFINE-TERM` ("without authority or right" → "without consent of an owner"). Effect: **clarify** (resolves an ambiguous element; courts had construed it). Normative kind: `doctrinal_ambiguity`. Citations: current theft §; DCCA construction; RCC §. Disposition: `needs_review`.
- **Finding 2.** Operation `MERGE` (fold trick/false-pretense conduct out of theft into the revised fraud offense, removing dual theft+fraud liability). Effect: **change** (alters charging/merger consequences). Normative kind: `policy_choice`. Disposition: `needs_review`.
- **Reviewer queue:** both findings surfaced with evidence spans; reviewer accepts/rejects/modifies, rationale logged.

---

## 17. Implementation phases

- **M0 — Calculus validation (1 wk).** Express every change in 3–5 CCRC offenses as compositions of §7 primitives; residual = missing primitives. *Exit:* the set is closed over the sample, or an amended set is.
- **M1 — Corpus + snapshot (1–2 wk).** Acquire CCRC reports (App. A/B/C + commentary), DC Code XML at `before_as_of` vintages, build authority graph for MVP offenses. *Exit:* `before/intended/alignment` + authority graph for §12 offenses.
- **M2 — Distill + canonical schema (2–3 wk).** L1/L2; populate via authority graph. *Exit:* MVP offenses distilled; gold labels hand-built.
- **M3 — Calculus engine (3–4 wk).** Diagnostics → operations → invariants → effect classifier. *Exit:* findings for MVP; agreement vs. CCRC measured.
- **M4 — Render + verify + workbench (2 wk).** L4/L5 incl. claim-level verification and disposition state machine. *Exit:* full per-offense packages + working review loop.
- **M5 — Evaluation (2 wk).** §13 incl. baselines. *Exit:* eval report + error taxonomy.
- **M6 — Second-jurisdiction adapter (scoping).** *Exit:* adapter spec + spike.

---

## 18. Long-term vision

A general legislative-engineering platform: criminal law (reference), then banking/securities regulation, tax, environmental, administrative procedure, municipal ordinances, agency manuals — supporting machine-readable legislation, AI-assisted drafting, regulatory modernization, and policy-sludge reduction. The Calculus is the portable core; the authority graph and adapters localize it. The CCRC is the first reference implementation because its record is uniquely complete; the banking-regulation consolidation problem (thousands of accreted instruments → a small set of consolidated directions) is the same calculus — predominantly MERGE + CANONICALIZE-DEFINITION + REPEAL + RESOLVE-CROSS-REFERENCE — applied to a different corpus.

---

## 19. Open questions

- Label unit: provision / element / redline-hunk / mens-rea-rule / gradation / penalty / commentary-paragraph? (Lean: element-and-redline-hunk, dual-keyed.)
- Representing stratified intent (1901 Congress vs. amendments vs. courts) — pace-layered annotations on the intended spec?
- Treatment-data source under §14 licensing constraints (open citator vs. licensed).
- Second-jurisdiction target for M6.

---

## 20. Appendix — lineage & glossary

Spec-as-durable-thinking / rule-as-output; architect–gardener maintenance (Allium `tend`/`weed`); pace layers; legibility (*Seeing Like a State*, turned on the tool itself, §2); the legible-and-analyzable / executable fork. Glossary: as-built / intended; the §7 operation set; effect classes; authority graph; normative kind vs. disposition state; claim-level verifier.
