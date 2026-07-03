# Consolidation package — Third-party risk management

> Wave: `w3-thirdparty-inccomp`. 
**Status: blocked pending human review.** Every finding is `draft`; none is `final`. The reform lever below is an illustrative (NG2) proposal, not an adopted instrument.

## Cluster summary

- distilled duties: 5 (verified: 5) · findings: 4 · final: 0 · in-review: 4


## As-built duties (distilled)

| duty_id | verb | object | cadence | force | anchor |
| --- | --- | --- | --- | --- | --- |
| s:TPR-01 | receive_report | Periodic reporting to the board regarding third-party relationships, including dependency on a single provider for multiple activities | none_specified | — | ok |
| s:TPR-02 | receive_report | Periodic reporting to the board on third-party relationships, including dependency on a single provider for multiple activities | none_specified | — | ok |
| s:TPR-03 | none_specified | Periodic reporting to the board regarding third-party relationships | none_specified | — | ok |
| s:TPR-04 | receive_report | Periodic reporting to the board, including dependency on a single provider for multiple activities | none_specified | — | ok |
| s:TPR-06 | receive_report | Periodic reporting to the board, including dependency on a single provider for multiple activities | none_specified | — | ok |


## Intended — reform lever (illustrative, NG2)

| lever | status | composition | primitives | effect | instrument_required |
| --- | --- | --- | --- | --- | --- |
| Quantitative 'critical activity' threshold for board attention; management approval + aggregate reporting otherwise. | residual | residual | — | unresolved | interagency_statement |

> **Residual checkpoint** — the 16-primitive set did not cleanly express this lever in the automated pass: The lever combines a quantitative 'critical activity' threshold governing WHEN board attention is triggered (FACTOR_EXCEPTION / ASSIGN_DUTY_PARAMETER cadence) with a re-routing of non-critical activities to management approval plus aggregate board reporting (an ASSIGN_DUTY_PARAMETER on who-approves + reporting cadence). This threshold-plus-reallocation pattern is not a single primitive nor any of the four named composites (consolidation, master_direction_build, board_role_clarification, vertical_rationalization). The named board_role_clarification is ASSIGN_DUTY_PARAMETER + SPLIT, but this lever's core novelty is defining 'critical' quantitatively as an exception threshold, which the text ('Defining critical quantitatively') identifies as the unresolved structural question, and it is not clear from the source that a SPLIT of a duty is intended. Missing structure: a primitive/composite that expresses 'quantitative trigger threshold that reallocates approval authority between board and management with aggregate reporting.'


## Instrument graph (nodes bearing on this cluster)

| node | citation | agency | stratum | treatment |
| --- | --- | --- | --- | --- |
| sr-23-4 | SR 23-4 | FRB | guidance | active |


## Findings

| id | provision | effect_class | normative_kind | disposition | status |
| --- | --- | --- | --- | --- | --- |
| w3-thirdparty-inccomp-dx-thi-0 | restatement :: s:TPR-01, s:TPR-02, s:TPR-03, s:TPR-04, s:TPR-06 | unresolved | interpretive_ambiguity | needs_review | draft |
| w3-thirdparty-inccomp-dx-thi-1 | undefined_term :: s:TPR-01 | unresolved | interpretive_ambiguity | needs_review | draft |
| w3-thirdparty-inccomp-dx-thi-2 | actor_ambiguity :: s:TPR-01 | unresolved | interpretive_ambiguity | needs_review | draft |
| w3-thirdparty-inccomp-dx-thi-3 | actor_ambiguity :: s:TPR-02 | unresolved | interpretive_ambiguity | needs_review | draft |


## Duplication — mirror pairs (cross-layer / cross-entity)

> Parallel obligations across layer/entity (BHC↔IDI). Lever: reliance / DEEM.

| id | provision | normative_kind | disposition |
| --- | --- | --- | --- |
| — | — | — | — |


## Duplication — restatements (same text repeated)

> Same obligation restated. Lever: MERGE / RESOLVE_CROSS_REFERENCE.

| id | provision | normative_kind | disposition |
| --- | --- | --- | --- |
| w3-thirdparty-inccomp-dx-thi-0 | restatement :: s:TPR-01, s:TPR-02, s:TPR-03, s:TPR-04, s:TPR-06 | interpretive_ambiguity | needs_review |


## Duty crosswalk (as-built citation → intended home)

| duty_id | verify status | pinned span | intended home (lever) |
| --- | --- | --- | --- |
| s:TPR-01 | verified | span-sr-23-4-att-anchor | residual |
| s:TPR-02 | verified | span-sr-23-4-att-anchor | residual |
| s:TPR-03 | verified | span-sr-23-4-att-anchor | residual |
| s:TPR-04 | verified | span-sr-23-4-att-anchor | residual |
| s:TPR-06 | verified | span-sr-23-4-att-anchor | residual |


## Authority to act

| reform lever | actor_with_authority | instrument_required | normative_kinds |
| --- | --- | --- | --- |
| Quantitative 'critical activity' threshold for board attention; management approval + aggregate reporting otherwise. | FRB, OCC, FDIC | interagency_statement | policy_choice, supervisory_value_judgment, interagency_coordination |


## Claim verification

| duty_id | verify status | method | distill anchor |
| --- | --- | --- | --- |
| s:TPR-01 | verified | live_retrieval | anchored |
| s:TPR-02 | verified | live_retrieval | anchored |
| s:TPR-03 | verified | live_retrieval | anchored |
| s:TPR-04 | verified | live_retrieval | anchored |
| s:TPR-06 | verified | live_retrieval | anchored |


## Normative review queue

| finding | provision | normative_kind (proposed) | effect |
| --- | --- | --- | --- |
| w3-thirdparty-inccomp-dx-thi-0 | restatement :: s:TPR-01, s:TPR-02, s:TPR-03, s:TPR-04, s:TPR-06 | interpretive_ambiguity | unresolved |
| w3-thirdparty-inccomp-dx-thi-1 | undefined_term :: s:TPR-01 | interpretive_ambiguity | unresolved |
| w3-thirdparty-inccomp-dx-thi-2 | actor_ambiguity :: s:TPR-01 | interpretive_ambiguity | unresolved |
| w3-thirdparty-inccomp-dx-thi-3 | actor_ambiguity :: s:TPR-02 | interpretive_ambiguity | unresolved |


## Final-status blocker summary

- 4 findings, all `draft` — 0 reach `final`.
- 4 in `needs_review` (0-op diagnostic ⇒ unresolved effect + needs_review default).
- Reform lever is a **residual checkpoint** (enum did not cleanly express it) — human decomposition required.
- Reform lever is illustrative (NG2); cannot finalize without human authorization.
- Every normative kind is a proposal; none is resolved (checkpoint discipline).
