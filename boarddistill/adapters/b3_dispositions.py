"""B3-T0 — apply the human B3 dispositions.

1. The 22 B2 residuals are accepted as documented residuals (stay ``unverified``, do not
   block B3).
2. ``s:CAP-11`` is reclassified as a supersession note (not a duty row) — excluded from duty
   counts and packages, retained in the instrument graph as SR 09-4 treatment evidence.

Duty text is never edited (§6.1). ``timestamp`` supplied by the caller.
"""

from __future__ import annotations

from typing import Any

from distillcore.models.review import ReviewDisposition

REVIEWER = "mhsu"
TIMESTAMP = "2026-07-02"
RESIDUAL_RATIONALE = "accepted as documented residual (B2); stays unverified, does not block B3"

# Rows reclassified out of the duty set (records, not duties).
SUPERSESSION_NOTES: frozenset[str] = frozenset({"s:CAP-11"})


def accept_residuals(verification: dict[str, Any]) -> list[ReviewDisposition]:
    """A ``reviewer_accepted`` disposition for every non-verified row (the residuals)."""
    return [
        ReviewDisposition(
            subject_id=row["duty_id"],
            state="reviewer_accepted",
            reviewer_id=REVIEWER,
            timestamp=TIMESTAMP,
            rationale=RESIDUAL_RATIONALE,
        )
        for row in sorted(verification["rows"], key=lambda r: r["duty_id"])
        if row["status"] != "verified"
    ]


def cap11_record() -> dict[str, Any]:
    return {
        "duty_id": "s:CAP-11",
        "record_type": "supersession_note",
        "reviewer_id": REVIEWER,
        "timestamp": TIMESTAMP,
        "note": "Reclassified (B3-T0): s:CAP-11 is a supersession/currency record — SR 09-4 is "
        "superseded for GSIBs per SR 15-18 fn. 5 — not a board duty. Excluded from duty counts "
        "and packages; retained in the instrument graph as SR 09-4 treatment evidence. The B2 "
        "placeholder actor-retag is withdrawn.",
    }


def duty_row_ids(verification: dict[str, Any]) -> list[str]:
    """Target duty rows after reclassification (s:CAP-11 excluded)."""
    return sorted(
        row["duty_id"] for row in verification["rows"] if row["duty_id"] not in SUPERSESSION_NOTES
    )


def ledger(verification: dict[str, Any]) -> dict[str, Any]:
    residuals = accept_residuals(verification)
    rows = verification["rows"]
    verified = [r["duty_id"] for r in rows if r["status"] == "verified"]
    duty_rows = duty_row_ids(verification)
    return {
        "_meta": "B3-T0 review state. 22 residuals accepted as documented; s:CAP-11 reclassified "
        "as a supersession_note (excluded from duty counts).",
        "counts": {
            "target_duty_rows": len(duty_rows),
            "verified_duties": len([d for d in verified if d not in SUPERSESSION_NOTES]),
            "residuals_accepted": len(residuals),
            "supersession_notes": len(SUPERSESSION_NOTES),
        },
        "residual_dispositions": [d.model_dump(mode="json") for d in residuals],
        "supersession_notes": [cap11_record()],
    }
