# AGENTS.md — BoardDistill / Lex-Balanus MVP build (v1)

**Audience:** an autonomous coding agent (Claude Code terminal, Codex, or equivalent).
**Companion specs (all in `specs/`):** `specs/boarddistill-prd-v0.1.md` (rationale) · `specs/B0_calculus-closure.md` + `specs/b0_decompositions.json` (approved calculus amendments + fixture sources) · the engine pair `specs/statutedistill-prd-v0.2.md` and `specs/statutedistill-AGENTS.md` (parent conventions) · `specs/statutedistill-FIXTURE_NOTES.md` (fixture labeling conventions). **If this file conflicts with the PRDs, follow the PRDs and stop to flag it.**

Read the whole file before writing code. The single most important instruction: **slice one is deterministic and fixtures-first. No LLM, no network, no scraping.** You are proving the architecture's spine on the banking profile, not building regulatory AI.

**Placement:** you are at the repo root. The corpus (inventory xlsx, reports, eval harness) lives one level up in the parent folder; reference it read-only via `../Synthesis/`, `../Tools/`, `../Reports/`.

---

## 0. What you are building (and not)

Build the first **deterministic vertical slice** of the shared distillation engine, with the **banking profile (Lex-Balanus) as the first fully-exercised profile**:

```
profile-parameterized canonical schema → fixture corpus → instrument hierarchy graph
   → as-built / intended DutySpecs → diagnostics → calculus operations
   → findings (+ effect class) → invariants → claim verification
   → review state → rendered consolidation package
```

**Architecture decision (PRD §18 Q7, resolved for slice one):** a single repo with a generic core and profile packages. The core (`distillcore/`) holds everything profile-independent; `profiles/lex_balanus/` supplies the banking enums, models, invariants, and fixtures. Create `profiles/lex_allium/` as a **stub only** (enums + `NotImplementedError` loaders) so the criminal profile from the engine AGENTS.md can land later without core changes. Do not build the criminal slice now.

**Do NOT implement in slice one:** LLM prompting or model-generated legal conclusions; live eCFR/US-Code/guidance retrieval; Wayback reconstruction; web UI; full 230-row corpus verification; burden quantification; the RBI benchmark. The inventory-xlsx adapter IS in scope (T8) because it is deterministic and local — but its outputs are drafts marked `unverified`, never trusted findings.

---

## 1. How you must work

- **Test-first, deterministic.** Same inputs → same outputs. No randomness, no clock-dependent core logic, no network. `pytest` is the gate.
- **Small steps**, one task (§12) per change-set; run `make check` (ruff + mypy --strict + pytest) before "done".
- **No uncited legal claims.** Every legal assertion in any spec or finding points to ≥1 `SourceSpan`. A claim with no span is a bug.
- **Stop at checkpoints (§14)** — do not author gold labels you then grade against without marking them, do not resolve a normative review item, do not add a primitive beyond the approved fifteen.
- Commit messages reference the task id (e.g., `T-CALCULUS: 15-primitive enum + DEEM_SATISFIED validation`).

---

## 2. Non-negotiable invariants — enforce IN CODE with tests

`distillcore/` and `profiles/lex_balanus/invariants.py` enforce these; `tests/test_invariants.py` is the regression spine. Items 1–8 are inherited from the engine AGENTS.md §2; items 9–12 are banking-profile additions.

