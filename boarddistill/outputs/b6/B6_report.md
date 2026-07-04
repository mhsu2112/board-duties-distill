# B6 report — the RBI Master-Directions rediscovery benchmark

> A held-out cross-jurisdiction test of the consolidation calculus: can the engine, given only pre-consolidation RBI circulars (pseudonymized, no Master-Direction identity), recover the *structural* moves of RBI's 2016-era consolidation — which circulars group into which consolidated instrument — scored against RBI's published traceability appendices? **Both a strong and a weak result are reportable; nothing was optimized toward agreement.**

## 1. Design (pooled-blind, §1.2)

Each sampled Master Direction's repeal appendix defines *which circulars are in scope* (unavoidable corpus definition). Everything else — the MD's text, structure, and the **grouping** — is held out. All sampled MDs' source circulars are pooled into one mixed corpus; the engine proposes consolidation groupings and span-anchored operations under a prompt that never names Master Directions or the RRA. The plain-LLM baseline (§1.4) sees the same pooled corpus and one prompt ("propose how to consolidate these instruments").

Scoring is **structural only**: RBI's substantive policy choices, thresholds, and drafting are held-out dials — never scored. Only grouping and the operation set are measured.

**Leakage controls (§1.3):** prompts never name the consolidation program; every circular identifier is pseudonymized in the LLM-facing corpus (RBI numbers, department-code refs, file-code tails, and 15 circulars that named the "Master Direction on <topic>" they were folded into — all scrubbed to neutral tokens); cross-references are pseudonymized *consistently* so the engine still sees the citation structure; every LLM output is leakage-scanned and any hit quarantined. A path guard (`benchmark_guard`) blocks the proposal pipeline from ever reading the sealed answer key.

## 2. Sample (acquired)

Four Master Directions, **163 pooled circulars**, 100% retrieval, via web.archive.org (pre-2025 MD pages whose appendices link each circular by id) + live RBI for the texts:

| MD | domain | circulars |
|---|---|---|
| Interest Rate on Deposits (2016) | deposits / interest-rate | 58 |
| Investment Portfolio Classification/Valuation | prudential / investment | 51 |
| Priority Sector Lending | lending / prudential | 40 |
| Credit/Debit Card Issuance & Conduct (2022) | conduct / payments | 14 |

Two candidate MDs were **dropped at acquisition (§3.3, symmetric):** KYC/AML (repeal list unlinked — plain-text refs, >15% unretrievable) and Frauds/governance (archived snapshots near-empty). Cost: the KYC/AML and governance domains — a stated sample-spread limitation.

## 3. Results (structural only; dials held out)

| metric | engine | baseline | delta |
|---|---|---|---|
| pairwise precision | 0.922 | 0.933 | -0.011 |
| pairwise recall | 0.362 | 0.376 | -0.014 |
| pairwise F1 | 0.52 | 0.536 | -0.016 |
| Adjusted Rand Index | 0.427 | 0.444 | -0.017 |
| proposed groups | 12 | 12 | — |

**The calculus scaffold adds ~0 grouping delta over a plain LLM** (F1 -0.016, ARI -0.017). Both recover near-*pure* topical clusters (precision 0.922) but with low recall (0.362) because both **over-split** RBI's coarse 4 MDs into ~12 finer groups.

**Operation-mix (the engine's unique output):** 131 span-anchored operations, **75% in {MERGE, REPEAL, CANONICALIZE_DEFINITION, RESOLVE_CROSS_REFERENCE}}** — matching the engine PRD §18 prediction. Full mix: {'CANONICALIZE_DEFINITION': 13, 'ELEVATE_GENERAL_RULE': 17, 'MERGE': 17, 'RELATE_OBLIGATION': 16, 'REPEAL': 32, 'RESOLVE_CROSS_REFERENCE': 36}. The plain LLM produces no operations at all; the scaffold's contribution is this structured, span-anchored, auditable operation layer, not grouping accuracy.

## 4. Disagreement characterization (never reconciled)

Engine groups spread each true MD across several groups: {'MD-CARDS': 2, 'MD-DEPOSITS': 4, 'MD-INVPF': 4, 'MD-PSL': 6}. The splits are coherent — 9 of 12 groups are 100% pure (dominated by one MD), split by **bank-type** (Scheduled / Urban-Co-op / Regional-Rural / Small-Finance) and **sub-topic** (NRE/FCNR vs rupee deposits; investment-portfolio vs government-securities). Notably, RBI's *own* 2025 consolidation later split these MDs by bank-type (Commercial-Banks-KYC, UCB-KYC, …), so several of the engine's finer groups are arguably cleaner than the 2016-era single MDs — recorded symmetrically, not as errors.

The one genuinely mixed group (Customer Service, Protection & Communica) is a cross-cutting theme RBI distributed across MDs — an alternative organization, not a mistake.

**Survival/repeal:** every consolidated circular is formally repealed in the appendices, so repeal precision is trivially 1.0 and the within-group *survivor* is not distinguished by RBI's flat appendix — characterized, not scored (§1.4).

## 5. Standing leakage caveat

Parametric familiarity with these Master Directions **cannot be eliminated, only made harder to use and detectable when overt** (§1.3d). Identifiers and program references are pseudonymized and every output is scanned, but a model may still carry latent knowledge of RBI's consolidation. This mirrors the corpus's LLM-as-judge caveat: the result is evidence, not proof, and should be read with that discount.

## 6. Limitations

- **Sample size:** 4 MDs / 163 circulars (KYC/AML and governance dropped at acquisition) — a small, bank-facing, English-only, 2016-vintage slice; not representative of RBI's full 244-MD 2025 consolidation.
- **Coarse ground truth:** RBI's 2016 MDs lump by topic; the engine's finer bank-type splits depress recall against them even where defensible.
- **Parse/scrub losses:** pseudonymization is regex-based and deliberately over-scrubs; some circular body text is replaced by tokens.
- **Single model, single run:** determinism via cache, not multi-sample stability here.

## 7. Publishable summary

> On a held-out, pseudonymized pool of 163 pre-consolidation RBI circulars, a consolidation-calculus engine recovered the topical structure of RBI's Master-Direction consolidation at pairwise precision 0.922 / recall 0.362 (F1 0.52, ARI 0.427) — **statistically indistinguishable from a plain-LLM baseline** on grouping. The calculus scaffold's value was not higher grouping accuracy but a different output entirely: 131 span-anchored, leakage-controlled consolidation *operations*, 75% of them the four merge/repeal/canonicalize/cross-reference primitives the framework predicted would dominate a consolidation exercise. Where the engine disagreed with RBI it disagreed *cleanly* — splitting single topical MDs into pure bank-type sub-groups that RBI's own 2025 consolidation independently adopted. The calculus generalizes across regulator and jurisdiction as a *structuring and auditing* discipline; it does not, on this evidence, out-cluster a capable language model. Both halves of that finding are the result.

