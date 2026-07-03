# B4 report — applying the B3 review dispositions and closing the known defects

**Authority:** `../REVIEW_PACKET_B3.md` (M. Hsu, 2026-07-02 — all recommendations accepted).
**Scope:** write the dispositions into the review state, fix the two known defect classes
(mispins; instrument-graph coverage), re-run classification, and re-render the packages.
Everything here is deterministic and offline (`make check` runs from the committed cache; no
API key). Nothing is finalized — reviewer acceptances are recorded on a draft-direction basis
(NG2); no finding reaches `final`.

---

## B4-T0 — dispositions written back (reviewer `mhsu`)

`outputs/b4/dispositions.json` — 28 `ReviewDisposition` records:

- **f-D1…f-D9** — `reviewer_accepted` **as draft roadmap direction** (not policy adoption;
  feasibility ranking D4 first, D5 second, D3 hardest, carried in the rationale).
- **b:AUD-07** — `reviewer_modified` (the oversight-not-certify resolution, applied in T1).
- **The 18 dx-\* diagnostics** — `reviewer_accepted` as investigation items (seed the
  DEFINE_TERM / ASSIGN_DUTY_PARAMETER worklists).

Regenerated blocker summary: **0 findings final, 0 silently finalized.** A `reviewer_accepted`
on a draft-direction basis records review state; `status` stays `draft` until an operative
reform instrument exists.

## B4-T1 — the AUD-07 conflict cleared

`outputs/b4/aud07_resolution.json`. The B3 distiller read SOX 302 / 17 CFR 240.13a-14 as
`verb_standard: certify` while the B2 retag had moved the actor to the CEO/CFO — a flagged
`verb_retag_conflict`. Resolution (Packet Part 2): the certification duty is split onto a
**management actor record** (`certify`, CEO/CFO), and the **board-side residual** is
audit-committee *oversight of the certification process* — `review_and_challenge`, grounded in
SOX 301 / Part 363, never `certify` as a board verb. The flagged conflict is cleared
(`verb_retag_conflicts: 0`). Regression test added: a board-level `certify` verb on a row whose
actor is management triggers the verb-vs-actor cross-check.

## B4-T2 — the ten mispinned rows re-pinned

`outputs/b4/repins.json`. Targeted offline retrieval fixed each B3 source-mismatch row to the
location *within its already-cited instrument* (allowlist unchanged) whose verbatim text
supports the duty. **All 10 quotes verbatim-verified against the cited cache; 0 escalated to
the F2/F4 candidate queue.**

| row | corrected pin | old pin was |
|---|---|---|
| b:AUD-08 | 12 CFR Part 30 App. D II.C (CAE appointment/removal/comp + charter) | App. D concentration-risk para |
| b:CAP-02 | 12 CFR 225.8(e)(3) (review robustness, before submission) | 225.8(d) definitions |
| s:CAP-09 | 12 CFR 225.8(e)(3) (mirror of b:CAP-02) | 225.8(d) definitions |
| b:RGC-05 | 12 CFR 252.33(a)(3)(ii) (independent chair) | 252.33(a)(1) general mandate |
| s:BCG-03 | OCC Handbook — credit-committee description | fiduciary-audit-committee para |
| s:CAP-07 | SR 15-18 att III.A.1 (board record of meetings) | post-stress escalation para |
| s:GOV-03 | SR 21-3 att Attribute 1 (expansion into new business/jurisdiction) | nominee-process passage |
| s:GOV-04 | SR 21-3 att Attribute 2 (timely, accurate information) | nominee-process passage |
| s:GOV-08 | SR 21-3 att Attribute 3 (CEO performance objectives) | nominee-process passage |
| s:GOV-12 | SR 21-3 att Attribute 4 (audit-committee oversight of internal audit) | nominee-process passage |

Seven pins are fuzzy anchor-matched (`anchor_matched: true`). `s:GOV-12` carries a
partial-support note: SR 21-3 (Audit) supports the audit-committee/internal-audit oversight and
remediation-timeliness core; the duty's "meets directly with the CAE / budget & staffing"
sub-elements are more fully grounded in App. D II.C / SR 13-1.

**Checkpoint (open):** the LLM re-distill of the ten corrected excerpts needs live calls (then
cache). With no `ANTHROPIC_API_KEY` this pass, the corrected pins are the deliverable and the
re-distill is left as `TODO(human): export ANTHROPIC_API_KEY, then b3-distill --live` over the
ten rows.

## B4-T3 — two duplication families, first-class