1. **Snapshot present.** Every `DutySpec` carries `SnapshotDates(inventory_as_of, consolidation_as_of, current_as_of)`; validation rejects specs without it.
2. **Every claim has a span.** A `LegalClaim` with empty `source_span_ids` fails verification.
3. **Effect class needs a baseline.** `Finding.effect_class` is computed only by diffing against an as-built baseline from the instrument hierarchy graph. **No baseline ⇒ `effect_class = "unresolved"`. Never guess.**
4. **Closed primitive set.** `Operation.primitive` is the fixed `PrimitiveOp` enum enumerated in §5 (16 members). A free-text primitive is invalid.
5. **effect_class ≠ primitive.** Different types; never conflated (test for exactly this).
6. **Normative gate.** A `Finding` with non-empty `normative_kind` and unresolved `disposition_state` cannot reach `final`.
7. **Verification gate.** Any `unverified` or `contradicted` claim blocks `final`.
8. **REGRADE / change default to review.** Any `REGRADE` op or `change`-class finding defaults `disposition_state = "needs_review"`.
9. **Binding-force conservation (per-se rule).** If a finding's output `legal_force` differs from *all* operand duties' `legal_force`, the finding is `change`-class **mechanically**, must carry `force_conversion_declared = True`, and defaults `needs_review`. An undeclared force conversion fails validation (this is a *require-declaration* invariant, not a block — see fixture D6).
10. **Statutory floor.** No composition of operations may `REPEAL` or `MERGE`-away a duty whose `instrument_stratum == "statute"` or that appears on the profile's `statutory_floor` list (`profiles/lex_balanus/statutory_floor.json`). `DEEM_SATISFIED` against a floor duty is permitted (the duty survives) but always `needs_review`. Violations are hard blocks.
11. **APA pathway.** Every `change`-class finding must carry a non-null `instrument_required`; `instrument_required = "guidance_action"` on a `change` to a *binding* duty fails validation ("just update the manual" is not a lawful pathway for a binding change).
12. **DEEM_SATISFIED survival.** Both `satisfied_ref` and `satisfying_ref` must resolve to duties that **survive** in the intended spec (distinct from `MERGE`); `conditions` must be non-empty. Validate in the model.

---

## 3. Stack (decided)

Python 3.11+ · `uv` · **Pydantic v2** (canonical models, JSON source of truth, `ConfigDict(extra="forbid")`) · **Typer** (CLI) · `pytest` (+`pytest-cov`) · `ruff` + `mypy --strict` · `networkx` for the in-memory instrument graph behind a `GraphStore` protocol · `openpyxl` **only** inside `adapters/inventory_xlsx.py` (T8). Outputs are Markdown + JSON. Flat-JSON/SQLite only; no server DB. **No Anthropic SDK, no requests/httpx in slice one.**

---

## 4. Repository layout

```
boarddistill/                      # package root (working name; rename is cosmetic)
  distillcore/                     # profile-independent
    models/
      base.py          # SnapshotDates, SourceSpan, LegalClaim, VerifierRecord
      calculus.py      # Operation (generic envelope), EffectClass, Diagnostic,
                       #   decompose()/validate_composition() parameterized by profile
      review.py        # Finding, ReviewDisposition, disposition state machine
      graph.py         # GraphStore protocol: baseline_for(target_ref, as_of)
    pipeline/
      distill.py align.py diagnostics.py operations.py classify.py
      invariants.py    # core gates (items 1-8) + hook for profile invariants
      verify.py render.py
  profiles/
    lex_balanus/
      enums.py         # PrimitiveOp(15), VerbStandard, LegalForce, RelationType,
                       #   NormativeKind, InstrumentRequired, Consequence, Cadence
      models.py        # DutySpec, DutyElement, InstrumentNode, InstrumentGraph
      invariants.py    # items 9-12
      statutory_floor.json
      composites.py    # profile decompose() table (§6)
    lex_allium/        # STUB: enums per engine AGENTS §5; loaders raise NotImplementedError
  adapters/
    fixture_loader.py  # load + validate a fixture dir into models
    inventory_xlsx.py  # T8: deterministic xlsx → draft DutySpecs (all claims "unverified")
    fba.py             # STUB: real eCFR/guidance ingestion (NotImplementedError) — §13
  cli.py               # Typer app (§7)
schemas/
  canonical.schema.json            # exported JSON Schema: DutySpec + Finding + Operation
data/fixtures/us-gsib/
  icfr/                # D4 — primary fixture
  sr12-17/             # D6 — binding-force invariant fixture
  board-effectiveness/ # D7 — codify-class contrast fixture
  _source/b0_decompositions.json   # copied from corpus folder; provenance for gold labels
outputs/.gitkeep
tests/
  test_models.py test_fixture_loader.py test_invariants.py
  test_calculus_banking.py test_verification.py test_render_package.py
  test_inventory_adapter.py
```

---

## 5. Domain models (build first)

