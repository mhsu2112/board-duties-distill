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

## B1 — claim verification (the first retrieval step)

**What.** Full-coverage citation verification of the 72 MVP-cluster board-duty rows
(3 MVP + 2 entangled clusters) against primary sources. Each row's citation is resolved,
its verbatim provision text pinned as a `SourceSpan`, and currency checked. Verification
never edits the inventory or the drafts — a bad citation is a finding for a human.

**From where (allowlisted primary sources only).** eCFR versioner XML (CFR sections &
appendices) · govinfo HTML granules (U.S. Code) · federalreserve.gov (SR letters). The
allowlist is enforced in code (`adapters/retrieval.py`); a non-allowlisted / paywalled /
CSI source is a checkpoint, never fetched.

**When / reproducibility.** Verified 2026-07-02 at snapshot `2026-06-30` (eCFR) / U.S. Code
2024 edition. Every document is cached under `data/sources/<source_id>/` with a
`manifest.json` (url, retrieved_at, sha256). The whole run replays offline, byte-identical,
from the committed cache — `make check` stays offline (live tests are `pytest -m live`,
excluded by default).

```bash
uv run boarddistill b1-targets                 # select the 72 target rows
uv run boarddistill verify-live --offline      # replay verification from cache
uv run boarddistill b1-report                  # -> outputs/b1/B1_report.md + review_queue.json
```

**Result: 21 verified · 51 unverified · 0 contradicted.** All 21 verified are binding-rule
cites (CFR sections, U.S.C., one SR letter) with pinned verbatim text. The 51 unverified are
the honest finding: most **supervisory-layer duties cite guidance-document locations**
(SR-letter attachments, exam-manual components, local line numbers), not addressable primary
law — a sludge signal in itself (the Risk-governance strategy cluster is 0/21 verified).

**Review queue (`outputs/b1/review_queue.json`) — TODO(human):** every non-verified row,
plus F2 flags where a citation verifies but the provision text does not name the stated
board actor (e.g. `b:AUD-07` — a board SOX-302 duty citing the *officer*-level
`17 CFR 240.13a-14`; SOX 404 statute rows), plus fidelity caveats (U.S.C. quotes are
section-level; SR attribute text lives in attachments, so the cover letter is pinned).

**Open question for the human — re-verification cadence.** Verified law drifts (amendments,
rescissions, new SR letters). B1 pins a snapshot; it does not subscribe to changes. Decide a
re-verification cadence (e.g. quarterly re-run + diff against the cached sha256s) before this
is relied on as standing L1 input.

## B2 — dispositions, expanded resolution, instrument graph

Applied the human B1 dispositions and built the resolvers for the harder citation classes,
then re-verified.

- **Dispositions.** The 21 verified rows are `reviewer_accepted`; the 6 support-flagged rows
  are `reviewer_modified` via an **actor retag** — corrected to the party the verified text
  actually binds (management / CEO-CFO / the company / the external auditor), with the
  board's indirect oversight annotated and the B1 quote as evidence. `s:CAP-11` carries a
  `TODO(human)`. Persisted in `outputs/b2/dispositions.json` + `retags.json`; duty text is
  never edited.
- **Expanded resolvers.** CFR **appendices** (terse "App. D" → 12 CFR Part 30), **SR-letter
  attachment PDFs** and **OCC/FDIC manuals** — the latter two via fuzzy **anchor matching**
  (the duty's paraphrase located in the source; high-confidence pins the span, borderline
  0.40–0.60 is recorded as a candidate for human review, never auto-verified).
- **Result: 21 → 50 verified / 72, 0 contradicted.** The Risk-governance strategy cluster
  went 0 → 11. The 22 residuals are mostly borderline anchor candidates, each with a reason
  (`outputs/b2/review_queue.json`, `B2_report.md`).
- **Instrument graph v1** (`data/graph/us-gsib_v1.json`): one node per instrument the 72
  rows cite (statute / regulation / enforceable_guideline / guidance / manual) with agency,
  effective date, and treatment status; `baseline_for` answers for all 50 verified duties.
  SR 09-4 is recorded `superseded` (SR 15-18 fn.5); SR 95-51 treatment is flagged
  `TODO(human)` rather than decided.

```bash
uv run boarddistill b2-accept          # reviewer_accepted for the verified rows
uv run boarddistill b2-retag           # actor retag for the approved 6
uv run boarddistill verify-live --offline --out outputs/b2   # re-verify from cache
uv run boarddistill b2-graph           # build data/graph/us-gsib_v1.json
uv run boarddistill b2-report          # outputs/b2/B2_report.md
```

## Next steps (roadmap — NOT built in slice one)

1. **Human confirmation** of the fixture placeholder labels and the T8 draft column
   mappings (both are §14.1 checkpoint outputs marked `TODO(human)`).
2. ~~**Full-coverage claim verification** of the MVP-cluster rows (B1 exit criterion).~~
   **Done (B1)** — see the B1 section above. Remaining: extend to the other ~155 rows;
   paragraph-precise U.S.C. and SR-attachment retrieval; the re-verification cadence.
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
