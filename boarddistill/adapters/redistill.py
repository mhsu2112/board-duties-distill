"""B5-T0(a) — live re-distill of the ten B4 re-pinned rows.

B3 distilled these ten rows against a pin that did not support the duty, so each resolved to
``none_specified`` / unresolved (the distiller refusing to invent structure — correct). B4-T2
corrected the pins (``outputs/b4/repins.json`` / :mod:`adapters.repin`); this module re-runs the
*same* distiller over each corrected excerpt so the ten rows carry real verb / object / cadence
structure, anchored to the corrected span. Live-then-cache: with ``ANTHROPIC_API_KEY`` set the
calls populate ``data/llm_cache``; every subsequent replay is byte-identical and offline.

The re-distilled rows are merged back into the MVP as-built corpus so the corpus roll-up rests
on the corrected structure. Discipline is unchanged: every asserted field must anchor to a
substring of the corrected excerpt (``anchor_failures``); nothing is overwritten silently and
nothing is finalized.
"""

from __future__ import annotations

from typing import Any

from adapters.distill import DistilledRow, DistillTarget, distill_target
from adapters.repin import REPINS, corrected_spans
from distillcore.llm import LlmHarness

# The ten rows, in the fixed B4-T2 order.
TEN_ROWS: list[str] = [r["duty_id"] for r in REPINS]


def build_redistill_targets(drafts: dict[str, Any]) -> list[DistillTarget]:
    """One :class:`DistillTarget` per re-pinned row, its excerpt = the corrected span quote."""
    spans = {s["id"]: s for s in corrected_spans()}
    targets: list[DistillTarget] = []
    for duty_id in TEN_ROWS:
        span = spans[f"repin-{duty_id}"]
        if duty_id not in drafts:
            raise ValueError(f"re-pinned row {duty_id} lacks a draft spec")
        targets.append(
            DistillTarget(
                duty_id=duty_id,
                draft=drafts[duty_id],
                excerpt=span["quote"],
                citation=span["citation"],
            )
        )
    return sorted(targets, key=lambda t: t.duty_id)


def redistill_all(
    harness: LlmHarness, drafts: dict[str, Any], retags: dict[str, Any]
) -> list[DistilledRow]:
    return [distill_target(harness, t, retags) for t in build_redistill_targets(drafts)]


def redistill_document(rows: list[DistilledRow]) -> dict[str, Any]:
    anchor_fail = sorted(r.duty_id for r in rows if not r.anchor_ok)
    conflicts = [r.retag_conflict for r in rows if r.retag_conflict]
    resolved = sorted(
        r.duty_id
        for r in rows
        if r.distilled.object.strip() and "object" not in r.distilled.unresolved_fields
    )
    return {
        "_meta": "B5-T0(a) re-distill of the ten B4 re-pinned rows against their corrected "
        "excerpts. Same distiller, corrected pins; every field anchored to the corrected span. "
        "Live-then-cache; nothing overwritten silently, nothing finalized.",
        "counts": {
            "rows": len(rows),
            "anchor_clean": sum(1 for r in rows if r.anchor_ok),
            "anchor_failures": len(anchor_fail),
            "object_resolved": len(resolved),
            "verb_retag_conflicts": len(conflicts),
        },
        "anchor_failure_rows": anchor_fail,
        "object_resolved_rows": resolved,
        "verb_retag_conflicts": conflicts,
        "rows": [
            {
                "duty_id": r.duty_id,
                "anchor_ok": r.anchor_ok,
                "anchor_failures": r.anchor_failures,
                "retag_conflict": r.retag_conflict,
                "distilled": r.distilled.model_dump(mode="json"),
            }
            for r in rows
        ],
    }


def merge_into_distilled(distilled_doc: dict[str, Any], rows: list[DistilledRow]) -> dict[str, Any]:
    """Return a copy of ``distilled_doc`` with the ten rows replaced by their re-distilled
    versions and the ``source_mismatch_rows`` count recomputed (the corrected pins clear them)."""
    by_id = {r.duty_id: r for r in rows}
    new_rows: list[dict[str, Any]] = []
    for row in distilled_doc["rows"]:
        r = by_id.get(row["duty_id"])
        if r is None:
            new_rows.append(row)
            continue
        new_rows.append(
            {
                "duty_id": r.duty_id,
                "anchor_ok": r.anchor_ok,
                "anchor_failures": r.anchor_failures,
                "retag_conflict": r.retag_conflict,
                "distilled": r.distilled.model_dump(mode="json"),
            }
        )
    doc = {**distilled_doc, "rows": new_rows}
    mismatch = sorted(
        row["duty_id"]
        for row in new_rows
        if not row["distilled"]["object"].strip()
        or "object" in row["distilled"]["unresolved_fields"]
    )
    anchor_fail = sorted(row["duty_id"] for row in new_rows if not row["anchor_ok"])
    counts = dict(doc.get("counts", {}))
    counts["source_mismatch_rows"] = len(mismatch)
    counts["anchor_failures"] = len(anchor_fail)
    counts["anchor_clean"] = sum(1 for row in new_rows if row["anchor_ok"])
    doc["counts"] = counts
    doc["source_mismatch_rows"] = mismatch
    doc["anchor_failure_rows"] = anchor_fail
    return doc
