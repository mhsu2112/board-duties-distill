"""B4-T0 — disposition write-back: f-D1…f-D9 + AUD-07 + the 18 diagnostics, under mhsu,
recorded without finalizing anything (NG2)."""

from __future__ import annotations

from typing import Any

from adapters.b4_dispositions import (
    AUD07_SUBJECT,
    all_dispositions,
    aud07_disposition,
    blocker_summary,
    consolidation_dispositions,
    diagnostic_dispositions,
    ledger,
)

_FINDINGS: dict[str, Any] = {
    "findings": [
        {"id": "f-D1", "disposition_state": "needs_review", "status": "draft"},
        {"id": "f-D7", "disposition_state": "auto_ok", "status": "draft"},
        {"id": "dx-ris-0", "disposition_state": "needs_review", "status": "draft"},
        {"id": "dx-cap-6", "disposition_state": "needs_review", "status": "draft"},
    ]
}


def test_consolidation_dispositions_accept_as_draft_direction() -> None:
    disps = consolidation_dispositions(_FINDINGS)
    assert [d.subject_id for d in disps] == ["f-D1", "f-D7"]
    assert all(d.state == "reviewer_accepted" and d.reviewer_id == "mhsu" for d in disps)
    # the draft-direction qualifier is explicit in the rationale (not policy adoption)
    assert all("draft roadmap direction" in d.rationale for d in disps)
    # from_state carries the pre-disposition state (auto_ok for f-D7)
    assert {d.subject_id: d.from_state for d in disps} == {
        "f-D1": "needs_review",
        "f-D7": "auto_ok",
    }


def test_diagnostic_dispositions_accept_all_as_investigation_items() -> None:
    disps = diagnostic_dispositions(_FINDINGS)
    assert [d.subject_id for d in disps] == ["dx-cap-6", "dx-ris-0"]
    assert all(d.state == "reviewer_accepted" for d in disps)
    assert all("investigation item" in d.rationale for d in disps)


def test_aud07_is_reviewer_modified_with_oversight_rationale() -> None:
    d = aud07_disposition()
    assert d.subject_id == AUD07_SUBJECT
    assert d.state == "reviewer_modified"
    assert "review_and_challenge" in d.rationale and "certify" in d.rationale


def test_blocker_summary_nothing_finalized() -> None:
    b = blocker_summary(_FINDINGS)
    assert b["findings_final"] == 0
    assert b["silently_finalized"] == []
    assert b["findings_draft"] == b["findings_total"] == 4


def test_ledger_has_all_families_and_stays_draft() -> None:
    doc = ledger(_FINDINGS)
    # 2 consolidation + 2 diagnostics + 1 AUD-07 = 5 records
    assert len(doc["dispositions"]) == len(all_dispositions(_FINDINGS)) == 5
    assert doc["counts"] == {"reviewer_accepted": 4, "reviewer_modified": 1}
    assert doc["blocker_summary"]["silently_finalized"] == []
