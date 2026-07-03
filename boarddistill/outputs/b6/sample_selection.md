# B6-T1 — RBI Master-Directions sample selection (DRAFT, pending human sign-off)

> **CHECKPOINT (B6_TASKS §3.1): human sign-off required BEFORE mass download.**
> Nothing has been mass-downloaded. A single reachability probe of the RBI Master-Directions
> **list** page confirmed `rbi.org.in` is retrievable from this environment (~58 MDs on one
> category page); no source circulars and no traceability appendices (answer keys) were fetched.
> This memo proposes the sample for your sign-off; on approval, T1 proceeds to acquisition
> (sealed answer key under `data/benchmark/answer_key/`, guarded in code).

## What you're approving

A pooled-blind rediscovery benchmark (§1.2): the engine, on a **mixed pool** of the selected
MDs' source circulars — with every MD's identity, text, structure, and grouping held out — tries
to recover *which circulars group into which consolidated instrument, what is repealed, what
survives*. Scored against RBI's published traceability appendices as the answer key. **RBI's
substantive policy choices are never scored** (held-out dials).

## Proposed sample (7 candidates → target 5–7 after acquisition)

| MD | Domain | Traceability appendix | Est. circulars | Why |
|---|---|---|---|---|
| KYC Direction, 2016 | KYC/AML | yes (Repeal section) | 40–80 ⚠ large | canonical AML consolidation; the domain the PRD names first |
| Investment Portfolio (Classification/Valuation), 2023 | prudential (investment) | yes (repeal annex) | 25–40 | clean prudential consolidation, mid-size |
| Interest Rate on Deposits, 2016 | deposits / interest-rate | yes (appendix) | 30–50 | the deposits/interest-rate domain (§1.1c) |
| Fraud Risk Management in Commercial Banks, 2024 | governance / conduct | yes (repeals Master Circular on Frauds) | 15–30 | board/audit-committee fraud oversight; recent, clean repeal list |
| Priority Sector Lending, 2020 | lending / prudential | yes (appendix) | 30–50 | second prudential/lending domain; well-mapped |
| Credit/Debit Card Issuance & Conduct, 2022 | conduct / payments | yes (repeals card circulars) | 15–30 | compact conduct/payments consolidation |
| Digital Payment Security Controls, 2021 | cyber / IT | partial ⚠ | 10–20 | cyber/IT spread; **candidate to DROP** if repeal list too thin to score |

**Domain spread (§1.1c) satisfied:** KYC/AML ✓, prudential/exposure ✓ (Investment Portfolio + PSL),
deposits/interest-rate ✓, governance/fit-and-proper ✓ (Fraud governance). Cards + DPSC add conduct
and cyber breadth.

## Rejected candidates (sample-bias transparency, §1.1)

- **FEMA Compounding MD** — a regulatory-*process* direction; no consolidation of subject-matter
  circulars into groupings, so nothing to rediscover.
- **Rupee Interest Rate Derivatives / Credit Derivatives / Electronic Trading Platforms** — narrow
  market-infrastructure MDs; source-circular sets below the ~10–80 target, far from board-duty
  domains.
- **Operational Guidelines for Primary Dealers** — niche market-participant scope.
- **NBFC-facing MDs** (IT Framework, Auditor's Report, Fraud Risk in NBFCs) — different regulated-
  entity class; excluded to keep the pooled corpus comparable to the bank-facing set (a deliberate
  comparability choice, not a quality judgment).
- **Internal Ombudsman for Regulated Entities, 2023** — thin repeal list, weak grouping signal.

## Known risks (to confirm on acquisition, symmetrically)

1. **KYC size** may exceed the 80-circular target — if so, trim to the core AML/KYC circular set
   and record the trim.
2. **DPSC answer-key thinness** — if its repeal list is too thin to score, DROP it and remove its
   circulars from **both** the corpus and the answer key (§1.1).
3. **English-only, bank-facing, 2016–2024 vintage** — stated limitations; NBFC deliberately
   excluded for comparability.
4. Any circular that cannot be retrieved is dropped from scope **and** the answer key symmetrically.

## Sign-off

`TODO(human): approve / amend this sample (which MDs, and whether to drop DPSC).` On approval,
T1 acquires the traceability appendices into the sealed `data/benchmark/answer_key/` (path-guarded
against the proposal pipeline in `adapters/benchmark_guard.py`) and the source circulars into
`data/benchmark/corpus/`, under B1 cache/manifest discipline. **Not started — awaiting sign-off.**

---

## Acquisition outcome (post-sign-off, 2026-07-03)

Acquired via web.archive.org (pre-2025 MD pages whose repeal appendices link each consolidated
circular by Id) + live rbi.org.in for the circular texts. **163 circulars, 100% retrieval, 0
missed:**

| MD | domain | circulars |
|---|---|---|
| MD-DEPOSITS (Interest Rate on Deposits, 2016) | deposits / interest-rate | 58 |
| MD-INVPF (Investment Portfolio Classification/Valuation) | prudential / investment | 51 |
| MD-PSL (Priority Sector Lending) | lending / prudential | 40 |
| MD-CARDS (Credit/Debit Card Issuance & Conduct, 2022) | conduct / payments | 14 |

**Dropped at acquisition (§3.3, symmetric):** MD-KYC (repeal appendix lists circulars as
plain-text references — unlinked, >15% unretrievable by Id) and MD-FRAUDS (archived snapshots
near-empty). **Cost: the KYC/AML and governance/fraud domains** — a stated sample-spread
limitation; the four acquired MDs still span deposits, prudential/investment, lending, and
conduct. Answer key sealed at `data/benchmark/answer_key/grouping.json` (circular→MD, plus
per-circular metadata, both held out); pooled corpus at `data/benchmark/corpus/` (163 texts).
