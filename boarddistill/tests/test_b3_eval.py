"""B3-T6 — eval (offline): B0 effect agreement, citation integrity gate, baseline."""

from __future__ import annotations

from typing import Any

from adapters.b3_eval import (
    _b0_dominant_effect,
    agreement_report,
    baseline_comparison,
    citation_integrity,
)


def test_b0_dominant_effect_takes_most_severe_and_flags_conditional() -> None:
    dec = {"operations": [{"effect_class": "codify"}, {"effect_class": "change"}]}
    assert _b0_dominant_effect(dec) == ("change", False)
    cond = {"operations": [{"effect_class": "clarify_or_change_per_duty"}]}
    assert _b0_dominant_effect(cond) == ("clarify", True)  # conditional label normalized


def test_agreement_marks_no_baseline_disagreement() -> None:
    decs = [
        {"id": "D1", "operations": [{"effect_class": "change"}]},
        {"id": "D3", "operations": [{"effect_class": "change"}]},
    ]
    findings = {
        "findings": [
            {"id": "f-D1", "effect_class": "change"},
            {"id": "f-D3", "effect_class": "unresolved"},
        ]
    }
    rep = agreement_report(decs, findings)
    assert rep["effect_class_agreement"] == "1/2"
    d3 = next(r for r in rep["rows"] if r["decomposition"] == "D3")
    assert not d3["agree"] and "no-baseline" in d3["characterization"]


def test_citation_integrity_pass_when_all_anchored() -> None:
    distilled = {
        "rows": [
            {
                "duty_id": "b:AUD-01",
                "distilled": {
                    "duty_id": "b:AUD-01",
                    "verb_standard": "review_and_challenge",
                    "verb_evidence": "shall review",
                    "object": "reports",
                    "object_evidence": "the reports",
                    "cadence": "none_specified",
                    "cadence_evidence": "",
                },
            }
        ]
    }
    excerpts = {"b:AUD-01": "The committee shall review the reports annually."}
    integ = citation_integrity(distilled, {"anchor_failures": []}, excerpts)
    assert integ["distilled_anchored_claims"] == 2  # verb + object evidence
    assert integ["distilled_anchor_failures"] == 0
    assert integ["hallucinated_citation_rate"] == 0.0
    assert integ["release_gate"] == "PASS"


def test_citation_integrity_fails_on_fabrication() -> None:
    distilled = {
        "rows": [
            {
                "duty_id": "b:AUD-01",
                "distilled": {
                    "duty_id": "b:AUD-01",
                    "verb_standard": "none_specified",
                    "verb_evidence": "",
                    "object": "x",
                    "object_evidence": "text not present anywhere",
                    "cadence": "none_specified",
                    "cadence_evidence": "",
                },
            }
        ]
    }
    integ = citation_integrity(distilled, {"anchor_failures": []}, {"b:AUD-01": "unrelated"})
    assert integ["release_gate"] == "FAIL"


def test_baseline_comparison_counts_pinned_excerpts() -> None:
    drafts: dict[str, Any] = {
        "b:AUD-01": {"duty_id": "b:AUD-01", "claims": [{"source_span_ids": ["cite-b:AUD-01"]}]},
        "b:AUD-99": {"duty_id": "b:AUD-99", "claims": [{"source_span_ids": ["cite-b:AUD-99"]}]},
    }
    aud = "Audit committee & independence"
    cluster_of = {"b:AUD-01": aud, "b:AUD-99": aud}
    excerpts = {"b:AUD-01": "real pinned text"}  # only AUD-01 was verified
    b = baseline_comparison(drafts, cluster_of, excerpts, aud)
    assert b["raw_inventory_rows"] == 2
    assert b["raw_claims_with_pinned_excerpt"] == 1
