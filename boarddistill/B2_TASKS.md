# B2_TASKS.md — Apply B1 dispositions + instrument-graph ingestion

**Audience:** an autonomous coding agent (Claude Code terminal). `AGENTS.md` (§1 rules, §2 invariants, §14 checkpoints) and `B1_TASKS.md` §3 retrieval rules remain binding. Read all three before starting.

**Human dispositions recorded (M. Hsu, 2026-07-02, via chat — the authority for this file):**
1. The **21 verified rows are accepted**.
2. The **6 support-flagged rows** (b:AUD-04, b:AUD-05, b:AUD-06, b:AUD-07, b:RGC-01 + the weak-support one) get the approved **actor-retag** treatment: the duty is retagged to the actor the verified text actually binds (management / CEO-CFO / "the company"), with the board's *indirect* oversight role stated as a separate annotation. The CAP-01 fidelity caveat is accepted as benign (no action).
3. The **51 unverified rows** are the worklist for this phase: build the resolvers that can reach appendix-, SR-attachment-, and manual-level citations, then re-verify.

**Mission:** convert as many of the 51 as the sources allow, build instrument-graph v1 for everything the 72 rows cite, and write the human dispositions into the review state — without ever editing the inventory xlsx.

---

## 1. Build order (each ends green on `make check`; commit per task)

- **B2-T0 Disposition write-back.** For the 21 accepted rows: `ReviewDisposition{state=reviewer_accepted, reviewer_id="mhsu", timestamp=2026-07-02, rationale="B1 verification accepted via chat review"}`. Statuses flow into `outputs/import/imported_duties.json` claims. *DoD:* dispositions persisted; `verify` blocker summary reflects them; nothing else changed.

- **B2-T1 Actor retag (the approved 6).** For each flagged row, emit an `ASSIGN_DUTY_PARAMETER(verb_standard/actor)` operation record with the B1 quote as evidence, and update the draft DutySpec: `actor` corrected to what the text binds; original value preserved in a `provenance` note; a separate `board_oversight_note` field stating the indirect duty (e.g., "board oversight via audit committee under SOX 301/Part 363" for the SOX 302/404 rows; "statute mandates committee existence; board duty is structural, not operational" for RGC-01). Disposition on each: `reviewer_modified`, reviewer "mhsu", same rationale. **Scope is exactly these 6 rows** — retagging any other row is a checkpoint. *DoD:* 6 retag operations + updated drafts + dispositions; tests cover one retag round-trip.

- **B2-T2 eCFR appendix resolver.** Extend `adapters/retrieval.py` to fetch and section-address CFR *appendices* (12 CFR Part 30 Apps. A & D; Part 363 App. A; Reg YY appendices; the GLBA security appendices): parse the appendix heading structure (II.A, III.F, I.E.8(b)…) into addressable spans. *DoD:* the 15 "CFR/guidance appendix" rows resolve to quoted spans (or a documented reason why not).

- **B2-T3 SR-letter / attachment resolver.** federalreserve.gov SR-letter pages + attachment PDFs (pdfplumber or pypdf; add to deps). Strategy for "Attachment, Attribute 1, p. 3" and local-line-number citations: locate the duty's quoted/paraphrased text in the attachment by fuzzy anchor match, then pin the *actual* page/paragraph as the span — record `anchor_matched: true` so nobody mistakes it for a pre-existing pinpoint cite. *DoD:* the 16 SR-attachment rows and the 12 local-line rows resolve or carry documented failure reasons.

- **B2-T4 Manual / handbook resolver.** FDIC RMS Manual of Examination Policies, OCC handbooks (Corporate & Risk Governance; Director's Book pages), FFIEC materials — same anchor-match strategy, same cache/manifest discipline. Large PDFs: cache once, extract per-citation. *DoD:* remaining manual-cited rows resolve or are documented.

- **B2-T5 Re-verify.** Re-run `verify-live` over all 51; regenerate `outputs/b1/` report artifacts as `outputs/b2/` (keep b1 as the audit trail). Every remaining `unverified` gets a specific, human-readable reason. *DoD:* updated summary table; review queue reduced to genuine residuals; **any `contradicted` result is a checkpoint** (record, never reconcile).

- **B2-T6 Instrument graph v1.** One `InstrumentNode` per instrument cited by the 72 rows (statutes, regs, appendices, SR letters, manuals): stratum, agency, effective date, `treatment_status` with evidence — including `superseded` for SR 09-4 (per SR 15-18 fn.5) and any `rescinded_informal` found via web.archive.org. Wire `GraphStore.baseline_for(duty_ref, as_of)` to real nodes; keep fixture graphs untouched. *DoD:* graph serialized to `data/graph/us-gsib_v1.json`; `baseline_for` answers for every verified duty; unit tests from cache.

- **B2-T7 Report + README.** `outputs/b2/B2_report.md`: before/after verification table, retag summary, graph coverage stats, residual queue for the human, re-verification-cadence recommendation. README section updated. *DoD:* full suite green; all work committed.

## 2. Checkpoints (stop, `TODO(human)`, leave a draft)

1. Any `contradicted` claim, anywhere.
2. Any retag candidate beyond the approved 6.
3. Anchor matches below high confidence (quote not found or multiple plausible locations) — present candidates, do not pick.
4. Treatment-status calls that require judgment (e.g., "is this 1995 letter implicitly superseded?") — record evidence, propose, do not decide.
5. Paywalled/licensed sources, anything CSI-adjacent, any allowlist expansion beyond: the B1 §3 list + specific OCC/FDIC handbook and manual pages.

## 3. Definition of done

The 21 acceptances and 6 retags are persisted review state; appendix/SR/manual citations are resolvable infrastructure, not gaps; the 51-row unverified bucket is reduced to a short residual list with reasons; instrument-graph v1 covers every instrument the MVP rows cite; `make check` green and deterministic (cache-replay); every task committed.

**After B2, the next phase is the LLM layer (distill/diagnose/classify behind the proven interfaces) — a separate instruction file; do not start it.**

---

**Begin at B2-T0.**
