# AGENTS.md — StatuteDistill / Lex-Allium MVP build (v2)

**Audience:** an autonomous coding agent (Codex, Claude Code terminal, or equivalent).
**Companion spec:** `statutedistill-prd-v0.2.md`. This file is the build order; the PRD is the rationale. **If they conflict, follow the PRD and stop to flag it.**

Read the whole file before writing code. The single most important instruction: **slice one is deterministic and fixtures-first. No LLM, no network, no scraping, no Allium.** You are proving the architecture's skeleton, not building legal AI.

---

## 0. What you are building (and not)

Build the first **deterministic vertical slice** that proves the spine:

```
canonical schema → fixture corpus → authority graph → as-built / intended specs
   → diagnostics → calculus operations → findings (+ effect class) → invariants
   → claim verification → review state → rendered package
```

Everything probabilistic (LLM-based distillation, retrieval) is introduced **later, behind interfaces this slice proves** (§13). Do not anticipate it now.

**Do NOT implement in slice one:** LLM prompting / model-generated legal conclusions; live case-law retrieval; live D.C. Code scraping; Allium CLI integration; web UI; full CCRC corpus ingestion; penalty-recommendation logic.

---

## 1. How you must work

- **Test-first, deterministic.** Same inputs → same outputs, every run. No randomness, no clock-dependent logic in core, no network. `pytest` is the gate.
- **Small steps**, one task (§12) per change-set; run `make check` before "done".
- **No uncited legal claims.** Every legal assertion in any spec or finding points to ≥1 `SourceSpan`. A claim with no span is a bug.
- **Stop at checkpoints (§14)** — do not author gold labels you then grade against without marking them, do not resolve a normative review item, do not add a primitive.
- Commit messages reference the task id (e.g., `T-CALCULUS: decompose() + 14-primitive enum`).

---

## 2. Non-negotiable invariants — enforce IN CODE with tests

`models/` and `pipeline/invariants.py` enforce these; `tests/test_invariants.py` is the regression spine.

1. **Snapshot present.** Every `OffenseSpec` carries `SnapshotDates(before_as_of, reform_as_of, current_as_of)`; validation rejects specs without it.
2. **Every claim has a span.** A `LegalClaim` with empty `source_span_ids` fails verification.
3. **Effect class needs a baseline.** `Finding.effect_class` is computed only by diffing against an as-built baseline from the authority graph. **No baseline ⇒ `effect_class = "unresolved"`. Never guess.**
4. **Closed primitive set.** `Operation.primitive` is the 14-member `PrimitiveOp` enum (§5). A free-text primitive is invalid.
5. **effect_class ≠ primitive.** They are different types and must never be conflated (there is a test for exactly this).
6. **Normative gate.** A `Finding` with non-empty `normative_kind` and an unresolved `disposition_state` cannot reach `final`.
7. **Verification gate.** Any `unverified` or `contradicted` claim blocks `final`.
8. **REGRADE / change default to review.** Any `REGRADE` op or `change`-class finding defaults `disposition_state = needs_review` (only an explicit rule may set `auto_ok`).

---

## 3. Stack (decided)

Python 3.11+ · `uv` · **Pydantic v2** (canonical models, JSON source of truth) · **Typer** (CLI) · `pytest` (+`pytest-cov`) · `ruff` + `mypy --strict` · `rich` (optional CLI output) · `networkx` for the in-memory authority graph behind a `GraphStore` protocol. Outputs are Markdown + JSON. SQLite/flat-JSON only; no server DB. **No Anthropic SDK, no requests/httpx in slice one.**

---

## 4. Repository layout

