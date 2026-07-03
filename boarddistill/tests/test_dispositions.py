"""B2-T0 — reviewer_accepted dispositions for the B1-verified rows."""

from __future__ import annotations

from typing import Any

from adapters.dispositions import accept_verified, ledger, stamp_dispositions

_VERIF: dict[str, Any] = {
    "rows": [
        {"duty_id": "b:AUD-02", "status": "verified"},
        {"duty_id": "b:AUD-01", "status": "verified"},
        {"duty_id": "s:GOV-02", "status": "unverified"},
        {"duty_id": "x:BAD-01", "status": "contradicted"},
    ]
}


def test_accept_only_verified_rows_sorted() -> None:
    disps = accept_verified(_VERIF)
    assert [d.subject_id for d in disps] == ["b:AUD-01", "b:AUD-02"]  # sorted, verified only
    for d in disps:
        assert d.state == "reviewer_accepted"
        assert d.reviewer_id == "mhsu"
        assert d.timestamp == "2026-07-02"
        assert d.rationale


def test_stamp_dispositions_onto_import() -> None:
    disps = accept_verified(_VERIF)
    import_doc = {
        "duties": [
            {"duty_id": "b:AUD-01", "claims": []},
            {"duty_id": "s:GOV-02", "claims": []},  # unverified -> no disposition
        ]
    }
    stamped = stamp_dispositions(import_doc, disps)
    by_id = {d["duty_id"]: d for d in stamped["duties"]}
    assert by_id["b:AUD-01"]["disposition"]["state"] == "reviewer_accepted"
    assert "disposition" not in by_id["s:GOV-02"]


def test_ledger_counts_and_determinism() -> None:
    disps = accept_verified(_VERIF)
    first = ledger(disps)
    assert first == ledger(disps)
    assert first["counts"] == {"reviewer_accepted": 2}
    assert len(first["dispositions"]) == 2
