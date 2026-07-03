# B5_TASKS.md — Scale-out: the remaining ~27 clusters → the corpus-wide consolidation product

**Audience:** an autonomous coding agent (Claude Code terminal). All prior contracts remain binding: `AGENTS.md` (invariants, checkpoints), `B1_TASKS.md` §3 (retrieval allowlist + cache discipline), `B3_TASKS.md` §§1–2 (LLM harness rules; span-anchoring; unresolved-over-guess), `B4_TASKS.md` outcomes (16-primitive enum, two duplication families, concept-node graph pattern, dominant-effect classifier).

**Human authority (M. Hsu, 2026-07-02, via chat):** scale-out approved for the full remaining corpus. The B4 carry-forwards are folded in here (§1 T0). **Requires `ANTHROPIC_API_KEY`** for the distill/diagnose passes — if absent, stop at T0 with the usual `TODO(human)`.

**Mission:** run the proven per-cluster pipeline — verify → distill → diagnose → classify → render — over the ~155 duty rows outside the MVP clusters, decompose the remaining reform levers into operations, and roll everything up into the **corpus-wide product**: per-cluster packages, a master duty crosswalk, a ranked reform roadmap, and one consolidated review packet for the human. This is crank-turning by design: **no new methods, no new primitives, no scope growth** — novelty is a checkpoint, not a feature.

---

## 1. Build order (commit per task; per-wave commits inside T2–T5)

- **B5-T0 Carry-forwards.** (a) Live re-distill of the ten B4-re-pinned rows (`b3-distill --live`, then cache). (b) D7 disposition-rule refinement: read strata *through concept groundings* so cross-stratum operands on concept refs default `needs_review` (the B4 characterized limitation); regression test. (c) Retry the three B2 residuals the better resolvers may now reach (`s:GOV-15`, `s:CAP-10`, `s:BCG-14`); leave the rest as accepted residuals. *DoD:* ten rows distilled; D7 disposition now `needs_review`; retries resolved or re-documented.

- **B5-T1 Wave plan.** Partition the ~155 non-MVP rows into **waves by domain** (expected: liquidity · resolution/recovery · operational resilience & cyber · model risk · third-party · incentive compensation · BSA/AML · consumer compliance · credit & lending · governance/misc). Write `outputs/b5/waves.json` (wave → cluster → row IDs, deterministic). Target 4–7 waves of manageable size. *DoD:* every non-MVP row in exactly one wave; counts printed.

- **B5-T2 Per-wave verification.** For each wave: run the full B1/B2 verify chain (eCFR / U.S. Code / appendix / SR-attachment / manual resolvers, allowlist unchanged, cache/manifest discipline). New instruments get graph nodes (stratum, treatment, evidence — including Wayback `rescinded_informal` where needed). Expected pattern per MVP experience: most binding-layer rows verify; guidance-layer paraphrases yield documented residuals — **record, never force**. Any `contradicted` claim halts that wave pending the review packet. *DoD per wave:* every row has an evidenced status; graph extended; committed.

- **B5-T3 Per-wave distill + diagnose + classify.** LLM distill of verified rows (span-anchored; unresolved over guess; verb-vs-actor cross-check active); diagnostics in both duplication families plus undefined-term / actor-ambiguity / restatement kinds; mechanical classifier with graph-aware target selection and dominant-effect rule. Budget guard: set a per-wave call ceiling and a corpus total (~250 calls expected; hard-stop at 400 with checkpoint). *DoD per wave:* findings with effect classes and default dispositions; zero unanchorable claims.

- **B5-T4 Lever decomposition (the B0 method, LLM-assisted, human-gated).** The Duplicate Clusters sheet's remaining "minimum reform levers" (~22 beyond the MVP five) and the unconsumed Reform Roadmap rows (e.g., resilience-planning integration, GLBA information-security consolidation, DFA §956 resolution, third-party threshold, tiering) are decomposed into operation compositions — LLM proposes, `validate_composition()` enforces the 16-enum and known composites. Concept operands get grounded concept nodes (B4-T4 pattern). **Any residual the enum cannot express: checkpoint, propose, never add** (this is the live test of B0's closure claim at corpus scale). Statutory-floor candidates encountered in new domains (e.g., GLBA §501(b), DFA §956, 12 U.S.C. 371c for insider/affiliate) are **proposed as floor additions, not added** — the floor file is human-owned. *DoD:* every lever decomposed or checkpointed; composition validation green.

- **B5-T5 Per-wave packages.** Render each wave's clusters into `outputs/b5/<wave>/<cluster>/package.md` (full §9 contents, both duplication-family tables, authority-to-act, blocker summary). *DoD:* all clusters render; nothing final.

- **B5-T6 Corpus roll-up (the product).** Build, from *all* clusters (MVP + B5):
  - `outputs/b5/corpus/master_crosswalk.md` — every duty row → its cluster, verification status, proposed operation(s), intended home;
  - `outputs/b5/corpus/reform_roadmap_v2.md` — every decomposed lever with effect class, normative kinds, `actor_with_authority`, `instrument_required`, statutory obstacles, and a **feasibility ranking** ordered by the inventory's own tiering principle (guidance consolidation → guidance retirement → rule harmonization → vertical rationalization → statutory), each row traceable to its package;
  - `outputs/b5/corpus/corpus_stats.md` — verification rates by stratum, duplication-family counts, verb-standard coverage (the "unstated board-action standard" metric corpus-wide), residual taxonomy;
  - `../REVIEW_PACKET_B5.md` (corpus folder) — **one consolidated decision packet** in the REVIEW_PACKET_B3 format: per-wave queues rolled up, every item with a recommendation, "accept all recommendations" answerable in one line.
  *DoD:* four artifacts; every claim in them traceable to a package or cache entry.

- **B5-T7 Eval + report.** `outputs/b5/B5_report.md`: corpus verification funnel (rows → verified → distilled → classified), lever-decomposition closure result (did the 16-primitive set hold at corpus scale?), citation-integrity gate (must remain 0.0), stability spot-check on one new wave, budget spent, and the full checkpoint list. README updated; suite green from cache. *DoD:* all committed.

## 2. Checkpoints (stop, `TODO(human)`, leave a draft)

1. Any `contradicted` claim (halts its wave's advance to T3).
2. Any lever the 16-primitive enum cannot express — the closure test failing at scale would be a *finding*, handled by proposal.
3. Any proposed statutory-floor addition (human-owned file).
4. Any normative disposition; any budget hard-stop; any allowlist expansion; anything CSI-adjacent.
5. Concept nodes that cannot be grounded with span evidence.
6. A wave whose verification rate falls far below the MVP pattern (suggests a systematically different source type — surface before grinding on).

## 3. Definition of done

Every duty row in the corpus has an evidenced verification status; every verified row is distilled and classified; every reform lever is decomposed or checkpointed; the four corpus artifacts exist and are internally traceable; `REVIEW_PACKET_B5.md` is ready for M. Hsu; citation-integrity gate 0.0; `make check` green offline; all committed.

**After B5 and the human review pass, one arc remains: the RBI Master-Directions rediscovery benchmark — its own file, on M. Hsu's word. Do not start it.**

---

**Begin at B5-T0.**
