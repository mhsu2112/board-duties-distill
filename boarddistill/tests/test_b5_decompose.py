"""B5-T4 — lever decomposition + closure validation."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from adapters.b5_decompose import ProposedLever, ProposedOp, _clean_floor_candidate, validate_lever

_ROOT = Path(__file__).resolve().parents[1]
_DECOMP = _ROOT / "outputs" / "b5" / "corpus" / "lever_decompositions.json"


def _op(primitive: str, **kw: object) -> ProposedOp:
    return ProposedOp(primitive=primitive, effect_class="change", **kw)  # type: ignore[arg-type]


def test_single_primitive_is_valid() -> None:
    lever = ProposedLever(lever_id="L1", composition="single", operations=[_op("MERGE")])
    v = validate_lever(lever)
    assert v["status"] == "valid_single"
    assert v["composition"] == "single:MERGE"


def test_known_composite_is_valid() -> None:
    lever = ProposedLever(
        lever_id="L2",
        composition="consolidation",
        operations=[_op("MERGE"), _op("CANONICALIZE_DEFINITION"), _op("RESOLVE_CROSS_REFERENCE")],
    )
    v = validate_lever(lever)
    assert v["status"] == "valid_composite"
    assert v["composition"] == "consolidation"


def test_unknown_multiop_bundle_is_a_residual() -> None:
    # RELOCATE + RESOLVE_CROSS_REFERENCE is not a named composite ⇒ residual (checkpoint).
    lever = ProposedLever(
        lever_id="L3",
        composition="consolidation",
        operations=[_op("RELOCATE"), _op("RESOLVE_CROSS_REFERENCE")],
    )
    v = validate_lever(lever)
    assert v["status"] == "residual"


def test_llm_declared_residual_with_no_ops_is_honored() -> None:
    lever = ProposedLever(
        lever_id="L4", composition="residual", residual_reason="disjunctive either/or reform"
    )
    v = validate_lever(lever)
    assert v["status"] == "residual"
    assert "disjunctive" in v["reason"]


def test_non_target_is_documented_not_forced() -> None:
    lever = ProposedLever(lever_id="L5", is_consolidation=False, composition="non_target")
    assert validate_lever(lever)["status"] == "documented_non_target"


def test_empty_ops_without_residual_flag_is_incomplete() -> None:
    lever = ProposedLever(lever_id="L6", composition="single")  # claims single, gives no op
    assert validate_lever(lever)["status"] == "incomplete"


def test_iff_violation_is_invalid_structure() -> None:
    # DEEM_SATISFIED without its required satisfied/satisfying refs violates the model iff-rule.
    lever = ProposedLever(
        lever_id="L7", composition="single", operations=[_op("DEEM_SATISFIED")]
    )
    assert validate_lever(lever)["status"] == "invalid_structure"


def test_floor_candidate_cleaning() -> None:
    assert _clean_floor_candidate("GLBA \\u00a7501(b)") == "GLBA §501(b)"
    assert _clean_floor_candidate('DFA ":___placeholder_do_not_use') is None
    assert _clean_floor_candidate("  12 U.S.C. 371c  ") == "12 U.S.C. 371c"


@pytest.mark.skipif(not _DECOMP.exists(), reason="B5-T4 artifact absent")
def test_decomposition_artifact_every_lever_resolved_or_checkpointed() -> None:
    doc = json.loads(_DECOMP.read_text())
    statuses = {r["lever_id"]: r["status"] for r in doc["levers"]}
    allowed = {"valid_single", "valid_composite", "residual", "documented_non_target"}
    assert all(s in allowed for s in statuses.values())  # no incomplete/invalid left
    # residuals are surfaced as checkpoints, floor candidates proposed (not added)
    assert doc["counts"]["residuals"] == len(doc["residual_checkpoints"])
    assert "GLBA §501(b)" in doc["statutory_floor_candidates"]["candidates"]