The B3 `duplicate_duty` diagnostic splits into two non-overlapping official kinds (Packet Part
4). The LLM's within-cluster duplicates re-key to **`restatement`** (same text repeated;
MERGE / RESOLVE_CROSS_REFERENCE-shaped); the B0 hand-labelled cross-layer/cross-entity pairs
are materialized as **`mirror_pair`** diagnostics (parallel obligations; RELATE_OBLIGATION /
DEEM-shaped; reform lever DEEM_SATISFIED / reliance).

| family | count | shape | reform lever |
|---|---|---|---|
| `mirror_pair` | 11 | cross-layer / cross-entity (BHC↔IDI, rule↔guideline) | DEEM_SATISFIED / reliance |
| `restatement` | 8 | same obligation restated across rows | MERGE / RESOLVE_CROSS_REFERENCE |

Zero overlap between the families (as the B0-vs-LLM divergence already showed). Packages render
the two families in separate tables; `findings.json` carries `finding_kind` and a
`duplication_families` summary.

## B4-T4 — concept-node graph extension (`data/graph/us-gsib_v2.json`)

Nine typed `concept_ref` nodes for the operand-level concepts the levers cite — each grounded
to its underlying instrument node(s) with **verbatim span evidence verified against the source
cache** (no free-floating concepts): `SOX-404b-attestation` (15 U.S.C. 7262), `Part363-ICFR-
assessment` (12 CFR Part 363), `AppD-committee-expectations` / `AppD-bank-committee-expectations`
(App. D), `consolidated-committee-standard` (Reg YY 252.33), the D3 committee-requirements
composite (Rule 10A-3 + SOX 404(b)), and the D6 / D7 / D8 targets — plus the SR 12-17 grounding
node the B2 graph lacked. **`baseline_for` now answers for all 11 B0 concept operands.**

## B4-T5 — re-classification and re-render

Two mechanical changes let the classifier reach the levers without guessing: (1) **graph-aware
target selection** anchors each consolidation finding on the first operation ref the graph can
baseline (inventory row or concept node); (2) the **dominant-effect classifier** takes a
finding's most severe op effect, so a multi-op lever like D4 (DEEM_SATISFIED + an unanchored
ASSIGN_DUTY_PARAMETER) resolves to `change` instead of short-circuiting on the parameter rule.

The five formerly-`unresolved` levers now classify — **zero `unresolved` among f-D1…f-D9:**

| lever | B4 effect | B0 gold | agree |
|---|---|---|---|
| D1 | change | change | ✓ |
| D2 | change | change | ✓ |
| D3 | change | change | ✓ |
| D4 | change | change | ✓ |
| D5 | clarify | clarify | ✓ |
| D6 | change | change | ✓ |
| D7 | codify | codify | ✓ |
| D8 | change | change | ✓ |
| D9 | **fill_gap** | codify | ✗ (characterized) |

**B0 effect-class agreement: 8/9, up from 3/9 in B3.** The sole disagreement is D9: the
mechanical classifier reads `INTRODUCE` of a new General-Part governance section as `fill_gap`
(most severe over the `ELEVATE_GENERAL_RULE` / `RESOLVE_CROSS_REFERENCE` codifies); B0's
conditional label is `codify_if_mechanics_identical`. Recorded as a **characterized
disagreement — the B0 gold is not edited** (checkpoint discipline).

Packages re-rendered into `outputs/b4/<cluster>/package.md` (both duplication-family tables;
mirror pairs routed into the risk-governance package). `outputs/b4/eval_report.md` regenerated:
**hallucinated-citation rate 0.0 — release gate PASS.**

**Characterized limitation (not a blocker):** D7 classifies `codify` but its mechanical
disposition is `auto_ok`, whereas B0 expects `needs_review` for its cross-stratum operands. The
disposition rule reads cross-stratum from *resolved as-built operand forces*, which are empty
for concept operands, so the cross-stratum signal is not seen. Effect class (the B4-T5 target)
is correct; the disposition under-detection is recorded here for a future refinement that reads
strata through the concept groundings.

## Fresh checkpoints for the human

1. **LLM re-distill of the ten re-pinned rows** — blocked on `ANTHROPIC_API_KEY` (B4-T2).
2. **D9 effect-class disagreement** — mechanical `fill_gap` vs B0 `codify`; characterized, not
   reconciled (B4-T5).
3. **D7 disposition under-detection** — `auto_ok` vs B0's `needs_review`-on-cross-stratum;
   noted for a future concept-grounding-aware disposition rule.

## What B4 leaves in place

All B3 dispositions persisted under `mhsu`; AUD-07 coherent; the ten pins fixed (or, for the
re-distill, checkpointed with evidence); both duplication families first-class; every lever
effect-classified with the extended graph; packages and eval regenerated; `make check` green
offline.

**Not started (own files when M. Hsu calls for them):** (i) scale to the remaining ~27
clusters; (ii) the RBI Master-Directions rediscovery benchmark.
