"""B5-T7 — corpus eval + report.

Assembles the B5 report: the corpus verification/distillation/classification funnel, the
lever-decomposition closure result (did the 16-primitive set hold at corpus scale?), the
citation-integrity gate (must remain 0.0 — every EMITTED claim is anchored; the two unanchored
diagnostics were dropped, not passed through), a stability spot-check on one new wave, the LLM
budget, and the full checkpoint list.
"""

from __future__ import annotations

from typing import Any

from adapters.distill import DistilledDuty, anchor_failures


def corpus_funnel(
    corpus_rows_status: list[str],
    distilled_counts: dict[str, int],
    findings_counts: dict[str, int],
) -> dict[str, Any]:
    verified = sum(1 for s in corpus_rows_status if s == "verified")
    return {
        "rows": len(corpus_rows_status),
        "verified": verified,
        "unverified": sum(1 for s in corpus_rows_status if s == "unverified"),
        "contradicted": sum(1 for s in corpus_rows_status if s == "contradicted"),
        "distilled": sum(distilled_counts.values()),
        "distilled_by_source": distilled_counts,
        "classified_findings": sum(findings_counts.values()),
        "findings_by_source": findings_counts,
    }


def closure_result(decomp_doc: dict[str, Any]) -> dict[str, Any]:
    by_status = decomp_doc["counts"]["by_status"]
    residuals = decomp_doc["residual_checkpoints"]
    return {
        "levers": decomp_doc["counts"]["levers"],
        "by_status": by_status,
        "clean": by_status.get("valid_single", 0) + by_status.get("valid_composite", 0),
        "residuals": len(residuals),
        "residual_levers": [r["lever_id"] for r in residuals],
        "sixteen_primitive_set_held_trivially": len(residuals) == 0,
        "note": (
            "The 16-primitive set expressed every clean lever as a single primitive or a known "
            "composite. The residuals are LLM-declared closure checkpoints (propose, never add) — "
            "several likely reduce to a known composite on human review; no primitive was added."
        ),
    }


def citation_integrity_b5(
    wave_distilled: dict[str, dict[str, Any]],
    wave_findings: dict[str, dict[str, Any]],
    wave_excerpts: dict[str, dict[str, str]],
) -> dict[str, Any]:
    """Every EMITTED anchored claim must resolve to its excerpt. Distilled rows are all
    anchor-clean by construction; the unanchored diagnostics were dropped (counted separately as
    a quality signal, not a gate failure — they never reached a finding)."""
    distill_total = 0
    distill_fail = 0
    dropped_unanchored = 0
    for wave, doc in wave_distilled.items():
        excerpts = wave_excerpts.get(wave, {})
        for row in doc["rows"]:
            d = DistilledDuty.model_validate(row["distilled"])
            for name in ("verb_evidence", "object_evidence", "cadence_evidence"):
                if getattr(d, name):
                    distill_total += 1
            distill_total += sum(1 for x in d.definitions_used if x.quote)
            distill_total += sum(1 for x in d.elements if x.quote)
            distill_fail += len(anchor_failures(d, excerpts.get(row["duty_id"], "")))
    for doc in wave_findings.values():
        dropped_unanchored += len(doc.get("anchor_failures", []))
    return {
        "distilled_anchored_claims": distill_total,
        "distilled_anchor_failures": distill_fail,
        "emitted_unanchored_claims": distill_fail,  # dropped diagnostics never reach a finding
        "dropped_unanchored_diagnostics": dropped_unanchored,
        "hallucinated_citation_rate": round(distill_fail / max(distill_total, 1), 4),
        "release_gate": "PASS" if distill_fail == 0 else "FAIL",
    }


def report_md(
    funnel: dict[str, Any],
    closure: dict[str, Any],
    integrity: dict[str, Any],
    stability: dict[str, Any] | None,
    budget_note: str,
    checkpoints: list[str],
) -> str:
    parts = [
        "# B5 report — the corpus scale-out\n",
        "> The proven per-cluster pipeline (verify → distill → diagnose → classify → decompose "
        "→ render → roll-up) run over the ~155 non-MVP duty rows and folded into the corpus-wide "
        "product. No new methods, no new primitives, no scope growth — novelty was a checkpoint, "
        "not a feature.\n",
        "\n## Corpus funnel\n",
        f"- **{funnel['rows']} rows → {funnel['verified']} verified "
        f"({funnel['verified'] / funnel['rows']:.0%}) → {funnel['distilled']} distilled → "
        f"{funnel['classified_findings']} findings.**\n",
        f"- verified {funnel['verified']} · unverified {funnel['unverified']} · **contradicted "
        f"{funnel['contradicted']}** (the three B2-era false contradictions were a range-parsing "
        "bug, fixed in B5-T2).\n",
        f"- distilled by source: {funnel['distilled_by_source']}; findings by source: "
        f"{funnel['findings_by_source']}.\n",
    ]

    parts.append("\n## Lever-decomposition closure result\n")
    parts.append(
        f"- **{closure['levers']} levers** (MVP D1-D9 + 22 B5): {closure['clean']} clean "
        f"(single primitive or known composite), "
        f"{closure['by_status'].get('documented_non_target', 0)} documented non-targets, "
        f"**{closure['residuals']} residual checkpoints**.\n"
        f"- The 16-primitive set held for every clean lever; it did **not** trivially express "
        f"the {closure['residuals']} residuals ({', '.join(closure['residual_levers'])}) under "
        "one conservative LLM pass — recorded as checkpoints (propose, never add a primitive).\n"
        f"- {closure['note']}\n"
    )

    parts.append("\n## Citation-integrity gate\n")
    parts.append(
        f"- distilled anchored claims: {integrity['distilled_anchored_claims']} · "
        f"anchor failures: {integrity['distilled_anchor_failures']}\n"
        f"- **hallucinated-citation rate: {integrity['hallucinated_citation_rate']} — gate "
        f"{integrity['release_gate']}.**\n"
        f"- {integrity['dropped_unanchored_diagnostics']} unanchored diagnostic(s) were caught "
        "and DROPPED (never reached a finding) — a quality signal, not a gate failure.\n"
    )

    parts.append("\n## Stability spot-check (one new wave)\n")
    if stability:
        parts.append(
            f"- wave `{stability['wave']}`, distill stage, {stability['rows_sampled']} rows × "
            f"{stability['samples']} samples: verb-standard agreement "
            f"{stability['verb_agree']}/{stability['rows_sampled']}, cadence agreement "
            f"{stability['cadence_agree']}/{stability['rows_sampled']}.\n"
        )
    else:
        parts.append(
            "- (stability samples not drawn in this run; see B3 eval for the MVP-stage checks)\n"
        )

    parts.append("\n## Budget\n")
    parts.append(f"- {budget_note}\n")

    parts.append("\n## Checkpoints (open items for the human — full list)\n")
    parts.extend(f"{i}. {c}\n" for i, c in enumerate(checkpoints, 1))
    parts.append(
        "\nAll open items are consolidated with recommendations in `../REVIEW_PACKET_B5.md` "
        '("accept all recommendations" answerable in one line).\n'
    )
    return "\n".join(parts)
