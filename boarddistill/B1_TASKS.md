# B1_TASKS.md — Full-coverage claim verification (the first retrieval step)

**Audience:** an autonomous coding agent (Claude Code terminal). Read `AGENTS.md` first — its §1 working rules, §2 invariants, and §14 checkpoints remain binding. This file *narrowly relaxes* one slice-one restriction: **network retrieval is now permitted, for the sources on the §3 allowlist only.** Everything else in AGENTS.md stands.

**Mission (PRD B1, exit criterion):** verify, against primary sources, every claim in the MVP-cluster duty rows — converting them from "LLM-synthesized draft" to trusted L1 input — and replace the fixtures' paraphrased quotes with verified verbatim text. **Verification never edits the inventory xlsx and never silently "fixes" a duty**: a bad citation is a *finding for a human*, not a correction to apply.

---

## 1. Scope

Target rows: every row in `outputs/import/imported_duties.json` whose Cluster is one of:
`Risk-governance framework / strategy` · `Audit committee & independence` · `Capital planning & stress testing` · `Risk committee architecture` · `Internal control over financial reporting`
(the three MVP clusters + the two entangled clusters B0's decompositions operate on; ~72 rows). Full coverage — every row, every claim; no sampling.

Out of scope: the other ~155 rows (later); instrument-graph ingestion beyond what verification needs; any LLM distillation/classification; any change to `Synthesis/*.xlsx`.

## 2. What "verified" means (per claim)

For each duty row, verify three things and record each as a `VerifierRecord` attached to the claim:

1. **Citation exists** — the cited provision resolves to real, retrievable text (F1 fabricated-source check).
2. **Text supports the duty** — the provision actually imposes the duty on the actor stated, at the board level stated (F2 misattribution / F4 invented-obligation check). Capture the supporting **verbatim quote** and pin it as a `SourceSpan` (source id, citation down to paragraph, quote, char offsets into the cached document).
3. **Currency** — the provision is in force as of `inventory_as_of` (2026-06) and today; note amendments/rescissions (F3 stale-as-current check). Where a rescission is informal, record `rescinded_informal` with the archival evidence.

Statuses: `verified` (all three hold, quote captured) · `contradicted` (citation wrong, duty misstated, or provision not in force — attach evidence) · `unverified` (source unreachable or ambiguous after reasonable effort — attach what was tried). **Never guess: unreachable ⇒ `unverified`, not `verified`.**

Map integrity flags to the rubric vocabulary (`specs/` + `../Tools/policy-sludge-rubric-v2.md`): F1→contradicted(fabricated), F2→contradicted(misattributed), F3→as_of_valid=false, F4→contradicted(invented), F7→unverified(unsupported).

## 3. Retrieval rules

- **Allowlist (primary sources only):** ecfr.gov · govinfo.gov · uscode.house.gov · federalregister.gov · federalreserve.gov · occ.gov / occ.treas.gov · fdic.gov · ffiec.gov · sec.gov · web.archive.org (for rescinded/moved items) · nyse.com and listingcenter.nasdaq.com (exchange listing standards, public pages only).
- Anything not on the list, anything paywalled/licensed, and anything that looks like confidential supervisory information: **stop, checkpoint (§6.3)**. No secondary sources (law-firm memos, Wikipedia, blogs) as *evidence* — they may be used as finding aids only and never cited in a `SourceSpan`.
- **Cache everything.** Every retrieved document is saved under `data/sources/<source_id>/` with a `manifest.json` entry: `{url, retrieved_at, sha256, title, notes}`. Verification must be auditable and replayable from the cache alone.
- Be polite: sequential fetches, no crawling; fetch the specific cited part (eCFR section pages, not whole titles) where possible.

## 4. Engineering shape (keep the proven interfaces)

- `adapters/retrieval.py` — allowlisted fetcher + cache/manifest. The **only** module that touches the network.
- `distillcore/pipeline/verify.py` gains a `SourceResolver` protocol; the existing deterministic span-check keeps working. New live path: `boarddistill verify-live outputs/import --clusters <...> --cache data/sources`.
- **`make check` stays deterministic.** All new tests run from the cache (record/replay); network tests are opt-in via `pytest -m live` and excluded from the default run. Same-cache re-runs must be byte-identical.
- Outputs: `outputs/b1/verification.json` (all VerifierRecords) · `outputs/b1/B1_report.md` (human-readable: per-row status table, quote snippets, F-flag list, currency notes, summary stats) · `outputs/b1/review_queue.json` (every `contradicted`/`unverified` row — the TODO(human) list).

## 5. Build order (each ends green on `make check`; commit per task)

- **B1-T0 Row extraction** — deterministically select the ~72 target rows from `outputs/import/imported_duties.json`; write `outputs/b1/targets.json`. *DoD:* count and IDs printed; stable across runs.
- **B1-T1 Fetcher + cache** — `adapters/retrieval.py`, allowlist enforcement in code (a non-allowlisted URL raises), manifest. *DoD:* unit tests with a fake transport; allowlist test.
- **B1-T2 Verify rows** — resolve each citation, capture spans, write VerifierRecords for all target rows. Work cluster by cluster; commit per cluster. *DoD:* every target row has a status; no row skipped.
- **B1-T3 Fixture realification** — replace the `[FIXTURE]` paraphrases in the four fixture `sources.json` files with verified verbatim quotes + pinned citations from the cache (12 CFR 363.2(b); 15 U.S.C. 7262(b); 12 U.S.C. 1831m; SR 12-17 attributes; 12 CFR 252.33(a)(1); 12 CFR 30 App. D II.A & III.F; SR 21-3). `[PLACEHOLDER]` reform-lever spans **stay** placeholders (they have no source by design). Re-run the full suite + `eval-fixture` after. *DoD:* fixtures carry real text; 84+ tests still green; eval agreement unchanged.
- **B1-T4 Report + review queue** — write the three §4 outputs; update `outputs/import/imported_duties.json` claims with verifier statuses (banner updated: "verified per B1 where marked"). *DoD:* summary stats in `B1_report.md`; review queue lists every non-verified row with evidence.
- **B1-T5 Replay tests + README** — cache-based regression tests; README section "B1: what was verified, when, from where"; note the re-verification cadence question for the human.

## 6. Checkpoints — stop, write `TODO(human)`, leave a draft

1. **Any `contradicted` claim.** Record it in the review queue with evidence; do NOT edit the inventory, the imported drafts' duty text, or B0's decompositions to match. (If a contradiction undermines a B0 operand — e.g., a lever's citation is wrong — flag the decomposition too.)
2. A citation that resolves ambiguously (two plausible provisions): present both candidates with quotes; do not pick.
3. Any source requiring license/paywall/login, or anything resembling CSI.
4. Fixture realification where the verified text *materially differs* from the paraphrase (don't quietly swap meaning — flag the delta).
5. Anything that would expand scope beyond the ~72 rows or the allowlist.

## 7. Definition of done (B1 exit, per PRD)

Every target row carries an evidence-backed verifier status; the fixtures rest on verified verbatim text; `outputs/b1/B1_report.md` gives the human a complete accept/fix queue; `make check` green and deterministic; all work committed.

---

**Begin at B1-T0.** Network is permitted for §3 allowlisted primary sources only. When in doubt: cache it, quote it, or mark it `unverified` — never assert what you cannot show.
