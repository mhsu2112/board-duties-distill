"""B1-T4 — report, review queue, and status write-back (offline, synthetic input)."""

from __future__ import annotations

from typing import Any

from adapters.b1_report import apply_statuses_to_import, build_report, build_review_queue

_VERIFICATION: dict[str, Any] = {
    "summary": {"verified": 2, "unverified": 1, "contradicted": 1},
    "spans": [
        {"citation": "12 CFR 363.5", "quote": "§ 363.5 Audit committees. (a) Each institution..."},
    ],
    "rows": [
        {
            "duty_id": "b:AUD-02",
            "cluster": "Audit committee & independence",
            "citation": "12 CFR 363.5",
            "status": "verified",
            "as_of_valid": True,
            "support_signal": "strong",
            "note": "12 CFR 363.5 present and in force at 2026-06-30; verbatim text pinned",
        },
        {
            "duty_id": "b:AUD-06",
            "cluster": "Audit committee & independence",
            "citation": "15 U.S.C. 7262(b)",
            "status": "verified",
            "as_of_valid": True,
            "support_signal": "none",
            "note": "15 U.S.C. 7262(b) present in U.S. Code (2024 ed.); text pinned",
        },
        {
            "duty_id": "s:GOV-02",
            "cluster": "Risk-governance framework / strategy",
            "citation": "Attachment, Attribute 1",
            "status": "unverified",
            "as_of_valid": False,
            "support_signal": "n/a",
            "note": "guidance-document location; no addressable source",
        },
        {
            "duty_id": "x:BAD-01",
            "cluster": "Audit committee & independence",
            "citation": "12 CFR 363.99",
            "status": "contradicted",
            "as_of_valid": False,
            "support_signal": "none",
            "note": "section 363.99 not found (F1)",
        },
    ],
}


def test_review_queue_kinds_and_counts() -> None:
    queue = build_review_queue(_VERIFICATION)
    kinds = {item["duty_id"]: item["kind"] for item in queue["queue"]}
    assert kinds["s:GOV-02"] == "unverified"
    assert kinds["x:BAD-01"] == "contradicted"
    assert kinds["b:AUD-06"] == "f2_support"  # verified but support none
    assert "b:AUD-02" not in kinds  # verified with strong support -> not queued
    assert queue["counts"] == {"contradicted": 1, "f2_support": 1, "unverified": 1}


def test_report_is_deterministic_and_has_sections() -> None:
    first = build_report(_VERIFICATION)
    assert build_report(_VERIFICATION) == first
    for section in ["## Summary", "## Per-row status", "## Review queue", "## Methodology"]:
        assert section in first
    assert "§ 363.5 Audit committees" in first  # verified snippet present


def test_apply_statuses_sets_target_claims_only() -> None:
    import_doc = {
        "_banner": "old",
        "duties": [
            {"duty_id": "b:AUD-02", "claims": [{"id": "c1", "verifier_status": "unverified"}]},
            {"duty_id": "s:GOV-02", "claims": [{"id": "c2", "verifier_status": "unverified"}]},
            {"duty_id": "z:OTHER", "claims": [{"id": "c3", "verifier_status": "unverified"}]},
        ],
    }
    updated = apply_statuses_to_import(import_doc, _VERIFICATION)
    by_id = {d["duty_id"]: d for d in updated["duties"]}
    assert by_id["b:AUD-02"]["claims"][0]["verifier_status"] == "verified"
    assert by_id["s:GOV-02"]["claims"][0]["verifier_status"] == "unverified"
    assert by_id["z:OTHER"]["claims"][0]["verifier_status"] == "unverified"  # non-target untouched
    assert "B1 verification" in updated["_banner"]
