"""B2 review-state: record human dispositions on the B1-verified duty rows.

Records are appended to a ledger and stamped onto the imported drafts (a ``disposition``
block per duty). Duty text is never edited (§6.1) — only review state is added.
"""

from __future__ import annotations

from typing import Any

from distillcore.models.review import DispositionState, ReviewDisposition

REVIEWER = "mhsu"
TIMESTAMP = "2026-07-02"
ACCEPT_RATIONALE = "B1 verification accepted via chat review"


def accept_verified(verification: dict[str, Any]) -> list[ReviewDisposition]:
    """A ``reviewer_accepted`` disposition for every ``verified`` row (sorted by id)."""
    return [
        ReviewDisposition(
            subject_id=row["duty_id"],
            state="reviewer_accepted",
            reviewer_id=REVIEWER,
            timestamp=TIMESTAMP,
            rationale=ACCEPT_RATIONALE,
        )
        for row in sorted(verification["rows"], key=lambda r: r["duty_id"])
        if row["status"] == "verified"
    ]


def stamp_dispositions(
    import_doc: dict[str, Any],
    dispositions: list[ReviewDisposition],
) -> dict[str, Any]:
    """Write each disposition onto its duty in the import doc (last-writer per subject)."""
    by_subject: dict[str, ReviewDisposition] = {d.subject_id: d for d in dispositions}
    for duty in import_doc["duties"]:
        disp = by_subject.get(duty["duty_id"])
        if disp is not None:
            duty["disposition"] = disp.model_dump(mode="json")
    return import_doc


def ledger(dispositions: list[ReviewDisposition]) -> dict[str, Any]:
    counts: dict[DispositionState, int] = {}
    for d in dispositions:
        counts[d.state] = counts.get(d.state, 0) + 1
    return {
        "_meta": "B2 review-state ledger. Human dispositions on B1-verified rows; "
        "duty text is never edited (§6.1).",
        "counts": dict(sorted(counts.items())),
        "dispositions": [d.model_dump(mode="json") for d in dispositions],
    }