```
statutedistill/
  __init__.py
  models/
    canonical.py        # SnapshotDates, SourceSpan, LegalClaim, Element, MensReaAssignment, OffenseSpec
    authority.py        # Authority, AuthorityGraph, GraphStore protocol
    calculus.py         # PrimitiveOp (14-enum), Operation, EffectClass, Diagnostic, decompose()
    verification.py     # VerifierRecord, verification gates
    review.py           # Finding, ReviewDisposition, disposition state machine
  adapters/
    fixture_loader.py   # load + validate a fixture dir into models
    dc.py               # STUB: real DC Code/case-law ingestion (NotImplementedError) — §13
  pipeline/
    distill.py          # fixture as-built spec → validated OffenseSpec (no LLM in slice one)
    align.py            # current↔intended crosswalk (1:1 / merge / split / repeal / new)
    diagnostics.py      # detect → candidate operations
    operations.py       # build Operation records; M0 composition check
    classify.py         # effect_class via authority baseline; "unresolved" if none
    invariants.py       # §2 checks + can_finalize()
    verify.py           # set verifier_status per claim against fixture spans
    render.py           # JSON + package.md, incl. final-status blocker summary
  cli.py                # Typer app (§7)
schemas/
  canonical.schema.json # exported JSON Schema for OffenseSpec + Finding
data/fixtures/dc/theft/
  sources.json  authority_graph.json  as_built.json  intended.json  gold_findings.json
data/fixtures/dc/_calculus/      # tiny robbery↔theft stub for the RELATE-OFFENSE M0 test (§12 T-CALCULUS)
outputs/.gitkeep
tests/
  test_models.py  test_fixture_loader.py  test_invariants.py
  test_calculus_theft.py  test_verification.py  test_render_package.py
```

---

## 5. Domain models (build first, `models/`)

Pydantic v2, `model_config = ConfigDict(extra="forbid")`.

- `SnapshotDates{ before_as_of: date, reform_as_of: date, current_as_of: date }`
- `SourceSpan{ id: str, source_id: str, citation: str, start: int | None, end: int | None, quote: str | None }`
- `LegalClaim{ id, claim: str, source_span_ids: list[str], support_type: Literal["quoted","paraphrased"], authority_type: Literal["statute","controlling_case","persuasive_case","comparator","secondary"], as_of_valid: bool, confidence: float, verifier_status: Literal["unverified","verified","contradicted"] = "unverified" }`
- `Element{ id, type: Literal["conduct","result","circumstance"], text: str, source_span_ids: list[str] }`
- `MensReaAssignment{ element_id: str, mental_state: Literal["purpose","knowledge","recklessness","negligence","strict","unresolved"], explicit_or_implicit: Literal["explicit","implicit"], source_span_ids: list[str] }`
- `OffenseSpec{ offense_id, label, jurisdiction, layer: Literal["as_built","intended"], snapshot_dates: SnapshotDates, elements: list[Element], mens_rea: list[MensReaAssignment], gradations, defenses, definitions_used, cross_refs: list[str], source_citations, claims: list[LegalClaim] }`

**Authority (`authority.py`)** — first-class graph, not RAG:
- `Authority{ id, citation, court, hierarchy_level: str, controlling_status: Literal["controlling","persuasive"], date: date, as_of_valid: bool, treatment_status: Literal["good","overruled","abrogated","distinguished"], holding_or_dicta: Literal["holding","dicta"], bears_on: list[str] }`  (`bears_on` = element ids / terms)
- `AuthorityGraph{ authorities: list[Authority], edges: list[...] }`
- `GraphStore` protocol with `baseline_for(target_ref: str, as_of: date) -> SourceSpan | None` → the controlling, good-treatment, as-of-valid **holding** bearing on the target, else `None`.

**Calculus (`calculus.py`)** — the spine:
- `PrimitiveOp` enum, **exactly these 14**: `MERGE, SPLIT, INTRODUCE, REPEAL, RELOCATE, RELATE_OFFENSE, CANONICALIZE_DEFINITION, DEFINE_TERM, SUBSTITUTE_TERM, NORMALIZE_ELEMENTS, ASSIGN_MENS_REA, FACTOR_EXCEPTION, REGRADE, ELEVATE_GENERAL_RULE, RESOLVE_CROSS_REFERENCE`.
- `Operation{ id, primitive: PrimitiveOp, operands: list[str], inverse: PrimitiveOp | None, scope: Literal["special_part","general_part"] = "special_part", relation: Literal["aggravated_form_of","shares_term","merges_with"] | None = None, diagnostics_triggering: list[str], normative_load: Literal["low","med","high"] }`
  - `relation` is set **iff** `primitive == RELATE_OFFENSE`; validate this.
  - `RELATE_OFFENSE` operands are two offense ids that **both survive** (distinct from `MERGE`, which collapses to one).
  - `scope` is meaningful for `INTRODUCE` / `ELEVATE_GENERAL_RULE` / `RELOCATE`.
- `EffectClass = Literal["codify","clarify","fill_gap","change","unresolved"]`
- `Diagnostic{ kind: str, target_ids: list[str], rationale: str, source_span_ids: list[str] }`
- `decompose(composite: str) -> list[PrimitiveOp]` encoding: `consolidation=[MERGE,CANONICALIZE_DEFINITION,RESOLVE_CROSS_REFERENCE]`, `codify_common_law=[INTRODUCE,ASSIGN_MENS_REA,DEFINE_TERM]`, `modernize=[SUBSTITUTE_TERM]`. Assert in tests that `clarification` is **not** a primitive and `RELATE_OFFENSE` is **not** decomposable.

