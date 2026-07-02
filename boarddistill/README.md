# BoardDistill (Lex-Balanus slice one)

The first **deterministic vertical slice** of the shared policy-distillation engine, with
the **US-GSIB banking profile (Lex-Balanus)** as the first fully-exercised profile.

Slice one is **deterministic and fixtures-first**: same inputs → same outputs, no LLM, no
network, no scraping. It proves the architecture's spine — a profile-parameterized
canonical schema, a closed 16-primitive calculus, a code-enforced invariant suite, the
verification/review gates, and a rendered consolidation package — on hand-authored
fixtures. See `AGENTS.md` for the build contract and `specs/` for the PRDs.

```
profile-parameterized schema → fixture corpus → instrument graph
   → as-built / intended DutySpecs → diagnostics → calculus operations
   → findings (+ effect class) → invariants → claim verification
   → review state → rendered consolidation package
```

## Quickstart

```bash
uv sync            # create the venv, install deps
make check         # ruff + mypy --strict + pytest  (the gate)
make schema        # re-export schemas/canonical.schema.json
```

## CLI

```bash
uv run boarddistill --help
uv run boarddistill validate-fixtures data/fixtures/us-gsib/icfr
uv run boarddistill run-fixture       data/fixtures/us-gsib/icfr --out outputs/run
uv run boarddistill render-package    outputs/run/icfr           # writes package.md
uv run boarddistill verify            outputs/run/icfr           # blocker summary
uv run boarddistill eval-fixture      data/fixtures/us-gsib/icfr # agreement vs gold
uv run boarddistill import-inventory  ../Synthesis/gsib-board_duties-combined_inventory.xlsx --out outputs/import
```

## Architecture

- `distillcore/` — profile-independent core: canonical models (`models/`), pipeline stages
  (`pipeline/`: distill · align · diagnostics · operations · classify · verify · render ·
  invariants), and the exported JSON Schema.
- `profiles/lex_balanus/` — the banking profile: enums (the 16-member `PrimitiveOp`),
  `DutySpec`/`InstrumentGraph`, invariants §2.9–2.12, the composite table, and the
  pipeline composition root (`pipeline.py`).
- `profiles/lex_allium/` — criminal profile **stub** (enums + loaders that raise), present
  so the criminal slice can land without core changes.
- `adapters/` — `fixture_loader` and the local, deterministic `inventory_xlsx` (T8).

The three fixtures — `icfr` (D4), `sr12-17` (D6), `board-effectiveness` (D7), plus the
`_calculus` mirror — reproduce their gold operation + effect class + disposition exactly,
with an empty residual and the mirror composing to `vertical_rationalization`.

## Next steps (roadmap — NOT built in slice one)

1. **Human confirmation** of the fixture placeholder labels and the T8 draft column
   mappings (both are §14.1 checkpoint outputs marked `TODO(human)`).
2. **Full-coverage claim verification** of the MVP-cluster rows (B1 exit criterion) —
   requires retrieval; design it behind the existing `verify` interface.
3. **Real instrument-graph ingestion**: eCFR / US Code parsing, guidance registries, and
   archival rescission reconstruction (`rescinded_informal`).
4. **LLM-based distillation / diagnostics / classification** behind the interfaces this
   slice proved — temperature 0, structured output, every claim span-anchored. This is the
   step that makes the product probabilistic; it is gated by everything slice one proved.
5. **Scale to all ~30 clusters**; per-cluster consolidation packages (B4).
6. **RBI Master-Directions rediscovery benchmark** + baselines (the existing horserace
   reports in `Reports/` are the plain-LLM baselines).
7. **`lex_allium` profile build** per the engine `AGENTS.md` (proves the core is genuinely
   shared).
8. **PRA / FCA adapter scoping.**

## Dormant-but-load-bearing guardrails

These are true today and must survive into every later step:

- **CSI gap.** Public runs are *as-published*, not *as-enforced*; prefer `unresolved` over a
  guess. Confidential supervisory information never enters a public run.
- **Snapshot rule.** Distill at `inventory_as_of`, never against live law. Every `DutySpec`
  carries `SnapshotDates`; a spec without them fails validation.
- **Retrieval-only authority.** No parametric (model-memory) legal claims — every legal
  assertion points to ≥1 `SourceSpan`; an uncited claim is a bug.
- **Source rights.** Exchange listing standards and licensed databases are flagged;
  agency / eCFR text is public. Respect the distinction in any ingestion step.

## Checkpoints (human-owned; the agent drafts and flags, never resolves)

Fixture placeholder labels and T8 mappings; any residual the calculus cannot express as a
§5 primitive or known composite (propose, do not add); any normative-review disposition;
any `statutory_floor.json` edit; a conflict between `AGENTS.md` and a PRD; anything needing
network access, licensed text, or CSI.

> Resolved 2026-07-02 (was checkpoint §14.5): parent-doc prose counts corrected — the engine
> set is fifteen primitives; the banking set closes at **16** (the fifteen + `DEEM_SATISFIED`).
> The enum remains the ground truth.
