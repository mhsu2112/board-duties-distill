"""B5-T0(c) — retry the three B2 residuals the better resolvers may now reach.

The B2 pass left 22 documented residuals (accepted). Three are worth one retry now that the
resolver stack is stronger and the SR 12-17 letter body is cached:

* ``s:GOV-15`` — SR 12-17 §A.2 corporate governance. B2 failed because the SR-attachment
  resolver found no attachment PDF; the new letter-body fallback anchor-matches the duty text
  inside the letter body itself. **Resolves** (verified, anchor-matched, span pinned).
* ``s:BCG-14`` — audit-committee composition for large IDIs. The duty's substance is in
  12 CFR Part 363 App. A, but the anchor is borderline **and** the duty carries a stale
  threshold (">$3 billion" vs the current "$5 billion"). **Re-documented** as a borderline
  candidate with a currency flag — stays ``unverified`` (never forced).
* ``s:CAP-10`` — "no board attestation on the FR Y-14A." A negative record whose real board
  instrument is the already-verified 12 CFR 225.8(e) / SR 15-18 capital-plan approval; FR Y-14A
  form instructions are not a primary-law source. **Re-documented** as a no-board-duty note
  (proposed reclassification, human-gated like s:CAP-11 — not applied here).

The rest of the 22 stay accepted residuals. Deterministic and cache-replayable; the retry runs
offline against the committed source cache.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from adapters.anchor import CANDIDATE_FLOOR, anchor_match
from adapters.repin import _cached_text
from adapters.resolvers import build_resolver
from adapters.retrieval import Fetcher, offline_client
from distillcore.pipeline.verify import verify_targets

RETRY_IDS: tuple[str, ...] = ("s:GOV-15", "s:CAP-10", "s:BCG-14")

_P363_SOURCE = "ecfr-t12-p363"
_P363_CITATION = "12 CFR Part 363, App. A, Guideline 27 (audit committee composition)"


def _rows_by_id(import_doc: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {d["duty_id"]: d for d in import_doc["duties"]}


def _bcg14_redoc(row: dict[str, Any]) -> dict[str, Any]:
    """Borderline candidate at Part 363 App. A + a currency flag (>$3B duty vs current $5B)."""
    score, window = anchor_match(row["object"], _cached_text(_P363_SOURCE))
    stale_threshold = "$3 billion" in row["object"] and "$5 billion" in window
    return {
        "duty_id": row["duty_id"],
        "outcome": "re-documented",
        "status": "unverified",
        "candidate_citation": _P363_CITATION,
        "candidate_source_id": _P363_SOURCE,
        "anchor_score": round(score, 2),
        "anchor_borderline": score >= CANDIDATE_FLOOR,
        "currency_flag": stale_threshold,
        "note": (
            f"Audit-committee composition content located in 12 CFR Part 363 App. A "
            f"(anchor {score:.2f} — borderline, not forced). Currency flag: the duty states "
            f'">$3 billion" but current Part 363 App. A applies at "$5 billion" (threshold '
            f"raised) — an F3-adjacent stale-threshold candidate for human review."
            if stale_threshold
            else f"Audit-committee composition content located in 12 CFR Part 363 App. A "
            f"(anchor {score:.2f}). Borderline; recorded as a candidate, not forced."
        ),
        "evidence_window": window[:300],
    }


def _cap10_redoc(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "duty_id": row["duty_id"],
        "outcome": "re-documented",
        "status": "unverified",
        "proposed_record_type": "no_board_duty_note",
        "cross_reference": "12 CFR 225.8(e) / SR 15-18 capital-plan approval (already verified)",
        "note": (
            "Negative record: no board-of-directors attestation is required on the FR Y-14A "
            "(the CFO signs). FR Y-14A form instructions are not a primary-law source, so the "
            "row is not independently verifiable as a duty. Proposed (human-gated, like "
            "s:CAP-11): reclassify as record_type=no_board_duty_note, excluded from duty "
            "counts; the board instrument it points to (225.8(e)/SR 15-18) is verified "
            "elsewhere. Not applied here — normative/reclassification checkpoint."
        ),
    }


def run_retries(import_doc: dict[str, Any], cache: Path = Path("data/sources")) -> dict[str, Any]:
    rows = _rows_by_id(import_doc)
    resolver = build_resolver(Fetcher(cache, offline_client()))
    targets = [rows[i] for i in RETRY_IDS if i in rows]
    verified_rows = verify_targets(targets, resolver)

    outcomes: list[dict[str, Any]] = []
    resolved_spans: list[dict[str, Any]] = []
    resolved_records: list[dict[str, Any]] = []
    for rv in verified_rows:
        if rv.duty_id == "s:GOV-15" and rv.record.status == "verified":
            outcomes.append(
                {
                    "duty_id": rv.duty_id,
                    "outcome": "resolved",
                    "status": "verified",
                    "as_of_valid": rv.verdict.as_of_valid,
                    "anchor_matched": rv.verdict.anchor_matched,
                    "support_signal": rv.verdict.support_signal,
                    "citation": rv.verdict.span.citation if rv.verdict.span else rv.citation,
                    "note": rv.verdict.note,
                }
            )
            if rv.verdict.span is not None:
                resolved_spans.append(rv.verdict.span.model_dump(mode="json"))
            resolved_records.append(rv.record.model_dump(mode="json"))

    outcomes.append(_cap10_redoc(rows["s:CAP-10"]))
    outcomes.append(_bcg14_redoc(rows["s:BCG-14"]))
    outcomes.sort(key=lambda o: o["duty_id"])

    resolved = [o["duty_id"] for o in outcomes if o["outcome"] == "resolved"]
    redocumented = [o["duty_id"] for o in outcomes if o["outcome"] == "re-documented"]
    return {
        "_meta": "B5-T0(c) residual retries. The three B2 residuals the stronger resolver stack "
        "may now reach; s:GOV-15 resolves via the SR-letter-body anchor fallback, the other two "
        "are re-documented with evidence (never forced). The remaining 19 B2 residuals stay "
        "accepted residuals.",
        "counts": {
            "retried": len(outcomes),
            "resolved": len(resolved),
            "re_documented": len(redocumented),
        },
        "resolved_rows": resolved,
        "re_documented_rows": redocumented,
        "resolved_spans": resolved_spans,
        "resolved_records": resolved_records,
        "outcomes": outcomes,
    }
