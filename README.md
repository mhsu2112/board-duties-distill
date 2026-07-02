# Bank Board "Policy Sludge" — Cumulative Project

A small, reproducible study that asks two linked questions:

1. **The policy question:** How much duplicative, overlapping, and unduly burdensome regulatory obligation actually sits on the boards of directors of the largest U.S. banks (Category I global systemically important bank holding companies, or GSIBs)? This accumulation of process-heavy, low-value requirements is what the project calls *policy sludge*.
2. **The methods question:** When you ask several frontier AI systems to compile a *citation-level inventory* of those obligations, how good — and how trustworthy — are the answers? Which models produce reliable, reform-ready work, and which produce polished text that falls apart under citation checking?

To answer the second question the project runs a **"horserace"**: the same research brief is given to multiple AI systems, and their reports are then graded by **multiple independent LLM judges** against a fixed, integrity-weighted rubric. The graded outputs are then distilled into a clean **synthesis** of board obligations intended to be useful to bank directors, their counsel, and policymakers working on regulatory-burden reduction.

This repository accompanies the related Substack write-up and is organized so a colleague or reader can follow the work end to end: the source reports, the evaluation tooling, the evaluation results, and the final synthesis.

---

## The research brief

Every model was given materially the same prompt (the full text lives in `Tools/sludge-report-evaluation-instructions.md`). In short:

> Compile a comprehensive, citation-level inventory of all current, in-force obligations imposed on boards of directors of Category I GSIB holding companies and their insured depository institution subsidiaries — drawn from Federal Reserve, OCC, FDIC, CFPB, and interagency sources — broken down by board structure (full board vs. audit/risk/compensation/governance committees; inside vs. outside vs. independent directors) and across every major regulatory domain (capital planning and stress testing, liquidity, resolution and recovery planning, operational resilience, model risk, third-party risk, incentive compensation, cybersecurity, BSA/AML, consumer compliance, and safety-and-soundness). For each obligation: the precise source, the nature of the duty, which actor it binds, and any director-class distinction. Audience: directors, counsel, and reform-minded policymakers. Target depth: ~40–60 pages.

Some follow-up runs used an *expanded* variant of this prompt; those are labeled `expanded-prompt` (vs. `original-prompt`) in the filenames.

---

## Repository structure

```
.
├── Reports/      Raw AI-generated reports (the things being graded)
│   ├── round-1-horserace/    First head-to-head: RegGenome, GPT-5.5, Opus-4.8, Caffrey
│   └── round-2-followups/    Later runs: GLM-5.2, Kimi, Iqidis, Opus, GPT, Codex
│                             (incl. multi-file bundles with their source corpus)
├── Tools/        The evaluation harness (rubric, judge prompt, scripts, instructions)
├── Evals/        Judge outputs + scored workbooks + summary tables
│   ├── round-1-horserace/    12 judge runs (3 judges × 4 reports) + scoring workbooks
│   ├── round-2-followups/    Judge runs on the later report set
│   └── judge-inputs/         The (de-identified) report text fed to the judges
└── Synthesis/    The distilled, cross-report inventories of GSIB board obligations
```

`_archive/` (superseded v1 artifacts and duplicates) is kept locally for provenance but **excluded from the public repository** via `.gitignore`.

---

## Methodology

### Producers (the AI systems under test)
RegGenome, OpenAI GPT-5.5, Anthropic Opus 4.8, "Caffrey," GLM-5.2, Kimi / Kimi-2.5, Iqidis, and Codex. Each produced one or more reports responding to the brief.

### Judges
Each report was graded independently by three LLM judges so that no single model's quirks dominate:

- **Claude Code** (with retrieval/file access)
- **Codex** (desktop, with verification where available)
- **Gemma 4 E4B** (run locally via Ollama; *no* browsing/retrieval — its citation-integrity scores are treated cautiously)