### Core (`distillcore/models/`) — shapes shared with the engine
- `SnapshotDates{ inventory_as_of: date, consolidation_as_of: date, current_as_of: date }` (field names are the banking profile's; keep them profile-supplied aliases over a generic three-date model so lex_allium's `before/reform/current` maps onto the same type)
- `SourceSpan{ id, source_id, citation, start: int|None, end: int|None, quote: str|None }`
- `LegalClaim{ id, claim, source_span_ids: list[str], support_type: Literal["quoted","paraphrased"], authority_type: Literal["statute","regulation","enforceable_guideline","guidance","manual","comparator","secondary"], as_of_valid: bool, confidence: float, verifier_status: Literal["unverified","verified","contradicted"] = "unverified" }`
- `EffectClass = Literal["codify","clarify","fill_gap","change","unresolved"]`
- `Diagnostic{ kind: str, target_ids: list[str], rationale: str, source_span_ids: list[str] }`
- `Operation` (generic envelope): `{ id, primitive: <profile enum>, operands: list[str], outputs: list[str], arity, inverse: str|None, scope: Literal["duty_level","general_part"] = "duty_level", diagnostics_triggering: list[str], normative_load: Literal["low","med","high"], actor_with_authority: list[str], instrument_required: <profile enum>|None, relation: <profile enum>|None, satisfied_ref: str|None, satisfying_ref: str|None, conditions: list[str], parameter: Literal["verb_standard","cadence"]|None }`
  - `relation` set **iff** primitive is `RELATE_OBLIGATION`; `satisfied_ref`/`satisfying_ref`/`conditions` set **iff** `DEEM_SATISFIED`; `parameter` set **iff** `ASSIGN_DUTY_PARAMETER`. Validate all three.
- `Finding{ id, provision, as_built_ref, intended_ref, operation_ids, effect_class, rationale, baseline: SourceSpan|None, normative_kind: list[<profile enum>] = [], disposition_state: Literal["auto_ok","needs_review","reviewer_accepted","reviewer_rejected","reviewer_modified"] = "needs_review", force_conversion_declared: bool = False, confidence: float, verifier_records: list[str], status: Literal["draft","final"] = "draft" }`

### Banking profile (`profiles/lex_balanus/`)
- `PrimitiveOp` enum — **exactly this list, in this order** (B0 TODO 1–2 approved):

  ```
  MERGE, SPLIT, INTRODUCE, REPEAL, RELOCATE, RELATE_OBLIGATION,
  CANONICALIZE_DEFINITION, DEFINE_TERM, SUBSTITUTE_TERM,
  NORMALIZE_ELEMENTS, ASSIGN_DUTY_PARAMETER, FACTOR_EXCEPTION,
  REGRADE, ELEVATE_GENERAL_RULE, RESOLVE_CROSS_REFERENCE, DEEM_SATISFIED
  ```

  Derivation: the engine's enum with `RELATE_OFFENSE→RELATE_OBLIGATION` and `ASSIGN_MENS_REA→ASSIGN_DUTY_PARAMETER` (the approved generalization over `verb_standard`/`cadence` — `ASSIGN_DUTY_STANDARD` is **not** a member), plus `DEEM_SATISFIED`. That is **16 members**. Write the count test against this explicit list (`len(PrimitiveOp) == 16`), not against prose.

  > ✅ **Resolved 2026-07-02 (was checkpoint §14.5).** Parent-doc prose counts corrected: the engine set is **fifteen** primitives (earlier prose said fourteen); the banking set is **16 members** (the fifteen with two profile renames, plus `DEEM_SATISFIED`). The enum list above remains the ground truth.
