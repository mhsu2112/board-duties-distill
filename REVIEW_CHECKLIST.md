# Review Checklist — the 3 items that need your judgment

> **✅ RESOLVED — July 2, 2026.** M. Hsu's decisions (via chat): Item 1 — all citations approved, placeholders retained until B1. Item 2 — anchors approved, **DFA §165(d) added**. Item 3 — all mapping rules confirmed as drafted. Items 4–5 executed the same day. This file is retained as the decision record.

**How to use this:** read each item, then either type your answers directly under each question (any text editor works — TextEdit is fine), or just tell Claude your decisions in chat (e.g., "Item 2: add §165(d). Item 3, rule 1: OK as is."). Claude makes all the actual file edits and re-runs the tests. **You never need to edit JSON or code.**

---

## Item 1 — Fixture citations (15 entries)

These are the hand-authored "source spans" the three test fixtures rest on. Two label types:
- **[FIXTURE]** = real citation, paraphrased text. *Your check: is the citation right, and is the paraphrase fair?*
- **[PLACEHOLDER]** = an openly fabricated stand-in for the *proposed reform* (which has no real source yet, since the reform doesn't exist). *Your check: fine to keep as declared placeholders until B1? (Recommended: yes.)*

### icfr fixture (SOX/FDICIA deem-satisfied)
| # | Label | Citation | Paraphrase (first line) | OK? |
|---|---|---|---|---|
| 1 | FIXTURE | 12 CFR 363.2(b) | "Management shall annually assess and report on the effectiveness of the institution's ICFR…" | ☐ |
| 2 | FIXTURE | 15 U.S.C. 7262(b) | "The registered public accounting firm shall attest to, and report on, management's assessment…" | ☐ |
| 3 | FIXTURE | 12 U.S.C. 1831m | "Each insured depository institution shall file an annual report on compliance…" | ☐ |
| 4 | FIXTURE | 12 U.S.C. 1831m (designated-laws annex) | "Compliance with designated safety-and-soundness laws (insider lending, dividend…)…" | ☐ |
| 5 | PLACEHOLDER | "Reform lever D4 memorandum" | deem-satisfied reform text | ☐ keep as placeholder |

### sr12-17 fixture (codify guidance into Reg YY)
| # | Label | Citation | Paraphrase | OK? |
|---|---|---|---|---|
| 6 | FIXTURE | SR 12-17 / CA 12-14, Attribute 1 | "board should ensure the risk-management function is independent…" | ☐ |
| 7 | FIXTURE | SR 12-17 / CA 12-14, Attribute 2 | "board should ensure risk appetite is established and embedded…" | ☐ |
| 8 | FIXTURE | 12 CFR 252.33(a) | "board shall approve the enterprise-wide risk-management policies…" | ☐ |
| 9 | PLACEHOLDER | "Reform lever D6 memorandum" | relocation reform text | ☐ keep as placeholder |

### board-effectiveness fixture (merge App. D III.F + SR 21-3)
| # | Label | Citation | Paraphrase | OK? |
|---|---|---|---|---|
| 10 | FIXTURE | 12 CFR Part 30, App. D, III.F | "board should conduct an annual self-assessment of its effectiveness…" | ☐ |
| 11 | FIXTURE | SR 21-3 | "board should periodically assess its effectiveness, composition, and governance…" | ☐ |
| 12 | PLACEHOLDER | "Reform lever D7 memorandum" | merge reform text | ☐ keep as placeholder |

### _calculus stub (BHC/IDI mirror pair)
| # | Label | Citation | Paraphrase | OK? |
|---|---|---|---|---|
| 13 | FIXTURE | 12 CFR 252.33(a)(1) | "BHC board approves the enterprise-wide risk-management framework." | ☐ |
| 14 | FIXTURE | 12 CFR Part 30, App. D, II.A | "covered bank board is responsible for the bank's risk-governance framework." | ☐ |
| 15 | PLACEHOLDER | "Reform lever D8 memorandum" | reliance-accommodation reform text | ☐ keep as placeholder |

**Corrections (if any):** *(write here — e.g., "#8 should cite 252.33(a)(1) not (a)")*

---

## Item 2 — The statutory floor (duties no consolidation may delete)

Current draft list (5 anchors). The invariant: nothing may REPEAL or MERGE-away these; DEEM_SATISFIED against them is allowed but always flagged for review.

| # | Citation | What it protects | Keep? |
|---|---|---|---|
| 1 | 12 U.S.C. 5365(h) | Dodd-Frank §165(h) — BHC risk committee | ☐ |
| 2 | 12 U.S.C. 5365(i) | §165(i) — company-run stress testing, board oversight | ☐ |
| 3 | SOX §301 (15 U.S.C. 78j-1(m)) | Audit committee independence & responsibilities | ☐ |
| 4 | FDI Act §36 (12 U.S.C. 1831m) + Part 363 | Annual independent audit, ICFR, audit committee | ☐ |
| 5 | 31 U.S.C. 5318(h); 12 U.S.C. 1818(s) | BSA/AML compliance program | ☐ |

**Questions for you:**
- Anything missing? Candidates to consider: DFA §165(d) resolution planning (board approval of the plan); SOX §302/§404(a) certifications; FDICIA §112 lineage items beyond §36; anything from the incentive-comp statute (DFA §956) given its unfinalized status.
- Should any anchor be *narrowed* (e.g., §165(i) protects board oversight of stress testing generally — is that the right scope, or only the statutory minimum)?

**Your additions/removals:** *(write here)*

---

## Item 3 — How the spreadsheet columns were translated (227 imported drafts)

The importer read your inventory xlsx and translated free-text columns into typed fields using these rules. Confirm or correct each rule:

| Rule | Translation | Judgment calls to confirm |
|---|---|---|
| 1. Legal force | "examination manual"→manual · "enforceable guideline"→enforceable_guideline · "statute"→statute · "regulation"→regulation · **anything else→guidance** | (a) Rows marked "Regulation / enforceable (cross-listed)" map to **regulation** — right? (b) Rows marked "Rating framework" (GOV-18/19) fall through to **guidance** — right, or do rating frameworks deserve their own treatment? |
| 2. Cadence | "annual"→annual · "quarterly"→quarterly · "event-driven"→event_driven · "periodic/ongoing"→continuous · else→none_specified | "Periodic / ongoing" collapsing to one bucket ("continuous") loses the periodic-vs-ongoing distinction — acceptable for drafts? |
| 3. Currency | "rescinded"→rescinded_formal · "superseded"→superseded · "proposed/proposal"→stale_unverified · else→active | Should "rescinded" default to rescinded_**informal** instead, given the corpus finding that most retirements are informal? |
| 4. Entity | "both/&"→both · "IDI"→IDI · "BHC/issuer"→BHC · **blank→both** | Blank defaulting to "both" is the conservative choice (duty presumed to bind everywhere) — confirm. |
| 5. Confidence | High→0.9 · Medium→0.6 · Low→0.3 · blank→0.5 | OK? |
| 6. Consequence | "enforcement"→enforcement_action · "disclosure"→public_disclosure · "certif…"→certification_required | OK? |

**Your corrections:** *(write here)*

---

## Items 4 & 5 — nothing for you to do

- **Item 4 (primitive-count prose fix)** and **Item 5 (git commit of the project documents)** are mechanical. Tell Claude "do items 4 and 5" and they're done.

## When you're finished

Tell Claude your answers (chat is fine — no need to save this file, though you can). Claude will apply every edit, re-run the full test suite to confirm nothing broke, and mark the checkpoints resolved. Then B1 (citation verification) is unblocked.
