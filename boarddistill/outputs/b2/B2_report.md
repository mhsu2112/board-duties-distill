# B2 verification report

Applied the B1 dispositions and built appendix / SR-attachment / manual resolvers, lifting verified MVP-cluster rows from **21/72 (B1)** to **50/72 (B2)**, with **0 contradicted**. All retrieval is allowlisted and cache-replayable.

## Verification: before (B1) → after (B2)

| cluster | B1 verified | B2 verified |
| --- | --- | --- |
| Audit committee & independence | 4 | 13 |
| Capital planning & stress testing | 8 | 17 |
| Internal control over financial reporting | 4 | 4 |
| Risk committee architecture | 5 | 5 |
| Risk-governance framework / strategy | 0 | 11 |
| **total** | 21 | 50 |

## Actor retags (the approved 6)

| duty | was (board_level) | retagged actor | flag |
| --- | --- | --- | --- |
| b:AUD-04 | Audit committee | management / the institution | — |
| b:AUD-05 | Audit committee | management | — |
| b:AUD-06 | Audit committee | external auditor (registered public accounting firm) | — |
| b:AUD-07 | Audit committee | CEO and CFO (principal executive and financial officers) | — |
| b:RGC-01 | Risk committee | the bank holding company | — |
| s:CAP-11 | n/a (superseded for target firms) | management / the company (proposed) | TODO(human) |

Dispositions: reviewer_accepted=15, reviewer_modified=6

## Instrument graph v1

- instruments: 16 · verified duties: 50 · baseline answered: 50
- strata: enforceable_guideline=2, guidance=5, manual=2, regulation=5, statute=2
- SR 09-4 recorded superseded (SR 15-18 fn.5); SR 95-51 treatment flagged TODO(human).

## Residual queue (22) — TODO(human)

Mostly borderline anchor matches (0.40–0.60) recorded as candidates, never picked (checkpoint §3). Each carries a specific reason.

| duty | citation | reason |
| --- | --- | --- |
| s:BCG-01 | Appendix C — Executive commit… | anchor match borderline in OCC Comptroller's Handbook: Corp… |
| s:BCG-02 | Appendix C — Audit committee | duty text not located in OCC Comptroller's Handbook: Corpor… |
| s:BCG-04 | Appendix C — Asset-liability … | anchor match borderline in OCC Comptroller's Handbook: Corp… |
| s:BCG-05 | Appendix C — Risk committee | anchor match borderline in OCC Comptroller's Handbook: Corp… |
| s:BCG-07 | Appendix C — Compensation com… | anchor match borderline in OCC Comptroller's Handbook: Corp… |
| s:BCG-09 | Board Leadership (CRG); Direc… | anchor match borderline in OCC Comptroller's Handbook: Corp… |
| s:BCG-10 | Director Nomination and Selec… | anchor match borderline in OCC Comptroller's Handbook: Corp… |
| s:BCG-12 | Board and Committee Minutes | anchor match borderline in OCC Comptroller's Handbook: Corp… |
| s:BCG-14 | Audit committee composition; … | part-level CFR cite; no addressable section |
| s:CAP-05 | Attachment, sec. III.A.1, p. … | anchor match borderline in SR 15-18 attachment (best 0.53);… |
| s:CAP-10 | FR Y-14A attestation requirem… | unrecognized or non-primary citation form |
| s:FDR-03 | Management (local ll. ~12073-… | anchor match borderline in FDIC RMS Manual of Examination P… |
| s:FDR-04 | Management (local ll. ~12170-… | duty text not located in FDIC RMS Manual of Examination Pol… |
| s:FDR-05 | Management component (local l… | local line-number reference (guidance doc); no addressable … |
| s:GOV-02 | Attachment, Attribute 1, p. 3… | anchor match borderline in SR 21-3 attachment (best 0.53); … |
| s:GOV-11 | Attachment, Attribute 4, p. 6 | anchor match borderline in SR 21-3 attachment (best 0.50); … |
| s:GOV-15 | Section A.2 (Corporate Govern… | no attachment PDF found on the SR 12-17 page |
| s:GOV-18 | Attachment, Governance & Cont… | anchor match borderline in SR 19-3 attachment (best 0.47); … |
| s:GOV-19 | Adopting release (bcreg202511… | anchor match borderline in SR 19-3 attachment (best 0.46); … |
| s:GOV-20 | Risk-management rating defini… | anchor match borderline in SR 95-51 attachment (best 0.56);… |
| s:IAU-03 | Attachment, p. (local ll. 599… | anchor match borderline in SR 13-1 attachment (best 0.56); … |
| s:STR-02 | Attachment, p. (local ll. 822… | anchor match borderline in SR 12-7 attachment (best 0.50); … |

## Re-verification cadence (recommendation)

- **Quarterly** re-run of `verify-live` + diff against the cached `sha256`s; a changed hash flags an amended provision for human review.
- **On SR-letter issuance/rescission**, re-check the affected instrument nodes (treatment_status) — especially the TODO(human) items (SR 95-51) and archival `rescinded_informal` candidates via web.archive.org.
- The eCFR snapshot date and U.S. Code edition are pinned; bump them deliberately, not implicitly, so the audit trail stays reproducible.