- `RelationType = Literal["implements","elaborates","parallel_distinct_purpose","entity_level_mirror","shares_term"]`
- `VerbStandard = Literal["approve","review_and_challenge","receive_report","be_informed","certify","none_specified"]`
- `LegalForce = Literal["statute","regulation","enforceable_guideline","guidance","manual"]` · `TreatmentStatus = Literal["active","amended","superseded","rescinded_formal","rescinded_informal","stale_unverified"]`
- `NormativeKind = Literal["policy_choice","supervisory_value_judgment","statutory_constraint","interpretive_ambiguity","institutional_discretion","interagency_coordination"]`
- `InstrumentRequired = Literal["rule_apa","joint_rulemaking","interagency_statement","guidance_action","statutory_amendment"]`
- `DutySpec{ duty_id, label, layer: Literal["as_built","intended"], snapshot_dates, board_level, director_class, entity: Literal["BHC","IDI","both"], verb_standard: VerbStandard, object: str, cadence, trigger: str|None, legal_force: LegalForce, consequence, instrument_id, currency_status: TreatmentStatus, source_citations, claims: list[LegalClaim], confidence }`
- `InstrumentNode{ id, citation, agency, stratum: LegalForce, effective_date: date, treatment_status: TreatmentStatus, treatment_date: date|None, bears_on: list[str] }` · `InstrumentGraph{ nodes, edges }` implementing `GraphStore.baseline_for(duty_ref, as_of)` → the highest-stratum, active, as-of-valid node bearing on the duty, else `None`.

---

## 6. Definitions / refinements that affect modeling

- **`DEEM_SATISFIED` is not decomposable.** `decompose()` must not map any composite to it, and `validate_composition()` must assert it is never re-expressed as `RESOLVE_CROSS_REFERENCE + FACTOR_EXCEPTION` (test: the D4 gold finding composes to a single `DEEM_SATISFIED`, residual empty).
- **`ASSIGN_DUTY_PARAMETER` effect semantics:** assigning a parameter that was implicit/`none_specified` → `codify` or `clarify` (baseline-dependent); re-assigning an explicit parameter → `change` per se. Encode in `classify.py`; test both branches.
- **`SUBSTITUTE_TERM` remains strictly meaning-preserving** (inherited).
- **Per-se force rule** (§2.9) lives in `classify.py` *and* `invariants.py`: classifier sets `change`, invariant demands the declaration.
- **Profile composites** (`composites.py`): `consolidation=[MERGE, CANONICALIZE_DEFINITION, RESOLVE_CROSS_REFERENCE]` · `master_direction_build=[INTRODUCE(general_part), MERGE, REPEAL, RESOLVE_CROSS_REFERENCE]` · `board_role_clarification=[ASSIGN_DUTY_PARAMETER, SPLIT]` · `vertical_rationalization=[RELATE_OBLIGATION(entity_level_mirror), DEEM_SATISFIED, FACTOR_EXCEPTION]` (the D8 schema). Assert in tests that `"streamlining"` and `"burden_reduction"` are **not** operations or effect classes.
- **The four pipeline layers stay separate modules** (diagnostics / operations / classify / invariants). Do not collapse them.

---

## 7. CLI (`cli.py`, Typer)

- `boarddistill validate-fixtures DIR` — load + schema-validate; non-zero exit on violation.
- `boarddistill run-fixture DIR --out OUTDIR` — distill → align → diagnose → operations (+ composition check) → classify → verify → write JSON.
- `boarddistill render-package OUTDIR` — write `package.md` from JSON outputs.
- `boarddistill verify OUTDIR` — recompute verifier statuses; print final-status blocker summary.
- `boarddistill eval-fixture DIR` — deterministic agreement on operation set + effect class vs `gold_findings.json`.
- `boarddistill import-inventory XLSX --out DIR` — T8 adapter; emits draft DutySpecs, every claim `unverified`, banner in output.

---

## 8. Fixtures (three, from B0; openly placeholder)

Author from `data/fixtures/us-gsib/_source/b0_decompositions.json` (already in place). Follow the engine's fixture conventions (`specs/statutedistill-FIXTURE_NOTES.md`): `[PLACEHOLDER]` = fabricated stand-in citation; `[FIXTURE]` = paraphrased reconstruction; unmarked quotes only from public-domain regulatory text actually present. Each fixture dir: `sources.json`, `instrument_graph.json`, `as_built.json`, `intended.json`, `gold_findings.json`.

