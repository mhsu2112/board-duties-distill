# Consolidation package — Resolution, recovery & contingency funding

> Wave: `w1-liquidity-resolution`. 
**Status: blocked pending human review.** Every finding is `draft`; none is `final`. The reform lever below is an illustrative (NG2) proposal, not an adopted instrument.

## Cluster summary

- distilled duties: 5 (verified: 5) · findings: 4 · final: 0 · in-review: 4


## As-built duties (distilled)

| duty_id | verb | object | cadence | force | anchor |
| --- | --- | --- | --- | --- | --- |
| b:LIQ-04 | none_specified | Independent review function to evaluate the company's liquidity risk management | annual | — | ok |
| b:RES-01 | approve | The resolution plan of a covered company, which must be approved by the board of directors and noted in the minutes before submission | event_driven | — | ok |
| b:RES-02 | none_specified | A covered insured depository institution's resolution plan submission | none_specified | — | ok |
| s:REC-02 | none_specified | Oversight of the firm's recovery planning process, focused on the firm's ability to identify and implement recovery options and oversee management's remediation of weaknesses | none_specified | — | ok |
| s:RES-05 | none_specified | Applicability of resolution plan and informational filing requirements to insured depository institutions with $50 billion or more in total assets | none_specified | — | ok |


## Intended — reform lever (illustrative, NG2)

| lever | status | composition | primitives | effect | instrument_required |
| --- | --- | --- | --- | --- | --- |
| Single 'resilience planning' board cycle; shared resolution submission with an IDI annex. | residual | residual | — | unresolved | joint_rulemaking |

> **Residual checkpoint** — the 16-primitive set did not cleanly express this lever in the automated pass: The lever bundles two structurally different moves that no single primitive or named composite captures: (1) collapsing multiple board-approved resilience/recovery plans onto one cycle (a cadence/parameter move plus MERGE of overlapping approvals), and (2) creating a shared resolution submission where the FDIC IDI interest is retained as a genuinely distinct annex ('parallel-but-justified'). The FDIC's distinct interest in resolving the insured bank even if the parent's plan fails means this is NOT a clean MERGE (the IDI submission survives as a distinct annex), nor is it vertical_rationalization (no entity_level_mirror + DEEM_SATISFIED + FACTOR_EXCEPTION pattern fits the 'shared submission with retained-distinct annex' shape). It combines a cadence-alignment across cycles, a partial merge of overlapping content, and a preserved parallel-distinct obligation \u2014 a mixture that spans authorities under two separate statutes and cannot be reduced to one primitive or one of the four composites.


## Instrument graph (nodes bearing on this cluster)

| node | citation | agency | stratum | treatment |
| --- | --- | --- | --- | --- |
| 12-cfr-part-243 | 12 CFR Part 243 | FRB | regulation | active |
| 12-cfr-part-252 | 12 CFR Part 252 | FRB | regulation | active |
| 12-cfr-part-360 | 12 CFR Part 360 | FDIC | regulation | active |
| sr-14-8 | SR 14-8 | FRB | guidance | active |


## Findings

| id | provision | effect_class | normative_kind | disposition | status |
| --- | --- | --- | --- | --- | --- |
| w1-liquidity-resolution-dx-res-0 | restatement :: b:RES-02, s:RES-05 | unresolved | interpretive_ambiguity | needs_review | draft |
| w1-liquidity-resolution-dx-res-1 | actor_ambiguity :: s:REC-02 | unresolved | institutional_discretion | needs_review | draft |
| w1-liquidity-resolution-dx-res-2 | undefined_term :: b:LIQ-04 | unresolved | — | needs_review | draft |
| w1-liquidity-resolution-dx-res-3 | undefined_term :: b:RES-02 | unresolved | interpretive_ambiguity | needs_review | draft |


## Duplication — mirror pairs (cross-layer / cross-entity)

> Parallel obligations across layer/entity (BHC↔IDI). Lever: reliance / DEEM.

| id | provision | normative_kind | disposition |
| --- | --- | --- | --- |
| — | — | — | — |


## Duplication — restatements (same text repeated)

> Same obligation restated. Lever: MERGE / RESOLVE_CROSS_REFERENCE.

| id | provision | normative_kind | disposition |
| --- | --- | --- | --- |
| w1-liquidity-resolution-dx-res-0 | restatement :: b:RES-02, s:RES-05 | interpretive_ambiguity | needs_review |


## Duty crosswalk (as-built citation → intended home)

| duty_id | verify status | pinned span | intended home (lever) |
| --- | --- | --- | --- |
| b:LIQ-04 | verified | span-ecfr-t12-p252-252.34 | residual |
| b:RES-01 | verified | span-ecfr-t12-p243-243.4 | residual |
| b:RES-02 | verified | span-ecfr-t12-p360-360.10 | residual |
| s:REC-02 | verified | span-sr-14-8-body-anchor | residual |
| s:RES-05 | verified | span-ecfr-t12-p360-360.10 | residual |


## Authority to act

| reform lever | actor_with_authority | instrument_required | normative_kinds |
| --- | --- | --- | --- |
| Single 'resilience planning' board cycle; shared resolution submission with an IDI annex. | FRB, FDIC | joint_rulemaking | policy_choice, supervisory_value_judgment, interagency_coordination, statutory_constraint |


## Claim verification

| duty_id | verify status | method | distill anchor |
| --- | --- | --- | --- |
| b:LIQ-04 | verified | live_retrieval | anchored |
| b:RES-01 | verified | live_retrieval | anchored |
| b:RES-02 | verified | live_retrieval | anchored |
| s:REC-02 | verified | live_retrieval | anchored |
| s:RES-05 | verified | live_retrieval | anchored |


## Normative review queue

| finding | provision | normative_kind (proposed) | effect |
| --- | --- | --- | --- |
| w1-liquidity-resolution-dx-res-0 | restatement :: b:RES-02, s:RES-05 | interpretive_ambiguity | unresolved |
| w1-liquidity-resolution-dx-res-1 | actor_ambiguity :: s:REC-02 | institutional_discretion | unresolved |
| w1-liquidity-resolution-dx-res-2 | undefined_term :: b:LIQ-04 | — | unresolved |
| w1-liquidity-resolution-dx-res-3 | undefined_term :: b:RES-02 | interpretive_ambiguity | unresolved |


## Final-status blocker summary

- 4 findings, all `draft` — 0 reach `final`.
- 4 in `needs_review` (0-op diagnostic ⇒ unresolved effect + needs_review default).
- Reform lever is a **residual checkpoint** (enum did not cleanly express it) — human decomposition required.
- Reform lever is illustrative (NG2); cannot finalize without human authorization.
- Every normative kind is a proposal; none is resolved (checkpoint discipline).
