# B3-T6 — eval report

## (a) Agreement vs. B0 gold

- Operation set: preserved verbatim from b0 (primitive-set agreement by construction); one systematic transform: ASSIGN_DUTY_STANDARD → ASSIGN_DUTY_PARAMETER (B0 TODO-2)

- Effect-class agreement: **8/9**


| decomposition | mine | b0 gold | conditional | agree | characterization |
| --- | --- | --- | --- | --- | --- |
| D1 | change | change | — | ✓ | agree |
| D2 | change | change | — | ✓ | agree |
| D3 | change | change | yes | ✓ | agree |
| D4 | change | change | — | ✓ | agree |
| D5 | clarify | clarify | yes | ✓ | agree |
| D6 | change | change | yes | ✓ | agree |
| D7 | codify | codify | — | ✓ | agree |
| D8 | change | change | — | ✓ | agree |
| D9 | fill_gap | codify | yes | ✗ | effect differs — recorded, not reconciled |

Disagreements are characterized, not reconciled (the B0 gold is never edited).


## (b) Stability (live samples, one cluster, then cached)

- **distill** (3 samples): verb agreement ✓ ['none_specified']; cadence ✓ ['none_specified']

- **diagnose** (3 samples): Jaccard 0.5; counts [8, 9, 7]; stable ['duplicate_duty:b:AUD-01,b:AUD-02,b:AUD-03', 'duplicate_duty:s:GOV-08,s:GOV-12', 'duplicate_duty:s:IAU-01,s:IAU-02', 'rule_guidance_restatement:b:FID-02,s:BCG-06', 'undefined_term:b:AUD-01', 'undefined_term:s:IAU-01']


## (c) Citation integrity (release gate)

- Distilled anchored claims: 208 · anchor failures: 0 · diagnostic anchor failures: 0
- **Hallucinated-citation rate: 0.0 — release gate PASS**


## (d) Baseline comparison (raw inventory, same checks)

- Cluster: Audit committee & independence · raw rows: 21 · raw claims: 21 · with a pinned excerpt: 13

- Raw inventory claims cite placeholder span ids (cite-<duty>) with no quote; only rows later verified in B1/B2 gained a pinned excerpt. The distillation layer adds verbatim, offset-checkable evidence for every asserted field (see citation integrity: 0 hallucinated).

