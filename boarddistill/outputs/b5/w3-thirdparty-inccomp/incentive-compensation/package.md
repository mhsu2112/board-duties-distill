# Consolidation package — Incentive compensation

> Wave: `w3-thirdparty-inccomp`. 
**Status: blocked pending human review.** Every finding is `draft`; none is `final`. The reform lever below is an illustrative (NG2) proposal, not an adopted instrument.

## Cluster summary

- distilled duties: 4 (verified: 4) · findings: 3 · final: 0 · in-review: 3


## As-built duties (distilled)

| duty_id | verb | object | cadence | force | anchor |
| --- | --- | --- | --- | --- | --- |
| b:INC-01 | none_specified | Disclosure to the appropriate Federal regulator of the structures of all incentive-based compensation arrangements offered by covered financial institutions | none_specified | — | ok |
| b:IND-07 | none_specified | Listing standards prohibiting listing of equity securities of an issuer not in compliance with compensation committee requirements | none_specified | — | ok |
| s:BCG-11 | none_specified | Board or designated committee sets and periodically reevaluates director compensation, which should be competitive to attract and retain qualified directors, aligned with industry standards, and safeguarded against being excessive | event_driven | — | ok |
| s:INC-05 | none_specified | Ongoing training program for all directors, covering complex products/services/risks, applicable laws and supervisory requirements, and other board-identified topics. | continuous | — | ok |


## Intended — reform lever (illustrative, NG2)

| lever | status | composition | primitives | effect | instrument_required |
| --- | --- | --- | --- | --- | --- |
| Finalize one 956 framework or rely on guidance; SEC independence satisfies the prudential element. | residual | residual | — | unresolved | joint_rulemaking |

> **Residual checkpoint** — the 16-primitive set did not cleanly express this lever in the automated pass: The lever offers a disjunctive choice ('finalize one 956 framework OR rely on guidance') requiring a six-agency policy decision to complete an unimplemented statutory mandate, not a mechanical structural consolidation of existing enacted text. Completing an unfinished DFA §956 rulemaking (or electing to abandon it in favor of guidance) is a discretionary interagency policy act that no primitive expresses; the calculus operates on enacted overlapping duties, and §956 duties are 'unimplemented.' The additional claim that 'SEC independence satisfies the prudential element' would suggest DEEM_SATISFIED, but the SEC comp-committee independence duty and the prudential §956 duty serve distinct purposes (investor protection vs. safety-and-soundness) and one duty (the §956 rule) does not yet exist to be deemed-satisfying, so no both-survive deem relation can be anchored.


## Instrument graph (nodes bearing on this cluster)

| node | citation | agency | stratum | treatment |
| --- | --- | --- | --- | --- |
| 12-cfr-part-30-app-d | 12 CFR Part 30 App. D | OCC | enforceable_guideline | active |
| 12-u-s-c-5641 | 12 U.S.C. 5641 | Congress | statute | active |
| 17-cfr-part-240 | 17 CFR Part 240 | SEC | regulation | active |
| occ-comptroller-s-handbook-corporate-risk-governance | OCC Comptroller's Handbook: Corporate & Risk Governance | OCC | manual | active |


## Findings

| id | provision | effect_class | normative_kind | disposition | status |
| --- | --- | --- | --- | --- | --- |
| w3-thirdparty-inccomp-dx-inc-0 | actor_ambiguity :: s:BCG-11 | unresolved | institutional_discretion, interpretive_ambiguity | needs_review | draft |
| w3-thirdparty-inccomp-dx-inc-2 | undefined_term :: b:INC-01 | unresolved | interpretive_ambiguity | needs_review | draft |
| w3-thirdparty-inccomp-dx-inc-3 | undefined_term :: s:INC-05 | unresolved | interpretive_ambiguity | needs_review | draft |


## Duplication — mirror pairs (cross-layer / cross-entity)

> Parallel obligations across layer/entity (BHC↔IDI). Lever: reliance / DEEM.

| id | provision | normative_kind | disposition |
| --- | --- | --- | --- |
| — | — | — | — |


## Duplication — restatements (same text repeated)

> Same obligation restated. Lever: MERGE / RESOLVE_CROSS_REFERENCE.

| id | provision | normative_kind | disposition |
| --- | --- | --- | --- |
| — | — | — | — |


## Duty crosswalk (as-built citation → intended home)

| duty_id | verify status | pinned span | intended home (lever) |
| --- | --- | --- | --- |
| b:INC-01 | verified | span-usc-t12-s5641-5641 | residual |
| b:IND-07 | verified | span-ecfr-t17-p240-240.10C-1 | residual |
| s:BCG-11 | verified | span-occ-ch-crg-anchor | residual |
| s:INC-05 | verified | span-ecfr-t12-p30-appD-III.E | residual |


## Authority to act

| reform lever | actor_with_authority | instrument_required | normative_kinds |
| --- | --- | --- | --- |
| Finalize one 956 framework or rely on guidance; SEC independence satisfies the prudential element. | FRB, OCC, FDIC, SEC, NCUA, FHFA | joint_rulemaking | policy_choice, interagency_coordination, statutory_constraint, institutional_discretion |


## Claim verification

| duty_id | verify status | method | distill anchor |
| --- | --- | --- | --- |
| b:INC-01 | verified | live_retrieval | anchored |
| b:IND-07 | verified | live_retrieval | anchored |
| s:BCG-11 | verified | live_retrieval | anchored |
| s:INC-05 | verified | live_retrieval | anchored |


## Normative review queue

| finding | provision | normative_kind (proposed) | effect |
| --- | --- | --- | --- |
| w3-thirdparty-inccomp-dx-inc-0 | actor_ambiguity :: s:BCG-11 | institutional_discretion, interpretive_ambiguity | unresolved |
| w3-thirdparty-inccomp-dx-inc-2 | undefined_term :: b:INC-01 | interpretive_ambiguity | unresolved |
| w3-thirdparty-inccomp-dx-inc-3 | undefined_term :: s:INC-05 | interpretive_ambiguity | unresolved |


## Final-status blocker summary

- 3 findings, all `draft` — 0 reach `final`.
- 3 in `needs_review` (0-op diagnostic ⇒ unresolved effect + needs_review default).
- Reform lever is a **residual checkpoint** (enum did not cleanly express it) — human decomposition required.
- Reform lever is illustrative (NG2); cannot finalize without human authorization.
- Every normative kind is a proposal; none is resolved (checkpoint discipline).
