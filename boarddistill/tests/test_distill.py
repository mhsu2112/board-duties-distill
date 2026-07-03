"""B3-T2 — distillation logic (offline): anchor verification, verb-vs-retag cross-check,
target build, and the diff/summary reports. LLM calls are not exercised here."""

from __future__ import annotations

from typing import Any

from adapters.distill import (
    DistilledDuty,
    anchor_failures,
    build_targets,
    diff_report,
    distilled_document,
    verb_retag_conflict,
)
from adapters.distill import (
    DistilledRow as Row,
)

_EXCERPT = (
    "The audit committee shall review with management and the independent public accountant "
    "the basis for the reports, and shall meet at least annually."
)


def _duty(**kw: Any) -> DistilledDuty:
    base: dict[str, Any] = {
        "duty_id": "b:AUD-01",
        "verb_standard": "review_and_challenge",
        "verb_evidence": "shall review with management",
        "object": "the basis for the reports",
        "object_evidence": "the basis for the reports",
        "cadence": "annual",
        "cadence_evidence": "at least annually",
    }
    base.update(kw)
    return DistilledDuty.model_validate(base)


def test_anchor_clean_when_quotes_are_substrings() -> None:
    assert anchor_failures(_duty(), _EXCERPT) == []


def test_anchor_failure_on_fabricated_quote() -> None:
    d = _duty(object_evidence="a quote the excerpt does not contain")
    fails = anchor_failures(d, _EXCERPT)
    assert len(fails) == 1 and "object_evidence" in fails[0]


def test_empty_evidence_is_not_an_anchor_failure() -> None:
    # unresolved fields carry empty evidence — that is allowed, not a hallucination.
    d = _duty(verb_standard="none_specified", verb_evidence="")
    assert anchor_failures(d, _EXCERPT) == []


def test_anchor_tolerates_source_whitespace_artifact() -> None:
    # XML extraction split "Capital" into "C apital"; the model quotes the correct spacing.
    artifact_excerpt = "(6) C apital plan cycle means the period beginning on January 1."
    d = _duty(
        object="capital plan cycle",
        object_evidence="Capital plan cycle means the period beginning",
        verb_standard="none_specified",
        verb_evidence="",
        cadence="none_specified",
        cadence_evidence="",
    )
    assert anchor_failures(d, artifact_excerpt) == []


def test_anchor_still_catches_real_fabrication_despite_ws_tolerance() -> None:
    d = _duty(
        object_evidence="the board shall hire a consultant",
        cadence_evidence="",
        verb_evidence="",
    )
    assert anchor_failures(d, _EXCERPT)  # content genuinely absent → still a failure


def test_verb_retag_conflict_flagged_for_active_verb() -> None:
    retag = {"parameter": "actor", "from_actor": "Audit committee", "to_actor": "management"}
    conflict = verb_retag_conflict(_duty(verb_standard="approve"), retag)
    assert conflict is not None
    assert conflict["retag_to_actor"] == "management"
    assert conflict["distilled_verb_standard"] == "approve"


def test_verb_retag_no_conflict_for_oversight_verb() -> None:
    retag = {"parameter": "actor", "from_actor": "Audit committee", "to_actor": "management"}
    assert verb_retag_conflict(_duty(verb_standard="receive_report"), retag) is None
    # review_and_challenge is an active board verb → it would conflict
    assert verb_retag_conflict(_duty(verb_standard="review_and_challenge"), retag) is not None


def _verification() -> dict[str, Any]:
    return {
        "rows": [
            {"duty_id": "b:AUD-01", "status": "verified"},
            {"duty_id": "s:GOV-02", "status": "unverified"},
        ],
        "records": [
            {"claim_id": "claim-b:AUD-01", "checked_span_ids": ["sp1"]},
        ],
        "spans": [{"id": "sp1", "citation": "12 CFR 363.5", "quote": _EXCERPT}],
    }


def test_build_targets_only_verified_rows() -> None:
    drafts = {"b:AUD-01": {"duty_id": "b:AUD-01", "object": "x", "verb_standard": "none_specified"}}
    targets = build_targets(_verification(), drafts)
    assert [t.duty_id for t in targets] == ["b:AUD-01"]
    assert targets[0].excerpt == _EXCERPT


def test_reports_summarize_flags() -> None:
    drafts = {
        "b:AUD-01": {
            "duty_id": "b:AUD-01",
            "object": "old object",
            "verb_standard": "none_specified",
            "cadence": "continuous",
        }
    }
    good = Row("b:AUD-01", _duty(), True, [], None)
    bad = Row(
        "b:AUD-01",
        _duty(object_evidence="nope"),
        False,
        ["object_evidence: 'nope' not in excerpt"],
        {"duty_id": "b:AUD-01"},
    )
    mismatch = Row("s:GOV-03", _duty(object="", object_evidence=""), True, [], None)
    doc = distilled_document([good, bad, mismatch])
    assert doc["counts"]["anchor_clean"] == 2
    assert doc["counts"]["anchor_failures"] == 1
    assert doc["counts"]["verb_retag_conflicts"] == 1
    # empty distilled object ⇒ the excerpt didn't support the duty (source-mismatch signal)
    assert doc["counts"]["source_mismatch_rows"] == 1
    assert doc["source_mismatch_rows"] == ["s:GOV-03"]

    md = diff_report([good], drafts)
    assert "b:AUD-01" in md and "review_and_challenge" in md