1. **`icfr/` (D4 — primary).** As-built: Part 363 ICFR assessment duty (calendar-year, regulation) + SOX 404(b) attestation duty (fiscal-year, statute-derived rule). Intended: deem-satisfied with designated-laws annex. Gold findings: `DEEM_SATISFIED` (`change`, `policy_choice`, `needs_review`) · `FACTOR_EXCEPTION` (`clarify`) · `RELATE_OBLIGATION(parallel_distinct_purpose)` (`clarify`) · `ASSIGN_DUTY_PARAMETER(cadence)` (`change`, `institutional_discretion`, `needs_review`). Exercises: 15th primitive, parameter re-assignment branch, parallel-but-justified preservation.
2. **`sr12-17/` (D6 — force-invariant fixture).** As-built: two guidance-layer duties (SR 12-17 attributes) + Reg YY rule duty. Intended: content relocated into the rule, letter repealed. Gold findings: `RELOCATE` (`change` per-se, `force_conversion_declared=True`) · `ASSIGN_DUTY_PARAMETER(verb_standard)` ("ensure"→"oversee", `clarify`) · `REPEAL` (rider). Exercises: §2.9 (declared conversion passes; a mutated copy with `force_conversion_declared=False` must fail — write that negative test), §2.11.
3. **`board-effectiveness/` (D7 — codify contrast).** As-built: App. D III.F self-assessment (enforceable guideline) + SR 21-3 assessment (guidance), near-identical text. Intended: one assessment, survivor at guideline stratum. Gold findings: `MERGE` (`codify`) · `RESOLVE_CROSS_REFERENCE` (`codify`). Exercises: codify-class with cross-stratum operands still `needs_review`; baseline lookup through the instrument graph.

Also add `data/fixtures/us-gsib/_calculus/` stub: one BHC/IDI mirror pair validating the `vertical_rationalization` composite (D8 schema) — used only by `test_calculus_banking.py`.

Authoring fixtures is a **checkpoint (§14)**: draft them, leave `TODO(human): confirm placeholder labels`, proceed using the draft.

---

## 9. Render package

`outputs/<fixture>/` → `as_built.json`, `intended.json`, `findings.json`, `verification.json`, `review_queue.json`, `package.md`.

`package.md` must contain, in order: snapshot dates · cluster summary · as-built duties table (actor / verb / object / cadence / force / citation) · intended duties table · instrument-graph summary (incl. treatment statuses) · **findings table** (duty, primitive, effect_class, normative_kind, actor_with_authority, instrument_required, disposition) · **duty crosswalk** (old citation → intended home) · **authority-to-act table** · **claim-verification table** · **normative review queue** · **final-status blocker summary**.

---

## 10. Composition validation (in slice one — pure and deterministic)

`operations.py` implements `validate_composition(findings) -> list[Residual]`: every gold change must be a single primitive or a known `composites.py` entry; anything else is a residual. `run-fixture` fails on non-empty residual. The `_calculus` mirror stub must validate as the `vertical_rationalization` composite with `DEEM_SATISFIED` intact (proving the 15th primitive is exercised and not silently absorbed).

---

## 11. Required behavioral tests

1. A `LegalClaim` with empty `source_span_ids` fails verification and blocks `final`.
2. A `Finding` with `normative_kind` and unresolved disposition blocks `final`.
3. `len(PrimitiveOp) == 16` (the explicit §5 list); free-text primitive rejected; `ASSIGN_MENS_REA`/`ASSIGN_DUTY_STANDARD` are **not** members.
4. `effect_class` and `primitive` are distinct types (conflation is a type error).
5. No baseline ⇒ `effect_class == "unresolved"`, never guessed.
6. `DEEM_SATISFIED`: missing `conditions`, or a `satisfied_ref` absent from the intended spec, fails validation; D4 gold composes to a single `DEEM_SATISFIED` (not decomposable).
7. Force conversion: sr12-17 fixture passes with `force_conversion_declared=True`; mutated undeclared copy fails §2.9; a `change` to a binding duty with `instrument_required="guidance_action"` fails §2.11.
8. Statutory floor: a synthetic `REPEAL` targeting a `statute`-stratum duty is a hard block; `DEEM_SATISFIED` against a floor duty passes but is `needs_review`.
9. `ASSIGN_DUTY_PARAMETER`: implicit-assignment branch yields `codify|clarify`; explicit-reassignment branch yields `change`.
10. All three fixture packages render into `package.md` with findings table, crosswalk, and blocker summary.
11. `import-inventory` output: every emitted claim is `unverified` and every emitted spec fails `can_finalize()` (drafts can never silently finalize).

---

## 12. Build order (each task ends green on `make check`)

