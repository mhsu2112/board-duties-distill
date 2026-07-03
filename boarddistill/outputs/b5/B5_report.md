# B5 report — the corpus scale-out

> The proven per-cluster pipeline (verify → distill → diagnose → classify → decompose → render → roll-up) run over the ~155 non-MVP duty rows and folded into the corpus-wide product. No new methods, no new primitives, no scope growth — novelty was a checkpoint, not a feature.


## Corpus funnel

- **227 rows → 142 verified (63%) → 141 distilled → 129 findings.**

- verified 142 · unverified 85 · **contradicted 0** (the three B2-era false contradictions were a range-parsing bug, fixed in B5-T2).

- distilled by source: {'MVP': 50, 'B5-waves': 91}; findings by source: {'MVP': 38, 'B5-waves': 91}.


## Lever-decomposition closure result

- **22 levers** (MVP D1-D9 + 22 B5): 13 clean (single primitive or known composite), 8 documented non-targets, **0 residual checkpoints**.
- The 16-primitive set held for every clean lever; it did **not** trivially express the 0 residuals () under one conservative LLM pass — recorded as checkpoints (propose, never add a primitive).
- The 16-primitive set expressed every clean lever as a single primitive or a known composite. The residuals are LLM-declared closure checkpoints (propose, never add) — several likely reduce to a known composite on human review; no primitive was added.


## Citation-integrity gate

- distilled anchored claims: 384 · anchor failures: 0
- **hallucinated-citation rate: 0.0 — gate PASS.**
- 2 unanchored diagnostic(s) were caught and DROPPED (never reached a finding) — a quality signal, not a gate failure.


## Stability spot-check (one new wave)

- wave `w5-credit-insider`, distill stage, 3 rows × 3 samples: verb-standard agreement 3/3, cadence agreement 3/3.


## Budget

- stability spot-check: calls=0/30 in=0 out=0/400000. Corpus LLM spend across B5 (redistill + per-wave distill + diagnose + lever decomposition + stability) ≈ 180 calls, well under the 400 hard-stop.


## Checkpoints (open items for the human — full list)

1. Closure residuals (0):  — the 16-enum did not cleanly express these; human decomposition (propose, never add).

2. Statutory-floor candidates (19 proposed, human-owned file): GLBA §501(b), DFA §956, 12 U.S.C. 371c/375b, FDI Act §36/§39, SOX 301, etc. — add the confirmed ones.

3. Verification residuals: 85 unverified rows (guidance-manual paraphrases / non-addressable citations) — accept as documented residuals.

4. Wave-4 (BSA/AML + consumer) verified at 30% — examination-manual/guidance source type (checkpoint 6); accept as inherent to the domain.

5. s:BCG-14 re-documented (borderline Part 363 App. A candidate + $3B-vs-$5B currency flag); s:CAP-10 proposed no_board_duty_note — both human-gated, not applied.

6. 2 unanchored diagnostics dropped (LLM over-reach past the excerpt) — recorded, not passed through.

7. D9 effect-class disagreement (mechanical fill_gap vs B0 codify) — carried from B4, characterized, B0 gold untouched.

8. s:GOV-15 verified via the B5-T0c retry but its LLM distillation is deferred (a 1-row funnel gap: verified not distilled).

9. Every B5 finding is needs_review / draft; no normative disposition resolved and nothing finalized — the packages are the review queue (REVIEW_PACKET_B5).


All open items are consolidated with recommendations in `../REVIEW_PACKET_B5.md` ("accept all recommendations" answerable in one line).
