"""B4-T0 — write the B3 review dispositions into the review state.

The human record is ``../REVIEW_PACKET_B3.md`` (M. Hsu, 2026-07-02; all recommendations
accepted). Three disposition families are persisted here as ``ReviewDisposition`` records
under reviewer ``mhsu``:

1. **f-D1…f-D9** (Packet Part 1) — ``reviewer_accepted`` **as draft roadmap direction**, not
   policy adoption. The rationale carries that qualifier and the feasibility ranking (D4
   first, D5 second, D3 hardest).
2. **b:AUD-07** (Packet Part 2) — ``reviewer_modified``: the certification duty stays with the
   CEO/CFO; the board-side residual is audit-committee *oversight* of the certification
   process (``review_and_challenge``, never ``certify`` as a board verb). Applied to the spec
   in B4-T1.
3. **The eighteen dx-* diagnostics** (Packet Part 5) — ``reviewer_accepted`` as investigation
   items seeding the DEFINE_TERM / ASSIGN_DUTY_PARAMETER worklists.

Load-bearing invariant (NG2): a ``reviewer_accepted`` on a *draft-direction* basis does **not**
finalize a finding. ``Finding.status`` stays ``draft`` until an operative reform instrument
exists; these records add review state, never flip status. Nothing is silently finalized.
"""

from __future__ import annotations

from typing import Any

from distillcore.models.review import DispositionState, ReviewDisposition

REVIEWER = "mhsu"
TIMESTAMP = "2026-07-02"

CONSOLIDATION_RATIONALE = (
    "REVIEW_PACKET_B3 Part 1 — advance as draft roadmap direction (evidence-backed "
    "candidate), NOT policy adoption. Feasibility ranking: D4 first, D5 second, D3 hardest."
)
AUD07_RATIONALE = (
    "REVIEW_PACKET_B3 Part 2 — certification duty stays with the CEO/CFO; the board-side "
    "residual is audit-committee oversight of the certification process (review_and_challenge, "
    "never certify as a board verb)."
)
DIAGNOSTIC_RATIONALE = (
    "REVIEW_PACKET_B3 Part 5 — accepted as an investigation item (seeds the DEFINE_TERM / "
    "ASSIGN_DUTY_PARAMETER worklists); not a decision."
)

AUD07_SUBJECT = "b:AUD-07"


def _consolidation_ids(findings_doc: dict[str, Any]) -> list[str]:
    return sorted(
        f["id"] for f in findings_doc["findings"] if f["id"].startswith("f-D")
    )


def _diagnostic_ids(findings_doc: dict[str, Any]) -> list[str]:
    return sorted(
        f["id"] for f in findings_doc["findings"] if f["id"].startswith("dx-")
    )


def _state_of(findings_doc: dict[str, Any]) -> dict[str, str]:
    return {f["id"]: f["disposition_state"] for f in findings_doc["findings"]}


def consolidation_dispositions(findings_doc: dict[str, Any]) -> list[ReviewDisposition]:
    """``reviewer_accepted`` (draft-direction) for each of f-D1…f-D9 (Packet Part 1)."""
    state = _state_of(findings_doc)
    return [
        ReviewDisposition(
            subject_id=fid,
            state="reviewer_accepted",
            reviewer_id=REVIEWER,
            timestamp=TIMESTAMP,
            rationale=CONSOLIDATION_RATIONALE,
            from_state=_as_state(state.get(fid)),
        )
        for fid in _consolidation_ids(findings_doc)
    ]


def diagnostic_dispositions(findings_doc: dict[str, Any]) -> list[ReviewDisposition]:
    """``reviewer_accepted`` (investigation item) for each of the eighteen dx-* diagnostics."""
    state = _state_of(findings_doc)
    return [
        ReviewDisposition(
            subject_id=fid,
            state="reviewer_accepted",
            reviewer_id=REVIEWER,
            timestamp=TIMESTAMP,
            rationale=DIAGNOSTIC_RATIONALE,
            from_state=_as_state(state.get(fid)),
        )
        for fid in _diagnostic_ids(findings_doc)
    ]


def aud07_disposition() -> ReviewDisposition:
    """``reviewer_modified`` for b:AUD-07 (Packet Part 2); applied to the spec in B4-T1."""
    return ReviewDisposition(
        subject_id=AUD07_SUBJECT,
        state="reviewer_modified",
        reviewer_id=REVIEWER,
        timestamp=TIMESTAMP,
        rationale=AUD07_RATIONALE,
        from_state="needs_review",
    )


def _as_state(value: str | None) -> DispositionState | None:
    allowed = {
        "auto_ok",
        "needs_review",
        "reviewer_accepted",
        "reviewer_rejected",
        "reviewer_modified",
    }
    return value if value in allowed else None  # type: ignore[return-value]


def all_dispositions(findings_doc: dict[str, Any]) -> list[ReviewDisposition]:
    return [
        *consolidation_dispositions(findings_doc),
        aud07_disposition(),
        *diagnostic_dispositions(findings_doc),
    ]


def blocker_summary(findings_doc: dict[str, Any]) -> dict[str, Any]:
    """Regenerated final-status blocker summary. Despite the acceptances, no finding reaches
    ``final`` (NG2): every finding is still ``draft`` and no operative reform instrument
    exists. This is the record that nothing was silently finalized."""
    findings = findings_doc["findings"]
    non_draft = [f["id"] for f in findings if f.get("status", "draft") != "draft"]
    return {
        "findings_total": len(findings),
        "findings_draft": sum(1 for f in findings if f.get("status", "draft") == "draft"),
        "findings_final": len(non_draft),
        "silently_finalized": non_draft,  # must be empty (NG2)
        "note": "reviewer_accepted is recorded on a draft-direction basis; status stays draft "
        "until an operative reform instrument exists (NG2). No finding reaches final.",
    }


def ledger(findings_doc: dict[str, Any]) -> dict[str, Any]:
    disps = all_dispositions(findings_doc)
    counts: dict[str, int] = {}
    for d in disps:
        counts[d.state] = counts.get(d.state, 0) + 1
    return {
        "_meta": "B4-T0 disposition write-back. Human record: ../REVIEW_PACKET_B3.md "
        "(mhsu, 2026-07-02, all recommendations accepted). reviewer_accepted on f-D* is "
        "draft-direction, not policy adoption; nothing finalized (NG2).",
        "reviewer": REVIEWER,
        "timestamp": TIMESTAMP,
        "counts": dict(sorted(counts.items())),
        "consolidation_findings": _consolidation_ids(findings_doc),
        "diagnostic_findings": _diagnostic_ids(findings_doc),
        "blocker_summary": blocker_summary(findings_doc),
        "dispositions": [d.model_dump(mode="json") for d in disps],
    }
