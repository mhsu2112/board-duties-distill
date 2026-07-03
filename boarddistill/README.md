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

## B3 — the LLM layer (distill · intended · diagnose → packages → eval)

The first slice to permit LLM calls, behind the interfaces B0–B2 proved. Every LLM output
lands as reviewable `draft`, anchored to the cache; the deterministic classifier runs after
every proposal. The harness (`distillcore/llm.py`) pins `claude-opus-4-8`, validates
structured output against the Pydantic schemas (reject-retry once, then hard-fail), and
**caches every call under `data/llm_cache/` keyed by `(model, prompt_sha256)`** — replay is
the default, so `make check` runs the whole layer offline with no key. Live calls need
`--live` + `ANTHROPIC_API_KEY`; absent the key the harness stops with `TODO(human)` and does
not improvise another provider.

- **T0 dispositions.** 22 B2 residuals accepted as documented; `s:CAP-11` reclassified as a
  supersession note (71 duty rows); SR 95-51 resolved as *amended* from the Fed page.
- **T2 distill.** The 50 verified duties refined against their pinned excerpts — **50/50
  anchor-clean, 0 hallucinated citations.** Surfaced 1 verb-vs-retag conflict (`b:AUD-07`) and
  **10 source-mismatch rows** (verified-but-mispinned spans).
- **T3 intended.** The 9 B0 levers as illustrative (NG2) consolidated specs + **33 operations**
  scaffolded verbatim from `b0_decompositions.json` (`ASSIGN_DUTY_STANDARD` → `ASSIGN_DUTY_PARAMETER`).
- **T4 diagnose + classify.** 9 consolidation findings (mechanical effect classes) + 18 LLM
  diagnostics; the B0-vs-LLM duplicate divergence recorded both directions (0 agreed).
- **T5 packages.** Three per-cluster `package.md` — every finding `draft`, **zero final**
  (the intended blocked-pending-review end-state).
- **T6 eval.** B0 effect-class agreement 3/9 (disagreements characterized, not reconciled);
  distill stable across samples; **hallucinated-citation rate 0.0 — release gate PASS**;
  baseline comparison vs the raw inventory.
- **T7** — `outputs/b3/B3_report.md` is the human review queue (the main artifact).

```bash
uv run boarddistill b3-apply           # T0 dispositions
uv run boarddistill b3-distill         # T2 (add --live to populate the cache)
uv run boarddistill b3-intended        # T3
uv run boarddistill b3-diagnose        # T4
uv run boarddistill b3-package         # T5 -> outputs/b3/<cluster>/package.md
uv run boarddistill b3-eval            # T6 -> outputs/b3/eval_report.md (--live for stability)
```

The next event is the **human review pass over the three packages** — see
`outputs/b3/B3_report.md`.

## B4 — apply the review dispositions and close the known defects

The first pass *after* human review. `../REVIEW_PACKET_B3.md` (M. Hsu, 2026-07-02) accepted all
recommendations; B4 writes them into the review state and fixes the two known defect classes.
Deterministic and offline — `make check` runs from cache, no key. Nothing finalized (NG2).

- **T0 dispositions.** f-D1…f-D9 `reviewer_accepted` *as draft roadmap direction*, b:AUD-07
  `reviewer_modified`, the 18 diagnostics `reviewer_accepted` — 28 records under `mhsu`;
  **0 findings final.**
- **T1 AUD-07.** Split into a management `certify` record (CEO/CFO) and a board-side
  `review_and_challenge` oversight residual; the verb-vs-retag conflict cleared.
- **T2 re-pin.** The 10 source-mismatch rows re-pinned to the supporting location in the cited
  instrument — **10/10 quotes cache-verified, 0 F2/F4 escalations.** The live LLM re-distill is
  checkpointed (needs `ANTHROPIC_API_KEY`).
- **T3 duplication split.** `duplicate_duty` → `mirror_pair` (11, cross-layer/entity) +
  `restatement` (8, same-text); packages report the two families in separate tables.
- **T4 concept graph** (`data/graph/us-gsib_v2.json`). 9 grounded `concept_ref` nodes with
  cache-verified span evidence; `baseline_for` answers for all 11 B0 concept operands.
- **T5 re-classify + re-render.** Graph-aware target selection + a dominant-effect classifier
  resolve the five formerly-`unresolved` levers — **zero `unresolved` among f-D1…f-D9**
  (D3/D4/D6/D8 change, D7 codify). **B0 effect-class agreement 3/9 → 8/9**; the one
  disagreement (D9 `fill_gap` vs B0 `codify`) is characterized, not reconciled. Zero
  hallucinated citations.
