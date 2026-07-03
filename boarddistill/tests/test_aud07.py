"""B4-T1 — AUD-07 resolution + the verb-vs-actor cross-check regression."""

from __future__ import annotations

from typing import Any

from adapters.aud07 import apply_to_distilled, resolve
from adapters.distill import DistilledDuty, verb_retag_conflict

_RETAG: dict[str, Any] = {
    "duty_id": "b:AUD-07",
    "parameter": "actor",
    "primitive": "ASSIGN_DUTY_PARAMETER",
    "from_actor": "Audit committee",
    "to_actor": "CEO and CFO (principal executive and financial officers)",
    "evidence_citation": "17 CFR 240.13a-14",
    "board_oversight_note": "Board oversight via the audit committee under SOX 301 / Part 363.",
}

_DISTILLED_DOC: dict[str, Any] = {
    "counts": {"distilled": 1, "verb_retag_conflicts": 1},
    "verb_retag_conflicts": [{"duty_id": "b:AUD-07", "distilled_verb_standard": "certify"}],
    "rows": [
        {
            "duty_id": "b:AUD-07",
            "anchor_ok": True,
            "anchor_failures": [],
            "retag_conflict": {"duty_id": "b:AUD-07", "distilled_verb_standard": "certify"},
            "distilled": {
                "duty_id": "b:AUD-07",
                "verb_standard": "certify",
                "verb_evidence": "must include certifications in the form specified",
                "object": "certification",
                "cadence": "quarterly",
            },
        }
    ],
}


def _distilled(verb: str) -> DistilledDuty:
    return DistilledDuty.model_validate(
        {"duty_id": "b:AUD-07", "verb_standard": verb, "object": "x", "cadence": "quarterly"}
    )


def test_board_certify_on_management_actor_triggers_cross_check() -> None:
    """Regression (B4-T1): a board-level `certify` verb on a row whose actor was retagged to
    management must trigger the verb-vs-actor cross-check."""
    conflict = verb_retag_conflict(_distilled("certify"), _RETAG)
    assert conflict is not None
    assert conflict["distilled_verb_standard"] == "certify"
    assert conflict["retag_to_actor"] == "CEO and CFO (principal executive and financial officers)"
    # A passive board verb on the same retagged row does not (only active board verbs do).
    assert verb_retag_conflict(_distilled("receive_report"), _RETAG) is None


def test_resolution_splits_board_oversight_from_management_certification() -> None:
    res = resolve(_DISTILLED_DOC["rows"][0], _RETAG)
    assert res["board_side"]["verb_standard"] == "review_and_challenge"
    assert res["board_side"]["verb_evidence"] == ""  # not anchorable in the SOX 302 excerpt
    assert res["management_side"]["verb_standard"] == "certify"
    assert res["management_side"]["actor"].startswith("CEO and CFO")
    assert res["conflict_cleared"] is True


def test_apply_clears_the_flagged_conflict() -> None:
    doc = apply_to_distilled(_DISTILLED_DOC, _RETAG)
    row = next(r for r in doc["rows"] if r["duty_id"] == "b:AUD-07")
    assert row["distilled"]["verb_standard"] == "review_and_challenge"
    assert row["retag_conflict"] is None
    assert doc["verb_retag_conflicts"] == []
    assert doc["counts"]["verb_retag_conflicts"] == 0
    # original document is not mutated in place
    assert _DISTILLED_DOC["counts"]["verb_retag_conflicts"] == 1