### The rubric (integrity-weighted)
Each report is scored 0–4 on six dimensions, then weighted to a 0–100 overall. Weights deliberately tilt toward source integrity, so a fluent report cannot earn a high headline number while its citations are unreliable:

| Dim | Dimension | Weight |
|----|-----------|:-----:|
| D1 | Coverage & Comprehensiveness | 20 |
| D2 | Source & Citation Integrity | **25** |
| D3 | Substantive Accuracy & Currency | 20 |
| D4 | Sludge-Analysis Quality | 15 |
| D5 | Structure, Granularity & Fitness-for-Purpose | 10 |
| D6 | Calibration & Transparency | 10 |

Integrity-bearing dimensions (D2 + D3) carry 45 of 100; with D6 the integrity-leaning total is 55.

### Flags and the reliability overlay
Separately from the numeric score, judges record binary integrity/scope flags, each requiring specific evidence:

`F1` fabricated source · `F2` misattribution · `F3` stale-presented-as-current · `F4` invented obligation · `F5` false exhaustiveness · `F6` scope evasion · `F7` unsupported central legal conclusion.

A *central* integrity flag zeros out its dimension and sets a **reliability overlay** (`Clean`, `INTEGRITY`, `SCOPE`, or `INTEG+SCOPE`). **The overlay overrides the numeric tier for reliance decisions:** any report marked `INTEGRITY` or `INTEG+SCOPE` should not be relied on regardless of its score or rank.

---

## Results at a glance — Round 1 horserace

Headline takeaways (see `Evals/` for the full per-dimension detail and flags):

- **Opus-4.8 and GPT-5.5 lead consistently** across all three judges and carry the cleanest integrity profiles.
- **Judges disagree in strictness, not in ranking.** Gemma (no retrieval) is the most generous, Codex the harshest. The *ordering* of reports is stable across judges even where the absolute numbers differ, which is the main reason for using three judges.

Round-2 follow-ups (expanded-prompt variants and additional models) are scored in `Evals/round-2-followups/` and the `Codex_judge` sheet of the summary workbook; several later runs drew integrity flags (e.g., invented obligations, stale-as-current), reinforcing the round-1 pattern that polish does not guarantee citation reliability.

> ⚠️ **Caveat on LLM-as-judge.** These scores are LLM judgments, not ground truth. Judges can both miss real citation errors and over-flag good ones. Treat the numbers as a directional, reproducible signal — and confirm any `FABRICATED`, `STALE`, or `Central` finding by hand before relying on it. Gemma's citation-integrity scores in particular are weak because it cannot retrieve sources.

---

## Reproducing the evaluation

Full step-by-step instructions are in `Tools/sludge-report-evaluation-instructions.md`. In outline:

1. Use the v2 evaluator artifacts in `Tools/` (rubric, judge prompt, reviewer protocol, scoring-workbook template).
2. Run one report per judge session against `policy-sludge-llm-judge-prompt-v2.md`, with `CITATION_SAMPLE_SIZE: 20` and the per-report sample seed.
3. Save each judge's JSON + markdown output (these are the audit trail; see `Evals/`).
4. Enter scores and flags into a per-judge copy of the scoring workbook; the workbook auto-computes effective scores, weighted overall, tier, overlay, and rank.
5. For the local Gemma judge, build the prompt packets and pipe them through Ollama (`Tools/Modelfile`, `Tools/run-gemma-evals.sh`).

---

## Notes and limitations

- **"Sludge" is a normative lens, not a legal conclusion.** The synthesis identifies candidate duplication and overlap; whether a given requirement *should* change is a policy judgment.
- **Producer labels** like "Caffrey," "RegGenome," and "Iqidis" refer to specific tools/configurations used in the runs; see the Substack post for context.
- **Not legal advice.** Nothing here is legal advice. Regulatory obligations change; verify against primary sources (many of which are included under `Reports/round-2-followups/codex_supervisory-expectations-inventory/sources/`) before acting.
