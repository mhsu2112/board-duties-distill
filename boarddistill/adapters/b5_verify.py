"""B5-T2 — per-wave verification.

Runs the same B1/B2 verify chain (the composite eCFR / U.S.C. / SR / SR-attachment / manual
resolver, allowlist unchanged) over each wave's rows. Same discipline as B1: a citation that
resolves and supports the duty ⇒ ``verified`` with a pinned span; unreachable/ambiguous ⇒
``unverified`` with a reason (never guessed); a citation that resolves to text contradicting the
duty ⇒ ``contradicted`` — a wave-halting checkpoint (§2.1).

Deterministic + cache-replayable: ``--live`` populates ``data/sources``; the default replays
from cache. Every wave writes ``outputs/b5/<wave>/verification.json`` + ``review_queue.json``.
"""

from __future__ import annotations

from collections import Counter
from typing import Any

from distillcore.pipeline.verify import RowVerification, SourceResolver, verify_targets


def wave_row_ids(wave_doc: dict[str, Any]) -> list[str]:
    return sorted(r for rows in wave_doc["clusters"].values() for r in rows)


def wave_targets(wave_doc: dict[str, Any], drafts: dict[str, Any]) -> list[dict[str, Any]]:
    return [drafts[i] for i in wave_row_ids(wave_doc) if i in drafts]


def verify_wave(
    wave_doc: dict[str, Any], drafts: dict[str, Any], resolver: SourceResolver
) -> list[RowVerification]:
    return verify_targets(wave_targets(wave_doc, drafts), resolver)


def wave_payload(wave_slug: str, rows: list[RowVerification]) -> dict[str, Any]:
    spans = [r.verdict.span.model_dump(mode="json") for r in rows if r.verdict.span is not None]
    summary: dict[str, int] = dict(Counter(r.record.status for r in rows))
    contradicted = sorted(r.duty_id for r in rows if r.record.status == "contradicted")
    return {
        "_meta": f"B5-T2 verification for wave {wave_slug}. Same resolver stack and allowlist as "
        "B1/B2; verified rows carry a pinned span, non-verified rows carry a reason. A "
        "contradicted row halts the wave (checkpoint).",
        "wave": wave_slug,
        "records": [r.record.model_dump(mode="json") for r in rows],
        "spans": spans,
        "rows": [
            {
                "duty_id": r.duty_id,
                "cluster": r.cluster,
                "citation": r.citation,
                "status": r.record.status,
                "as_of_valid": r.verdict.as_of_valid,
                "support_signal": r.verdict.support_signal,
                "anchor_matched": r.verdict.anchor_matched,
                "note": r.verdict.note,
            }
            for r in rows
        ],
        "summary": summary,
        "contradicted": contradicted,
    }


def wave_review_queue(wave_slug: str, rows: list[RowVerification]) -> dict[str, Any]:
    """Every non-verified row (the human TODO list), plus any currency/anchor flags on verified
    rows worth a look."""
    items: list[dict[str, Any]] = []
    for r in rows:
        flag: str | None = None
        if r.record.status != "verified":
            flag = r.record.status
        elif not r.verdict.as_of_valid:
            flag = "currency"
        if flag is None:
            continue
        items.append(
            {
                "duty_id": r.duty_id,
                "cluster": r.cluster,
                "citation": r.citation,
                "flag": flag,
                "note": r.verdict.note,
            }
        )
    counts = dict(Counter(i["flag"] for i in items))
    return {
        "_meta": f"B5-T2 review queue for wave {wave_slug}: non-verified rows and currency flags.",
        "wave": wave_slug,
        "counts": counts,
        "items": sorted(items, key=lambda i: i["duty_id"]),
    }
