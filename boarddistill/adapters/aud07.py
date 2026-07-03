"""B4-T1 — apply the AUD-07 resolution (REVIEW_PACKET_B3 Part 2).

The B3 distiller read the SOX 302 / 17 CFR 240.13a-14 source as ``verb_standard: certify``;
the B2 retag had already moved the actor to the CEO/CFO. Both cannot describe the board — the
distiller flagged the contradiction (``verb_retag_conflict``) rather than resolve it.

M. Hsu's disposition (accepted 2026-07-02): the **certification** duty belongs to the CEO/CFO
(the SOX 302 verb ``certify`` lives on a management actor record); the **board-side residual**
is audit-committee *oversight of the certification process*, recorded as ``review_and_challenge``
— never ``certify`` as a board verb. That residual is grounded not in SOX 302 but in the audit
committee's oversight mandate (SOX 301 / Part 363), carried by the B2 retag's oversight note.

This module is a deterministic **review-state overlay**: it splits the conflicting row into a
board-side spec (review_and_challenge) and a management actor record (certify), and clears the
flagged conflict. The LLM is not re-run; nothing is finalized.
"""

from __future__ import annotations

from typing import Any

AUD07 = "b:AUD-07"
REVIEWER = "mhsu"
TIMESTAMP = "2026-07-02"

BOARD_VERB = "review_and_challenge"
MANAGEMENT_VERB = "certify"
MANAGEMENT_ACTOR = "CEO and CFO (principal executive and financial officers)"

RATIONALE = (
    "REVIEW_PACKET_B3 Part 2 — SOX 302 (17 CFR 240.13a-14) binds the certifying officers, "
    "not the board; the board-side residual is audit-committee oversight of the certification "
    "process (review_and_challenge), grounded in SOX 301 / Part 363, not SOX 302."
)


def resolve(distilled_row: dict[str, Any], retag: dict[str, Any]) -> dict[str, Any]:
    """Build the AUD-07 resolution from the distilled row and the B2 retag record."""
    return {
        "duty_id": AUD07,
        "reviewer_id": REVIEWER,
        "timestamp": TIMESTAMP,
        "rationale": RATIONALE,
        "board_side": {
            "actor": "Audit committee",
            "verb_standard": BOARD_VERB,
            "object": "oversight of the CEO/CFO certification process via the audit committee",
            # Not anchorable in the SOX 302 excerpt; grounded in the retag's oversight note.
            "verb_evidence": "",
            "grounding": retag.get("board_oversight_note", ""),
            "grounding_citation": "SOX 301 / 12 CFR Part 363 (audit committee oversight)",
        },
        "management_side": {
            "actor": MANAGEMENT_ACTOR,
            "verb_standard": MANAGEMENT_VERB,
            "object": "quarterly certification of financial reports",
            "citation": retag.get("evidence_citation", "17 CFR 240.13a-14"),
            "verb_evidence": distilled_row["distilled"].get("verb_evidence", ""),
            "note": "SOX 302 certification verb lives on the management actor, not the board.",
        },
        "conflict_cleared": True,
    }


def apply_to_distilled(distilled_doc: dict[str, Any], retag: dict[str, Any]) -> dict[str, Any]:
    """Return a copy of the distilled document with the AUD-07 conflict resolved: the board-side
    verb becomes ``review_and_challenge`` and the flagged ``verb_retag_conflict`` is cleared."""
    doc = {**distilled_doc}
    rows = []
    resolution: dict[str, Any] | None = None
    for row in distilled_doc["rows"]:
        if row["duty_id"] != AUD07:
            rows.append(row)
            continue
        resolution = resolve(row, retag)
        new_row = {**row}
        distilled = {**row["distilled"]}
        distilled["verb_standard"] = BOARD_VERB
        distilled["verb_evidence"] = ""  # board oversight verb not in the SOX 302 excerpt
        note = distilled.get("notes", "")
        distilled["notes"] = (
            (note + " " if note else "")
            + "AUD-07 resolved (B4-T1): board-side verb is review_and_challenge (audit-committee "
            "oversight); the SOX 302 certify verb lives on the CEO/CFO actor record."
        ).strip()
        new_row["distilled"] = distilled
        new_row["retag_conflict"] = None
        new_row["aud07_resolution"] = resolution
        rows.append(new_row)
    doc["rows"] = rows

    # Drop the cleared conflict from the document-level ledgers.
    doc["verb_retag_conflicts"] = [
        c for c in distilled_doc.get("verb_retag_conflicts", []) if c.get("duty_id") != AUD07
    ]
    counts = {**distilled_doc.get("counts", {})}
    counts["verb_retag_conflicts"] = len(doc["verb_retag_conflicts"])
    doc["counts"] = counts
    doc["aud07_resolution"] = resolution
    return doc
