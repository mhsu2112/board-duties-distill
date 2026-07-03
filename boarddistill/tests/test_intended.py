"""B3-T3 — intended layer (offline): operation scaffolding (iff-rules + the
ASSIGN_DUTY_STANDARD amendment), operand resolution, and intended-spec assembly."""

from __future__ import annotations

from typing import Any

import pytest

from adapters.intended import (
    IntendedDraft,
    build_intended_spec,
    resolution_report,
    scaffold_operation,
    scaffold_operations,
)
from profiles.lex_balanus.enums import PrimitiveOp

_DEC: dict[str, Any] = {
    "id": "D1",
    "cluster": "Risk-governance framework / strategy",
    "lever": "One enterprise framework approval",
    "instrument_required": "interagency_statement",
    "actor_with_authority": ["FRB", "OCC"],
    "operations": [
        {
            "primitive": "RELATE_OBLIGATION",
            "relation": "entity_level_mirror",
            "operands": ["b:RGC-02", "b:RGC-07"],
            "effect_class": "clarify",
        },
        {
            "primitive": "DEEM_SATISFIED",
            "satisfied_ref": "b:RGC-07",
            "satisfying_ref": "b:RGC-02",
            "conditions": ["risk profiles substantially the same"],
            "effect_class": "change",
        },
        {"primitive": "ASSIGN_DUTY_STANDARD", "standard": "approve", "effect_class": "clarify"},
    ],
}


def test_relate_obligation_carries_relation() -> None:
    op = scaffold_operation(_DEC, 0, _DEC["operations"][0])
    assert op.primitive == PrimitiveOp.RELATE_OBLIGATION
    assert op.relation is not None and op.relation.value == "entity_level_mirror"
    assert op.operands == ["b:RGC-02", "b:RGC-07"] and op.arity == 2


def test_deem_satisfied_refs_and_conditions() -> None:
    op = scaffold_operation(_DEC, 1, _DEC["operations"][1])
    assert op.primitive == PrimitiveOp.DEEM_SATISFIED
    assert op.satisfied_ref == "b:RGC-07" and op.satisfying_ref == "b:RGC-02"
    assert op.conditions and op.arity == 2
    assert op.normative_load == "high"  # effect_class == change


def test_assign_duty_standard_amended_to_parameter() -> None:
    # B0 TODO-2: ASSIGN_DUTY_STANDARD generalizes to ASSIGN_DUTY_PARAMETER over verb_standard.
    op = scaffold_operation(_DEC, 2, _DEC["operations"][2])
    assert op.primitive == PrimitiveOp.ASSIGN_DUTY_PARAMETER
    assert op.parameter == "verb_standard"


def test_unknown_primitive_raises() -> None:
    with pytest.raises(ValueError):
        scaffold_operation(_DEC, 0, {"primitive": "TELEPORT_DUTY", "operands": []})


def test_resolution_splits_clean_ids_from_concept_refs() -> None:
    ops = scaffold_operations(_DEC)
    rr = resolution_report(ops, inventory_ids={"b:RGC-02", "b:RGC-07"})
    assert set(rr["resolved"]) == {"b:RGC-02", "b:RGC-07"}
    assert rr["unresolved"] == []


def test_resolution_reports_unresolved_concept_ref() -> None:
    ops = scaffold_operations(_DEC)
    rr = resolution_report(ops, inventory_ids={"b:RGC-02"})  # b:RGC-07 now "unresolved"
    assert "b:RGC-07" in rr["unresolved"]


def test_intended_spec_is_illustrative_and_cites_all_operands() -> None:
    draft = IntendedDraft(
        decomposition_id="D1",
        label="Enterprise framework approval",
        object="one enterprise risk-governance framework",
        consolidated_text="The board approves one enterprise framework...",
        operands_cited=["b:RGC-02"],  # LLM under-cited; spec uses the full deterministic set
    )
    drafts = {
        "b:RGC-02": {"entity": "BHC", "legal_force": "regulation"},
        "b:RGC-07": {"entity": "IDI", "legal_force": "guidance"},
    }
    spec = build_intended_spec(_DEC, draft, ["b:RGC-02", "b:RGC-07"], drafts)
    assert spec.layer == "intended"
    assert "[illustrative consolidation — NG2]" in spec.label
    assert spec.verb_standard.value == "none_specified"
    assert spec.legal_force.value == "regulation"  # max stratum of operands
    assert spec.entity == "both"
    assert spec.source_citations == ["b:RGC-02", "b:RGC-07"]  # complete, not the LLM subset
    assert spec.confidence == 0.4