- **T0 Scaffold** — `git init` + initial commit of the pre-seeded tree (AGENTS.md, specs/, data/), then `pyproject.toml`, `Makefile` (`check` = ruff+mypy+pytest), Typer skeleton.
- **T1 Core models** — `distillcore/models/` + snapshot enforcement + exported `schemas/canonical.schema.json`.
- **T2 Profile** — `profiles/lex_balanus/` enums + `DutySpec`/`InstrumentNode` + `statutory_floor.json` v1 (12 U.S.C. 5365(h), 5365(i), SOX 301, FDI Act §36/Part 363 anchors, BSA program statutes) + lex_allium stub. *Tests:* #3.
- **T-CALCULUS** — generic `Operation` envelope validation (`relation`/`satisfied_ref`/`parameter` iff-rules), `composites.py`, `validate_composition()`. *Tests:* #4, #6 (composition half), composite assertions (§6).
- **T3 Invariants** — core gates + profile invariants (§2.9–2.12) + `can_finalize()`. *Tests:* #1, #2, #5, #7, #8, #9.
- **T4 Fixtures** — the three B0 fixtures + `_calculus` mirror stub + `fixture_loader.py` + `validate-fixtures` CLI. **Checkpoint.**
- **T5 Pipeline** — `distill`/`align`/`diagnostics`/`operations`/`classify`/`verify`; `run-fixture` CLI. *DoD:* all three fixtures produce findings matching gold operation+effect; residual empty; mirror stub composes to `vertical_rationalization`.
- **T6 Render** — `render.py`; `render-package` CLI. *DoD:* test #10.
- **T7 Verify/Review** — `verify` CLI; disposition state machine; final-status gates end-to-end.
- **T8 Inventory adapter** — `import-inventory` against `../Synthesis/gsib-board_duties-combined_inventory.xlsx` (read-only; do not modify anything outside the repo) ("All Board Duties" sheet → draft DutySpecs; map Layer→legal_force hints, Cluster, Board level, Cadence, Citation, Confidence, Status). *DoD:* test #11; ~230 drafts emitted; zero finalizable.
- **T9 Eval + README** — `eval-fixture` CLI (agreement vs gold); README with the §13 roadmap.

---

## 13. README "next steps" (write at T9; do NOT build now)

1. Human confirmation of fixture placeholder labels and of the T8 draft mappings (checkpoint outputs).
2. Full-coverage claim verification of the MVP-cluster rows (B1 exit criterion) — requires retrieval; design behind `verify`'s interface.
3. Real instrument-graph ingestion: eCFR/US Code parsing, guidance registries, archival rescission reconstruction (`rescinded_informal`).
4. **LLM-based distillation/diagnostics/classification behind the interfaces this slice proved** — temperature 0, structured output, every claim span-anchored.
5. Scale to all ~30 clusters; per-cluster consolidation packages (B4).
6. RBI Master-Directions rediscovery benchmark + baselines (the existing horserace reports in `Reports/` are the plain-LLM baselines).
7. lex_allium profile build per the engine AGENTS.md (proves the core is genuinely shared).
8. PRA/FCA adapter scoping.

**Dormant-but-load-bearing guardrails to restate in the README:** CSI gap (public runs are as-published, not as-enforced; `unresolved` over guess); snapshot rule (distill at `inventory_as_of`, never live law); retrieval-only authority (no parametric legal claims); source rights (exchange listing standards and licensed databases flagged; agency/eCFR text is public).

---

## 14. Checkpoints — stop, write `TODO(human)`, leave a draft

1. Authoring/confirming fixture placeholder labels (T4) and T8 column mappings.
2. A residual the calculus cannot express as one of the §5 primitives or a known composite — propose, do not add. (The set is human-approved as of B0; it changes only by this route.)
3. Any normative-review disposition (never resolve `needs_review` yourself).
4. Any statutory-floor edit (`statutory_floor.json` is human-owned; you may draft v1 in T2 but flag it).
5. A conflict between this file and either PRD.
6. Anything requiring network access, licensed text, or confidential supervisory information.

---

**Begin at T0. Slice one is deterministic and fixtures-first. Do not introduce an LLM, network, or scraping until the README roadmap step that names it.**
