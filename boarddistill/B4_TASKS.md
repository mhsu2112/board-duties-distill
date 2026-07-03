# B4_TASKS.md — Apply the B3 review dispositions + close the known defects

**Audience:** an autonomous coding agent (Claude Code terminal). `AGENTS.md`, `B1_TASKS.md` §3 (retrieval rules), and `B3_TASKS.md` §2 (LLM harness rules) remain binding.

**Human dispositions recorded (M. Hsu, 2026-07-02, via `../REVIEW_PACKET_B3.md` — all recommendations accepted; that file is the authority):**
1. **f-D1…f-D9 advance** — `reviewer_accepted` *as draft roadmap direction* (not policy adoption), reviewer "mhsu", rationale "REVIEW_PACKET_B3 Part 1"; feasibility ranking noted: D4 first, D5 second, D3 hardest.
2. **b:AUD-07** — certification duty stays with CEO/CFO; the board-side residual is audit-committee **oversight of the certification process** (`review_and_challenge` in the oversight note, never `certify` as a board verb).
3. **The 10 mispinned rows** (`b:AUD-08, b:CAP-02, b:RGC-05, s:BCG-03, s:CAP-07, s:CAP-09, s:GOV-03, s:GOV-04, s:GOV-08, s:GOV-12`) — re-pin approved.
4. **Duplicate diagnostics split** into `mirror_pair` and `restatement` kinds; both are official diagnostic families.
5. **All 18 dx-* diagnostics accepted** as investigation items (`reviewer_accepted`), seeding the DEFINE_TERM and ASSIGN_DUTY_PARAMETER worklists.
6. **Concept-node instrument-graph extension approved** so the classifier can reach the five `unresolved` levers.

**Mission:** write those dispositions into the review state, fix the two known defect classes (mispins; graph coverage), re-run classification, and re-render the packages — ending with the MVP clusters in a coherent, human-reviewed, evidence-complete state that the scale-up and benchmark phases can build on.

---

## 1. Build order (each ends green on `make check`; commit per task)

- **B4-T0 Disposition write-back.** Items 1, 2 (disposition part), and 5 above as `ReviewDisposition` records; regenerate blocker summaries. **Findings still do not reach `final`** — `reviewer_accepted` on a draft-direction basis is recorded via the disposition's rationale; the `status` field stays `draft` until an operative reform instrument exists (NG2). *DoD:* dispositions persisted and visible in `verify` output; nothing silently finalized.
- **B4-T1 AUD-07 fix.** Apply item 2 to the distilled DutySpec (verb on the board-side note = `review_and_challenge`; certification verb lives with the CEO/CFO actor record); add a regression test: a board-level `certify` verb on a row whose actor is management triggers the verb-vs-actor cross-check. *DoD:* conflict cleared; test in place.
- **B4-T2 Re-pin the 10 rows.** Targeted retrieval per row: find the source location that actually supports the stated duty (allowlist unchanged; anchor-match with the B2 conventions, `anchor_matched: true` where fuzzy). Update spans; re-run LLM distill for exactly these 10 (live, then cached). Rows whose duty text cannot be supported anywhere in the cited instrument: **checkpoint — record as candidate F2/F4 in a fresh review queue, do not fix silently.** *DoD:* each of the 10 either distills cleanly from a correct pin or sits in the queue with evidence.
- **B4-T3 Diagnostic-kind split.** `duplicate_duty` → `mirror_pair` (cross-layer/cross-entity, RELATE_OBLIGATION-shaped) and `restatement` (same-text repetition, MERGE/RESOLVE_CROSS_REFERENCE-shaped); re-key the 9 existing duplicate diagnostics plus the 11 B0 mirror pairs under the new kinds; packages report the two families in separate tables. *DoD:* both families render distinctly; enum + tests updated.
- **B4-T4 Concept-node graph extension.** Add typed concept nodes (kind: `concept_ref`) for the operand concepts the levers cite — at minimum: `SOX-404b-attestation`, `Part363-ICFR-assessment`, `AppD-committee-expectations`, `AppD-bank-committee-expectations`, `consolidated-committee-standard`, the D3 committee-requirements composite, and the D6/D7/D8/D9 targets — each grounded to its underlying instrument node(s) with span evidence (no free-floating concepts). *DoD:* `baseline_for` resolves every B0 operand; graph tests green.
- **B4-T5 Re-classify + re-render.** Re-run the mechanical classifier over f-D1…f-D9 with the extended graph; the five `unresolved` should now classify (expected: D3/D4/D6/D8 `change`, D7 `codify`; D9 re-examined against B0's `codify` — record agreement or characterized disagreement, **never edit the B0 gold**). Re-render the three packages + regenerate the eval report section (a). *DoD:* zero `unresolved` effect classes among f-D1…f-D9, or documented reasons; updated B0-agreement number reported.
- **B4-T6 Report.** `outputs/b4/B4_report.md`: dispositions applied, re-pin outcomes, new effect classes and B0 agreement, the two duplication-family tables, any fresh checkpoints. README updated. *DoD:* full suite green from cache; all committed.

## 2. Checkpoints (stop, `TODO(human)`, leave a draft)

1. Any re-pinned row whose duty text is unsupportable in the cited instrument (candidate invented/misattributed obligation — the first potential real F2/F4 in the corpus).
2. Any re-classified effect class that *disagrees* with B0 gold — record as characterized disagreement.
3. Concept nodes that cannot be grounded to an instrument with span evidence — propose, do not add ungrounded.
4. Anything touching the statutory floor, any normative kind resolution, any allowlist expansion.

## 3. Definition of done

All B3 dispositions persisted under "mhsu"; AUD-07 coherent; the 10 pins fixed or escalated; both duplication families first-class; every lever effect-classified with the extended graph; packages and eval regenerated; `make check` green offline; committed.

**After B4, two arcs remain and get their own files when M. Hsu calls for them: (i) scale to the remaining ~27 clusters, (ii) the RBI Master-Directions rediscovery benchmark. Do not start either.**

---

**Begin at B4-T0.**
