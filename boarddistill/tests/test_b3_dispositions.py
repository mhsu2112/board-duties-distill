"""B3-T0 — residual acceptances + s:CAP-11 reclassification + SR 95-51 node."""

from __future__ import annotations

from typing import Any

from adapters.b3_dispositions import accept_residuals, cap11_record, duty_row_ids, ledger

_VERIF: dict[str, Any] = {
    "rows": [
        {"duty_id": "b:AUD-02", "status": "verified"},
        {"duty_id": "s:CAP-11", "status": "verified"},  # reclassified out of duties
        {"duty_id": "s:GOV-02", "status": "unverified"},
        {"duty_id": "s:GOV-11", "status": "unverified"},
    ]
}


def test_accept_residuals_only_non_verified() -> None:
    disps = accept_residuals(_VERIF)
    assert [d.subject_id for d in disps] == ["s:GOV-02", "s:GOV-11"]
    assert all(d.state == "reviewer_accepted" and d.reviewer_id == "mhsu" for d in disps)


def test_cap11_reclassified_and_excluded_from_duties() -> None:
    rec = cap11_record()
    assert rec["duty_id"] == "s:CAP-11" and rec["record_type"] == "supersession_note"
    # s:CAP-11 is excluded from the duty row set
    assert "s:CAP-11" not in duty_row_ids(_VERIF)
    assert set(duty_row_ids(_VERIF)) == {"b:AUD-02", "s:GOV-02", "s:GOV-11"}


def test_ledger_counts() -> None:
    doc = ledger(_VERIF)
    c = doc["counts"]
    assert c["target_duty_rows"] == 3  # 4 rows minus s:CAP-11
    assert c["verified_duties"] == 1  # b:AUD-02 (s:CAP-11 excluded)
    assert c["residuals_accepted"] == 2
    assert c["supersession_notes"] == 1


def test_graph_has_sr_9551_amended() -> None:
    from adapters.graph_build import _EXTRA_NODES

    sr = next(n for n in _EXTRA_NODES if n["id"] == "sr-95-51")
    assert sr["treatment_status"] == "amended"
    assert "revised" in str(sr["treatment_evidence"]).lower()