- **T6** — `outputs/b4/B4_report.md`.

```bash
uv run boarddistill b4-apply           # T0 dispositions -> outputs/b4/dispositions.json
uv run boarddistill b4-aud07           # T1 -> outputs/b4/as_built_distilled.json (+ resolution)
uv run boarddistill b4-repin           # T2 -> outputs/b4/repins.json
uv run boarddistill b4-graph           # T4 -> data/graph/us-gsib_v2.json
uv run boarddistill b3-diagnose --graph data/graph/us-gsib_v2.json \
    --distilled outputs/b4/as_built_distilled.json --out outputs/b4   # T5 re-classify
uv run boarddistill b3-package --findings outputs/b4/findings.json \
    --distilled outputs/b4/as_built_distilled.json \
    --graph data/graph/us-gsib_v2.json --out outputs/b4               # T5 re-render
uv run boarddistill b3-eval --findings outputs/b4/findings.json \
    --distilled outputs/b4/as_built_distilled.json --out outputs/b4   # T5 eval
```

After B4, two arcs remained (their own files when called for): scale to the remaining ~27
clusters, and the RBI Master-Directions rediscovery benchmark.

## B5 — scale-out to the full corpus (the remaining ~155 rows → the product)

Runs the proven per-cluster pipeline over the ~155 non-MVP duty rows and rolls everything up
into a corpus-wide product. No new methods, no new primitives, no scope growth — novelty is a
checkpoint, not a feature.

- **T0 carry-forwards** — live re-distill of the ten B4 re-pins; the D7 disposition now reads
  cross-stratum *through concept groundings* (`needs_review`); retry of three B2 residuals
  (`s:GOV-15` resolves via a new SR-letter-body anchor fallback; two re-documented).
- **T1 wave plan** — the 155 non-MVP rows partitioned into six domain waves
  (`outputs/b5/waves.json`).
- **T2 per-wave verification** — every row evidenced against primary sources; **142/227
  verified, 0 contradicted.** Two resolver fixes: an SR-letter `/boarddocs/` URL fallback, and
  CFR section-*range* parsing (`252.62-252.63`) that had produced three *false* contradictions.
  Corpus instrument graph `data/graph/us-gsib_v3.json` (49 instruments, 0 unknown-agency).
- **T3 distill + diagnose + classify** — 91 wave rows distilled 100% anchor-clean; per-cluster
  diagnostics (both duplication families) with 0-op ⇒ `unresolved` + `needs_review`. Two
  unanchored diagnostics were caught and **dropped** (never passed through).
- **T4 lever decomposition** — the 22 non-MVP reform levers decomposed (LLM proposes,
  `validate_composition()` enforces the 16-enum + 4 composites). **Closure result:** 8 clean,
  8 documented non-targets, **6 residual checkpoints** (propose, never add). 19 statutory-floor
  candidates proposed (human-owned file).
- **T5 packages** — 22 per-cluster `outputs/b5/<wave>/<cluster>/package.md`, full §9, nothing
  final.
- **T6 corpus roll-up** — `outputs/b5/corpus/{master_crosswalk,reform_roadmap_v2,corpus_stats}.md`
  and the consolidated `../REVIEW_PACKET_B5.md`. Corpus-wide: **79% of distilled duties state no
  board-action standard.**
- **T7 eval** — `outputs/b5/B5_report.md`: funnel, closure, **citation-integrity 0.0 (PASS)**,
  stability spot-check (3/3 verb + cadence agreement on one wave), budget (~180 calls), full
  checkpoint list.

```bash
uv run python cli.py b5-redistill --live        # T0(a)
uv run python cli.py b5-retry-residuals         # T0(c)
uv run python cli.py b5-waves                    # T1
uv run python cli.py b5-verify --wave all        # T2 (network; --offline to replay)
uv run python cli.py b5-graph                    # T2 corpus graph v3
uv run python cli.py b5-distill --wave all --live # T3 distill
uv run python cli.py b5-diagnose --wave all      # T3 diagnose (replay)
uv run python cli.py b5-decompose --live         # T4
uv run python cli.py b5-package --wave all       # T5
uv run python cli.py b5-corpus                   # T6
uv run python cli.py b5-eval                     # T7
```

After B5 and the human review pass, one arc remains: the RBI Master-Directions rediscovery
benchmark — its own file, on M. Hsu's word. Not started.

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
5. Per-cluster consolidation packages — **done (B3/B4 for the MVP clusters; B5 for the
   remaining ~27).** The corpus-wide product (master crosswalk, reform roadmap v2, stats,
   `REVIEW_PACKET_B5`) is built.
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
