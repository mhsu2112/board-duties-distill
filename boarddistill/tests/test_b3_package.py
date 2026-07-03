"""B3-T5 — per-cluster consolidation packages (deterministic render)."""

from __future__ import annotations

from typing import Any

from adapters.b3_package import build_packages, cluster_slug, render_cluster_package

_DISTILLED = {
    "rows": [
        {
            "duty_id": "b:AUD-01",
            "anchor_ok": True,
            "distilled": {
                "verb_standard": "none_specified",
                "object": "audit committee composition",
                "cadence": "none_specified",
                "elements": [{"text": "e", "quote": "q"}],
            },
        }
    ]
}
_INTENDED = {
    "decompositions": [
        {
            "cluster": "Audit committee & independence",
            "intended_spec": {
                "duty_id": "i:D3",
                "legal_force": "regulation",
                "object": "one audit committee",
                "entity": "both",
                "source_citations": ["b:AUD-01", "SOX-301"],
            },
        }
    ]
}
_AUD = "Audit committee & independence"
_FINDINGS = {
    "finding_cluster": {"f-D3": _AUD, "dx-aud-0": _AUD},
    "findings": [
        {
            "id": "f-D3",
            "provision": "one audit committee lever",
            "effect_class": "unresolved",
            "normative_kind": ["policy_choice"],
            "disposition_state": "needs_review",
            "status": "draft",
            "as_built_ref": "b:AUD-01",
            "intended_ref": "i:D3",
        },
        {
            "id": "dx-aud-0",
            "provision": "duplicate_duty :: b:AUD-01, b:AUD-02",
            "effect_class": "unresolved",
            "normative_kind": [],
            "disposition_state": "needs_review",
            "status": "draft",
            "as_built_ref": "b:AUD-01",
            "intended_ref": None,
        },
    ],
}
_VERIF = {
    "rows": [{"duty_id": "b:AUD-01", "cluster": _AUD, "status": "verified"}],
    "records": [
        {
            "claim_id": "claim-b:AUD-01",
            "checked_span_ids": ["sp1"],
            "status": "verified",
            "method": "live_retrieval",
        }
    ],
    "spans": [
        {"id": "sp1", "citation": "12 CFR 363.5", "quote": "audit committee composition text"}
    ],
}
_GRAPH: dict[str, Any] = {
    "graph": {
        "nodes": [
            {
                "id": "p363",
                "citation": "12 CFR Part 363",
                "agency": "FDIC",
                "stratum": "regulation",
                "treatment_status": "active",
                "bears_on": ["b:AUD-01"],
            }
        ],
        "edges": [],
    }
}


def test_build_packages_covers_three_mvp_clusters() -> None:
    pkgs = build_packages(_DISTILLED, _INTENDED, _FINDINGS, _VERIF, _GRAPH)
    assert set(pkgs) == {"risk-governance", "audit-committee", "capital-planning"}


def test_audit_package_has_all_sections_and_zero_final() -> None:
    pkgs = build_packages(_DISTILLED, _INTENDED, _FINDINGS, _VERIF, _GRAPH)
    md = pkgs["audit-committee"]
    for section in [
        "## As-built duties",
        "## Intended duties",
        "## Instrument graph",
        "## Findings",
        "## Duty crosswalk",
        "## Authority to act",
        "## Claim verification",
        "## Normative review queue",
        "## Final-status blocker summary",
    ]:
        assert section in md
    assert "b:AUD-01" in md and "i:D3" in md
    assert "| final |" not in md  # nothing finalized — the intended B3 end-state
    assert "blocked pending human review" in md


def test_cluster_slug_mapping() -> None:
    assert cluster_slug("Capital planning & stress testing") == "capital-planning"


def test_render_handles_empty_cluster() -> None:
    md = render_cluster_package("Empty cluster", [], [], [], {}, {}, [])
    assert "## Findings" in md and "final: 0" in md
