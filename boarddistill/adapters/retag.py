"""B2-T1 — actor retag for the 6 B1 support-flagged rows (human-approved, M. Hsu 2026-07-02).

Each row's citation verified but its text does not bind the stated board actor. We record a
retag (conceptually ASSIGN_DUTY_PARAMETER on an *actor* dimension) with the B1 verbatim quote
as evidence, correct the draft's actor to what the text binds, preserve the original in a
provenance note, add a board_oversight_note for the indirect duty, and set the disposition to
``reviewer_modified``. Scope is EXACTLY these 6 (§checkpoint 2); s:CAP-11 carries a TODO(human).

NOTE (§14.2 proposal, not applied): formalizing "actor" as a member of the ASSIGN_DUTY_PARAMETER
parameter set (currently {verb_standard, cadence}) is a calculus extension left for the human —
these records reference it without mutating the core enum.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from distillcore.models.review import ReviewDisposition

from .dispositions import ACCEPT_RATIONALE, REVIEWER, TIMESTAMP

RETAG_RATIONALE = (
    "B1 support-flag retag: actor corrected to the bound party; board oversight annotated"
)

# The approved 6. to_actor = the party the verified text actually binds.
RETAGS: dict[str, dict[str, str | None]] = {
    "b:AUD-04": {
        "actor": "management / the institution",
        "note": "Board oversight via the audit committee under FDI Act §36 / Part 363; the "
        "annual report and audited financial statements are management's.",
        "todo": None,
    },
    "b:AUD-05": {
        "actor": "management",
        "note": "Board oversight via the audit committee under SOX 301 / Part 363; SOX 404(a) "
        "binds management's ICFR assessment, not the board.",
        "todo": None,
    },
    "b:AUD-06": {
        "actor": "external auditor (registered public accounting firm)",
        "note": "The audit committee oversees the external auditor's ICFR attestation under "
        "SOX 301 / Part 363; SOX 404(b) binds the auditor.",
        "todo": None,
    },
    "b:AUD-07": {
        "actor": "CEO and CFO (principal executive and financial officers)",
        "note": "Board oversight via the audit committee under SOX 301 / Part 363; SOX 302 "
        "binds the certifying officers, not the board.",
        "todo": None,
    },
    "b:RGC-01": {
        "actor": "the bank holding company",
        "note": "Statute mandates committee existence; the board duty is structural (maintain "
        "a risk committee), not operational.",
        "todo": None,
    },
    "s:CAP-11": {
        "actor": "management / the company (proposed)",
        "note": "TODO(human): s:CAP-11 cites SR 15-18 fn. 5 — a supersession note (SR 09-4 "
        "superseded for GSIBs), not a board-actor misattribution. Actor retag is a placeholder.",
        "todo": "confirm whether s:CAP-11 is a retag at all; it is an instrument-treatment note "
        "(B2-T1 gave no board_oversight guidance for it).",
    },
}


@dataclass(frozen=True)
class RetagRecord:
    duty_id: str
    primitive: str
    parameter: str
    from_actor: str
    to_actor: str
    evidence_citation: str
    evidence_quote: str
    board_oversight_note: str
    todo_human: str | None


def _evidence(duty_id: str, verification: dict[str, Any]) -> tuple[str, str]:
    row = next((r for r in verification["rows"] if r["duty_id"] == duty_id), None)
    if row is None:
        return "", ""
    row_cite = row["citation"]
    for span in verification.get("spans", []):
        if span["citation"] and span["citation"] in row_cite:
            return span["citation"], span.get("quote", "")
    return row_cite, ""


def build_retags(
    verification: dict[str, Any],
    import_doc: dict[str, Any],
) -> tuple[list[RetagRecord], dict[str, Any]]:
    """Return the retag records and the import doc with the 6 drafts modified in place."""
    by_id = {d["duty_id"]: d for d in import_doc["duties"]}
    records: list[RetagRecord] = []
    for duty_id, spec in RETAGS.items():
        duty = by_id.get(duty_id)
        if duty is None:
            continue
        from_actor = str(duty.get("board_level", ""))
        to_actor = str(spec["actor"])
        cite, quote = _evidence(duty_id, verification)
        record = RetagRecord(
            duty_id=duty_id,
            primitive="ASSIGN_DUTY_PARAMETER",
            parameter="actor",
            from_actor=from_actor,
            to_actor=to_actor,
            evidence_citation=cite,
            evidence_quote=quote,
            board_oversight_note=str(spec["note"]),
            todo_human=spec["todo"],
        )
        records.append(record)

        disposition = ReviewDisposition(
            subject_id=duty_id,
            state="reviewer_modified",
            reviewer_id=REVIEWER,
            timestamp=TIMESTAMP,
            rationale=RETAG_RATIONALE,
            from_state="reviewer_accepted",
        )
        duty["actor"] = to_actor
        duty["provenance"] = {
            "original_board_level": from_actor,
            "note": "actor retagged per B1 support-flag review (B2-T1)",
        }
        duty["board_oversight_note"] = str(spec["note"])
        if spec["todo"] is not None:
            duty["todo_human"] = spec["todo"]
        duty["disposition"] = disposition.model_dump(mode="json")
    return records, import_doc


def combined_ledger(verification: dict[str, Any]) -> list[ReviewDisposition]:
    """The full disposition set after retag: accepted for verified rows, modified for the 6."""
    out: list[ReviewDisposition] = []
    for row in sorted(verification["rows"], key=lambda r: r["duty_id"]):
        if row["status"] != "verified":
            continue
        if row["duty_id"] in RETAGS:
            out.append(
                ReviewDisposition(
                    subject_id=row["duty_id"],
                    state="reviewer_modified",
                    reviewer_id=REVIEWER,
                    timestamp=TIMESTAMP,
                    rationale=RETAG_RATIONALE,
                    from_state="reviewer_accepted",
                )
            )
        else:
            out.append(
                ReviewDisposition(
                    subject_id=row["duty_id"],
                    state="reviewer_accepted",
                    reviewer_id=REVIEWER,
                    timestamp=TIMESTAMP,
                    rationale=ACCEPT_RATIONALE,
                )
            )
    return out


def retag_ledger(records: list[RetagRecord]) -> dict[str, Any]:
    return {
        "_meta": "B2-T1 actor-retag ledger. The approved 6 support-flagged rows; actor "
        "corrected to the bound party with the B1 quote as evidence. s:CAP-11 is TODO(human). "
        "Formalizing 'actor' as an ASSIGN_DUTY_PARAMETER member is a §14.2 proposal, not applied.",
        "retags": [r.__dict__ for r in records],
    }