**Review (`review.py`)**:
- `Finding{ id, provision: str, as_built_ref, intended_ref, operation_ids: list[str], effect_class: EffectClass, rationale, baseline: SourceSpan | None, normative_kind: list[Literal["policy_choice","penalty_value_judgment","constitutional_risk","doctrinal_ambiguity","institutional_discretion"]] = [], disposition_state: Literal["auto_ok","needs_review","reviewer_accepted","reviewer_rejected","reviewer_modified"] = "needs_review", confidence: float, verifier_records: list[str], status: Literal["draft","final"] = "draft" }`
- `ReviewDisposition{ finding_id, state, reviewer_id: str | None, timestamp: datetime | None, rationale: str | None }`

---

## 6. Definitions / refinements that affect modeling

- **SUBSTITUTE_TERM is strictly meaning-preserving.** A term swap that changes scope is `DEFINE_TERM` with `change` effect — not `SUBSTITUTE_TERM`. Encode this distinction in `diagnostics.py`/`operations.py` and test it.
- **General-Part scope.** Building the culpability-distribution rule, causation, the merger provision, or the penalty-class scheme is `INTRODUCE`/`ELEVATE_GENERAL_RULE` with `scope="general_part"`.
- **The four layers stay separate modules:** `diagnostics.py` (detect→trigger), `operations.py` (the Operation records + M0 check), `classify.py` (label effect vs. baseline), `invariants.py` (validate). Do not collapse them.

---

## 7. CLI (`cli.py`, Typer)

- `statutedistill validate-fixtures DIR` — load + schema-validate a fixture dir; non-zero exit on any violation.
- `statutedistill run-fixture DIR --out OUTDIR` — distill → align → diagnose → operations (+ M0 composition check) → classify → verify → write JSON outputs.
- `statutedistill render-package OUTDIR` — write `package.md` from the JSON outputs.
- `statutedistill verify OUTDIR` — recompute verifier statuses and print the final-status blocker summary.
- `statutedistill eval-fixture DIR` — compare produced findings to `gold_findings.json`; print agreement on operation set + effect class (deterministic; no baselines/LLM in slice one).

---

## 8. Theft fixture (openly placeholder)

Author `data/fixtures/dc/theft/` from the PRD §16 illustrative slice only. **Mark everything as placeholder; do not present fixture citations as authoritative unless real source text is present.** Contents:
- `sources.json` — labeled `SourceSpan`s (clearly fixture/placeholder).
- `authority_graph.json` — ≥1 controlling, good-treatment holding bearing on the intent element (so `classify` can label it `codify`/`clarify`).
- `as_built.json` — theft: means-based conduct, implicit mens rea, the ambiguous "without authority or right" element, value gradation.
- `intended.json` — RCC-style normalized theft: typed elements, explicit mens rea per element, value gradation with strict liability on value.
- `gold_findings.json` — exactly two findings:
  1. `DEFINE_TERM` ("without authority or right" → defined consent term) → `clarify`, `normative_kind=[doctrinal_ambiguity]`, `needs_review`.
  2. `MERGE` (fold false-pretense conduct into fraud) → `change`, `normative_kind=[policy_choice]`, `needs_review`.

Authoring fixtures is a **checkpoint (§14)**: produce the draft, leave `TODO(human): confirm placeholder labels`, proceed using the draft.

For the RELATE-OFFENSE M0 case, add a minimal `data/fixtures/dc/_calculus/` stub with a robbery and a theft-from-a-person offense and one expected `RELATE_OFFENSE(aggravated_form_of)` operation — used only by `test_calculus_theft.py` to exercise the 14th primitive deterministically.

---

## 9. Render package

`outputs/theft/` → `as_built.json`, `intended.json`, `findings.json`, `verification.json`, `review_queue.json`, `package.md`.

`package.md` must contain, in order: snapshot dates · offense summary · as-built spec · intended spec · authority-graph summary · **findings table** (provision, primitive, effect_class, normative_kind, disposition) · **claim-verification table** · **normative review queue** · **final-status blocker summary** (the explicit list of what is preventing `final`: open normative items, unverified/contradicted claims, unresolved effect classes).

---

