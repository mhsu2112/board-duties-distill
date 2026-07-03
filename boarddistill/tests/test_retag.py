"""B2-T1 — actor retag for the approved 6 (scope guard + round-trip + s:CAP-11 TODO)."""

from __future__ import annotations

from typing import Any

from adapters.retag import RETAGS, build_retags, combined_ledger

_VERIF: dict[str, Any] = {
    "rows": [
        {
            "duty_id": "b:AUD-07",
            "status": "verified",
            "citation": "SOX sec. 302; 17 CFR 240.13a-14",
        },
        {"duty_id": "s:CAP-11", "status": "verified", "citation": "SR 15-18 fn. 5 (supersession)"},
        {"duty_id": "b:RGC-02", "status": "verified", "citation": "12 CFR 252.33(a)(1)"},
        {"duty_id": "s:GOV-02", "status": "unverified", "citation": "Attachment, Attribute 1"},
    ],
    "spans": [
        {
            "citation": "17 CFR 240.13a-14",
            "quote": "Each principal executive and financial officer shall certify...",
        },
    ],
}


def test_scope_is_exactly_the_six() -> None:
    assert set(RETAGS) == {"b:AUD-04", "b:AUD-05", "b:AUD-06", "b:AUD-07", "b:RGC-01", "s:CAP-11"}


def test_retag_round_trip_and_provenance() -> None:
    import_doc = {
        "duties": [
            {"duty_id": "b:AUD-07", "board_level": "Audit committee", "claims": []},
            {"duty_id": "b:RGC-02", "board_level": "Risk committee", "claims": []},  # not retagged
        ]
    }
    records, doc = build_retags(_VERIF, import_doc)
    by_id = {d["duty_id"]: d for d in doc["duties"]}

    aud07 = by_id["b:AUD-07"]
    assert aud07["actor"].startswith("CEO and CFO")
    assert aud07["provenance"]["original_board_level"] == "Audit committee"
    assert aud07["disposition"]["state"] == "reviewer_modified"
    assert aud07["disposition"]["from_state"] == "reviewer_accepted"
    assert "audit committee" in aud07["board_oversight_note"].lower()

    # a retag record carries the B1 quote as evidence
    rec = next(r for r in records if r.duty_id == "b:AUD-07")
    assert rec.parameter == "actor"
    assert "certify" in rec.evidence_quote

    # non-retagged verified row is untouched by the retag
    assert "actor" not in by_id["b:RGC-02"]


def test_cap11_carries_todo_human() -> None:
    import_doc = {"duties": [{"duty_id": "s:CAP-11", "board_level": "Full board", "claims": []}]}
    records, doc = build_retags(_VERIF, import_doc)
    cap11 = doc["duties"][0]
    assert cap11["todo_human"]
    rec = next(r for r in records if r.duty_id == "s:CAP-11")
    assert rec.todo_human is not None


def test_combined_ledger_splits_accepted_and_modified() -> None:
    disps = combined_ledger(_VERIF)
    states = {d.subject_id: d.state for d in disps}
    assert states["b:AUD-07"] == "reviewer_modified"
    assert states["s:CAP-11"] == "reviewer_modified"
    assert states["b:RGC-02"] == "reviewer_accepted"
    assert "s:GOV-02" not in states  # unverified -> no disposition
