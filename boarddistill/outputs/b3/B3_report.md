# B3 — the LLM layer: report & human review queue

**For:** M. Hsu. **Scope:** the three MVP clusters (risk-governance framework/strategy ·
audit committee & independence · capital planning & stress testing). **State:** everything
below is `draft`/`needs_review` — this document *is* the review queue, not a set of
decisions. Consolidated/intended duty language is illustrative (NG2) and non-authoritative.
`make check` replays the entire layer offline from `data/llm_cache/`.

---

## 1. What the LLM layer added beyond the deterministic pipeline

Slice-one (MVP–B2) was fully deterministic: schema, the 16-primitive calculus, invariant
suite, allowlisted retrieval, 50/72 rows verified against pinned primary-source excerpts, the
instrument graph. B3 adds three LLM stages, each behind the interfaces that slice proved, each
output landing as reviewable draft, every claim anchored to the cache:

| Stage | What the LLM does | What stays in code |
|---|---|---|
| **Distill** (T2) | Refines each of the 50 verified duties against its pinned excerpt — precise verb/object/cadence, definitions, intra-duty elements | Anchor verification (every quote a substring of the excerpt); the verb-vs-retag cross-check |
| **Intended** (T3) | Drafts the illustrative (NG2) consolidated duty language for each of the 9 B0 levers, citing operands | Operation scaffolding from `b0_decompositions.json` (operands verbatim); operand resolution report |
| **Diagnose** (T4) | Proposes diagnostics per cluster (duplicate duty, rule-guidance restatement, undefined term, actor ambiguity) with span evidence; proposes normative kinds | Effect classification (`classify_finding` — baseline_for diffs, per-se force-conversion, no-baseline ⇒ unresolved); disposition defaults |

The LLM never sets an effect class, never resolves a normative flag, never finalizes. The
deterministic classifier runs *after* every LLM proposal. **68 LLM calls total**, all cached.

The value-add over the raw synthesis inventory is concrete (T6-d): the raw audit-cluster rows
carry placeholder citations and no field-level evidence; the distillation layer produced **209
verbatim, offset-checkable anchors at a 0.0 hallucinated-citation rate** (T6-c release gate:
**PASS**).

---

## 2. The human review queue (the point of this phase)

The three per-cluster packages are in `outputs/b3/<cluster>/package.md` (risk-governance,
audit-committee, capital-planning). Each carries the §9 sections and a blocker summary. The
items below are what most need a human eye, ranked by how much judgment they need.

### 2.1 Verb-vs-retag conflict — 1 (reconcile actor vs. verb)

- **b:AUD-07**: the distilled `verb_standard` is `certify`, but B2 retagged the actor to **CEO
  and CFO** (SOX §302/§906 certification is management's, not the board's). The `certify` verb
  re-asserts board performance on a duty moved off the board. *Flagged, not overwritten.*
  **TODO(human):** confirm this row is board oversight of management's certification, not a
  board certification duty.

### 2.2 Source-mismatch rows — 10 (the pinned excerpt does not support the duty)

The LLM returned an empty object and `unresolved` rather than guessing on 10 verified rows
whose B2-pinned excerpt does not actually support the duty's object:

`b:AUD-08, b:CAP-02, b:RGC-05, s:BCG-03, s:CAP-07, s:CAP-09, s:GOV-03, s:GOV-04, s:GOV-08, s:GOV-12`

Example: **b:AUD-08** (audit committee approves the chief audit executive's appointment) is
pinned to an OCC *Concentration Risk Management* paragraph. **TODO(human):** these look like
mis-assigned spans from B1/B2 retrieval — re-pin or re-scope the citation. This is arguably the
most useful signal the LLM layer surfaced: it caught verified-but-mispinned rows.

### 2.3 Duplicate-detection divergence — B0 vs LLM (0 agreed)

The LLM's duplicate diagnostics and the B0 hand-labelled duplicates (RELATE_OBLIGATION /
DEEM_SATISFIED operand pairs) **do not overlap at all**: 11 B0-only pairs (the risk-governance
framework mirror pairs, `b:RGC-01..05`), 35 LLM-only pairs (same-provision restatements in the
audit and capital clusters, e.g. `b:AUD-01/02/03`, `b:CAP-02/03`). Both directions are findings
(§checkpoint). **TODO(human):** the two methods are detecting *different kinds* of duplication —
cross-layer framework mirrors vs. within-cluster restatements. Decide which the consolidation
should act on (likely both, differently).

### 2.4 Normative review queue — 26 findings in `needs_review`

9 consolidation findings + 18 diagnostics, 26 in review. Every `normative_kind` is a **proposal**
(policy_choice, interagency_coordination, statutory_constraint, …), none resolved. See each
package's "Normative review queue" section.

### 2.5 Distillation gaps (lower priority)

- **41/50** distilled duties have `verb_standard = none_specified` — most excerpts state an
  underlying requirement, not a board-action standard. A sludge signal in itself.
- **2/9** intended levers (D3, D5) the LLM under-cited operands in its drafting (the spec's
  `source_citations` are complete regardless; this is a drafting-quality flag only).

---

## 3. Agreement / disagreement vs the B0 gold (T6-a)

- **Operation set:** preserved verbatim from `b0_decompositions.json` — primitive-set agreement
  is by construction. One systematic transform: `ASSIGN_DUTY_STANDARD → ASSIGN_DUTY_PARAMETER`
  (B0 TODO-2, resolved 2026-07-02).
- **Effect class:** **3/9** agree (D1, D2 → `change`; D5 → `clarify`). The 6 disagreements are
  characterized, not reconciled:
  - D3, D4, D6, D7, D8: the mechanical classifier returns `unresolved` because no instrument-
    graph node bears on the concept-ref operands (no baseline ⇒ never guessed); B0 used domain
    judgment. **This is a graph-coverage gap, not a classifier error** — the concept-ref
    operands (`AppD-committee-expectations`, `SOX-404b-attestation`, …) have no node to diff
    against. Extending the instrument graph to cover them would let the classifier reach them.
  - D9: `fill_gap` (mechanical, INTRODUCE default) vs `codify` (B0).

The gold labels are never edited; disagreements are the finding.

## 4. Stability (T6-b)

3 live samples per stage on the audit cluster (cached): **distill** verb and cadence identical
across all 3 samples; **diagnose** Jaccard 0.5 (counts 8/9/7) with 6 stable core diagnostics and
a varying tail. Extraction of pinned fields is stable; open-ended diagnostic discovery is
moderately stable at its core and noisier at the margin.

## 5. Budget spent

**68 LLM calls**, all `claude-opus-4-8`, temperature not sent (Opus 4.8 rejects it; determinism
is the response cache), thinking disabled, structured output. ≈ **205k input / 39k output
tokens** across the four live passes (distill 50 · intended 9 · diagnose 3 · stability 6). Every
call is committed under `data/llm_cache/` keyed by `(model, prompt_sha256)`; `make check` and CI
replay them offline and byte-identically — no key needed after this pass.

## 6. Status

`make check` green from cache (183 tests). All B3 tasks (T0–T7) committed. The next event is the
**human review pass over the three packages** — this queue is built for exactly that. Scaling to
all clusters and the RBI benchmark are separate future files and are not started.