## 10. M0 calculus validation (belongs in slice one — it is pure, deterministic composition)

In `operations.py`, implement `validate_composition(findings) -> list[Residual]`: every change in a fixture's gold findings must be a single primitive or a known `decompose()` composite; anything else is a residual. The CLI `run-fixture` runs this and fails on a non-empty residual. The robbery↔theft stub must validate as a single `RELATE_OFFENSE` (proving the 14th primitive is exercised and not silently absorbed into MERGE).

---

## 11. Tests (must pass)

Beyond unit coverage, these four behavioral tests are required:
1. A `LegalClaim` with empty `source_span_ids` **fails verification** (and blocks `final`).
2. A `Finding` with a `normative_kind` and unresolved disposition **blocks `final` status**.
3. The two theft findings **render into `package.md`** (and appear in the findings table + review queue).
4. `effect_class` is **not** the same type/value space as `Operation.primitive` (conflation is a type error / explicit assertion).
Plus: a finding whose target has **no authority baseline** yields `effect_class="unresolved"` (never a guessed class); and the robbery↔theft stub composes to a single `RELATE_OFFENSE`.

---

## 12. Build order (each ends green on `make check`)

- **T0 Scaffold** — repo, `pyproject.toml`, `Makefile`, Typer skeleton, empty CI-less `make check`.
- **T1 Models** — §5 models + `SnapshotDates` enforcement + exported `schemas/canonical.schema.json`.
- **T-CALCULUS** — `PrimitiveOp` (14), `Operation` (with `relation`/`scope` validation), `decompose()`, `validate_composition()`. *Tests:* closed enum; `relation` iff RELATE_OFFENSE; clarification-not-a-primitive; RELATE_OFFENSE-not-decomposable.
- **T2 Invariants** — `invariants.py` + `can_finalize()`; `tests/test_invariants.py` (the §2 spine incl. effect-class-needs-baseline, normative gate, verification gate).
- **T3 Fixtures** — theft fixture + `_calculus` stub (§8); `fixture_loader.py`; `validate-fixtures` CLI. Checkpoint.
- **T4 Pipeline** — `distill`/`align`/`diagnostics`/`operations`/`classify`/`verify`; `run-fixture` CLI (runs M0). *DoD:* theft produces two findings matching gold operation+effect; residual empty; stub composes to RELATE_OFFENSE.
- **T5 Render** — `render.py`; `render-package` CLI; `package.md` with blocker summary. *DoD:* test #3.
- **T6 Verify/Review** — `verify` CLI; disposition state machine; final-status gates. *DoD:* tests #1, #2.
- **T7 Eval** — `eval-fixture` CLI: deterministic agreement on operation set + effect class vs gold.
- **T8 README + next steps** — write the §13 roadmap.

---

## 13. README "next steps" (write at T8; do NOT build now)

1. Replace placeholder theft fixture with real CCRC / D.C. Code source text (public domain; bulk-download the DC Code XML, do not scrape).
2. Add a second offense fixture (robbery) that fully exercises `RELATE_OFFENSE`.
3. Add authority-treatment ingestion (controlling/treatment/as-of validity) — the real authority graph.
4. **Introduce LLM-based distillation/classification behind the proven `distill`/`diagnose`/`classify` interfaces** — temperature 0, structured output, every legal claim carrying a `SourceSpan`; this is the step that makes the product probabilistic, and it is gated by everything slice one proved.
5. Add the Allium renderer/validator as a view over the canonical schema (pin the version).
6. Add the expert gold-label evaluation harness with baselines (plain LLM, RAG-only, human review) and precision/recall.

**Guardrails that are dormant in a fixtures-only slice but load-bearing the moment ingestion lands:** source rights (no Model Penal Code / ALI / licensed-citator ingestion); snapshot rule (distill the as-built spec from `before_as_of`, never the current code); retrieval-only authority (no model-parametric legal claims). State these in the README so they are not forgotten.

---

## 14. Checkpoints — stop, write `TODO(human)`, leave a draft

1. Authoring/confirming fixture (placeholder) labels (T3).
2. A residual the calculus cannot express as a primitive or known composite (M0) — propose, do not add.
3. Any normative-review disposition (never resolve `needs_review` yourself).
4. A conflict between this file and the PRD.
5. Anything that would require non-public/licensed text or network access.

---

**Begin at T0. Slice one is deterministic and fixtures-first. Do not introduce an LLM, network, scraping, or Allium until the README roadmap step that names it.**
