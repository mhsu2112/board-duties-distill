"""B4-T3 — the duplicate diagnostic splits into two first-class families: mirror_pair
(cross-layer/cross-entity) and restatement (same-text)."""

from __future__ import annotations

from adapters.diagnose import (
    MIRROR_PAIR,
    OFFICIAL_DIAGNOSTIC_KINDS,
    RESTATEMENT,
    Diagnostic,
    diagnostic_finding,
    duplication_family,
    mirror_pair_findings,
    official_kind,
)


def test_both_families_are_official_kinds() -> None:
    assert MIRROR_PAIR in OFFICIAL_DIAGNOSTIC_KINDS
    assert RESTATEMENT in OFFICIAL_DIAGNOSTIC_KINDS
    # duplicate_duty is no longer an official kind — it re-keys to restatement.
    assert "duplicate_duty" not in OFFICIAL_DIAGNOSTIC_KINDS


def test_duplicate_duty_rekeys_to_restatement() -> None:
    assert official_kind("duplicate_duty") == RESTATEMENT
    assert official_kind("rule_guidance_restatement") == "rule_guidance_restatement"
    assert official_kind("undefined_term") == "undefined_term"


def test_duplication_family_partition() -> None:
    assert duplication_family("duplicate_duty") == RESTATEMENT  # via re-key
    assert duplication_family("rule_guidance_restatement") == RESTATEMENT
    assert duplication_family(MIRROR_PAIR) == MIRROR_PAIR
    assert duplication_family("undefined_term") is None
    assert duplication_family("actor_ambiguity") is None


def test_diagnostic_finding_provision_uses_official_kind() -> None:
    d = Diagnostic.model_validate(
        {"kind": "duplicate_duty", "target_ids": ["b:AUD-01", "b:AUD-02"],
         "evidence_quote": "", "rationale": "same text"}
    )
    f = diagnostic_finding("Audit committee & independence", 0, d, anchor_ok=True)
    assert f.provision.startswith("restatement :: ")
    assert "duplicate_duty" not in f.provision


def test_mirror_pair_findings_materialize_b0_pairs() -> None:
    divergence = {"b0_only": [["b:RGC-01", "b:RGC-02"], ["b:RGC-02", "b:RGC-07"]]}
    cluster_of = {"b:RGC-01": "Risk-governance framework / strategy"}
    findings = mirror_pair_findings(divergence, cluster_of)
    assert len(findings) == 2
    assert all(f.provision.startswith("mirror_pair :: ") for f in findings)
    assert all(f.effect_class == "unresolved" for f in findings)  # 0-op, never guessed
    assert all(f.disposition_state == "needs_review" for f in findings)
    assert findings[0].as_built_ref == "b:RGC-01"
