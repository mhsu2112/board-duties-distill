"""T2 — banking profile: closed primitive set (test #3), DutySpec snapshot enforcement,
instrument-graph baseline lookup, and the lex_allium stub."""

from __future__ import annotations

from datetime import date

import pytest
from pydantic import ValidationError

from profiles.lex_allium import loaders as allium_loaders
from profiles.lex_allium.enums import PrimitiveOp as AlliumPrimitiveOp
from profiles.lex_balanus.enums import STRATUM_RANK, LegalForce, PrimitiveOp, is_binding
from profiles.lex_balanus.models import (
    BankingOperation,
    DutySpec,
    InstrumentGraph,
)

_EXPECTED_ORDER = [
    "MERGE",
    "SPLIT",
    "INTRODUCE",
    "REPEAL",
    "RELOCATE",
    "RELATE_OBLIGATION",
    "CANONICALIZE_DEFINITION",
    "DEFINE_TERM",
    "SUBSTITUTE_TERM",
    "NORMALIZE_ELEMENTS",
    "ASSIGN_DUTY_PARAMETER",
    "FACTOR_EXCEPTION",
    "REGRADE",
    "ELEVATE_GENERAL_RULE",
    "RESOLVE_CROSS_REFERENCE",
    "DEEM_SATISFIED",
]


def test_primitive_set_is_exactly_sixteen_in_order() -> None:
    assert len(PrimitiveOp) == 16
    assert [p.name for p in PrimitiveOp] == _EXPECTED_ORDER


def test_generalized_and_criminal_names_are_not_members() -> None:
    names = {p.name for p in PrimitiveOp}
    assert "ASSIGN_MENS_REA" not in names
    assert "ASSIGN_DUTY_STANDARD" not in names  # the generalization replaced it
    assert "RELATE_OFFENSE" not in names
    assert "ASSIGN_DUTY_PARAMETER" in names
    assert "DEEM_SATISFIED" in names


def test_free_text_primitive_rejected() -> None:
    with pytest.raises(ValidationError):
        BankingOperation(id="op", primitive="frobnicate", arity=1)  # type: ignore[arg-type]


def _snapshot_kwargs() -> dict[str, date]:
    return {
        "inventory_as_of": date(2026, 6, 1),
        "consolidation_as_of": date(2026, 6, 30),
        "current_as_of": date(2026, 7, 1),
    }


def _duty(**over: object) -> DutySpec:
    base: dict[str, object] = {
        "duty_id": "RGC-02",
        "label": "Approve enterprise risk framework",
        "layer": "as_built",
        "snapshot_dates": _snapshot_kwargs(),
        "board_level": "full_board",
        "director_class": "any",
        "entity": "BHC",
        "verb_standard": "approve",
        "object": "enterprise risk-management framework",
        "cadence": "annual",
        "legal_force": "regulation",
        "consequence": "supervisory_finding",
        "instrument_id": "reg-yy-252.33",
        "currency_status": "active",
        "confidence": 0.9,
    }
    base.update(over)
    return DutySpec.model_validate(base)


def test_dutyspec_requires_snapshot_dates() -> None:
    duty = _duty()
    assert duty.snapshot_dates.inventory_as_of == date(2026, 6, 1)
    without_snapshot = {
        "duty_id": "x",
        "label": "x",
        "layer": "as_built",
        "board_level": "full_board",
        "director_class": "any",
        "entity": "BHC",
        "verb_standard": "approve",
        "object": "x",
        "cadence": "annual",
        "legal_force": "regulation",
        "consequence": "none_specified",
        "instrument_id": "i",
        "currency_status": "active",
        "confidence": 0.5,
    }
    with pytest.raises(ValidationError):
        DutySpec.model_validate(without_snapshot)


def test_is_binding_and_stratum_rank() -> None:
    assert is_binding(LegalForce.STATUTE)
    assert is_binding(LegalForce.ENFORCEABLE_GUIDELINE)
    assert not is_binding(LegalForce.GUIDANCE)
    assert STRATUM_RANK[LegalForce.STATUTE] > STRATUM_RANK[LegalForce.REGULATION]
    assert STRATUM_RANK[LegalForce.GUIDANCE] > STRATUM_RANK[LegalForce.MANUAL]


def _graph() -> InstrumentGraph:
    return InstrumentGraph.model_validate(
        {
            "nodes": [
                {
                    "id": "reg-yy",
                    "citation": "12 CFR 252.33",
                    "agency": "FRB",
                    "stratum": "regulation",
                    "effective_date": "2014-01-01",
                    "treatment_status": "active",
                    "bears_on": ["RGC-02"],
                },
                {
                    "id": "sr-12-17",
                    "citation": "SR 12-17",
                    "agency": "FRB",
                    "stratum": "guidance",
                    "effective_date": "2012-01-01",
                    "treatment_status": "active",
                    "bears_on": ["RGC-02"],
                },
                {
                    "id": "sr-09-4",
                    "citation": "SR 09-4",
                    "agency": "FRB",
                    "stratum": "guidance",
                    "effective_date": "2009-01-01",
                    "treatment_status": "superseded",
                    "treatment_date": "2015-01-01",
                    "bears_on": ["CAP-11"],
                },
            ]
        }
    )


def test_baseline_picks_highest_active_stratum() -> None:
    baseline = _graph().baseline_for("RGC-02", date(2026, 6, 1))
    assert baseline is not None
    assert baseline.id == "reg-yy"  # regulation beats guidance


def test_baseline_none_when_no_bearing_node() -> None:
    assert _graph().baseline_for("DOES-NOT-EXIST", date(2026, 6, 1)) is None


def test_baseline_excludes_superseded_and_future_nodes() -> None:
    graph = _graph()
    # superseded before the snapshot -> not a baseline
    assert graph.baseline_for("CAP-11", date(2026, 6, 1)) is None
    # but valid before its supersession date
    assert graph.baseline_for("CAP-11", date(2010, 1, 1)) is not None
    # regulation not yet effective at an early snapshot
    early = graph.baseline_for("RGC-02", date(2013, 1, 1))
    assert early is not None
    assert early.id == "sr-12-17"


def test_graph_materializes_to_networkx() -> None:
    graph = _graph().to_networkx()
    assert graph.number_of_nodes() == 3


def test_lex_allium_stub_enums_and_loaders() -> None:
    names = {p.name for p in AlliumPrimitiveOp}
    # The engine's set enumerates 15 names though the prose says "fourteen" — the
    # off-by-one flagged in AGENTS §5 / checkpoint §14.5. The *set* is ground truth.
    assert len(AlliumPrimitiveOp) == 15
    assert "RELATE_OFFENSE" in names
    assert "ASSIGN_MENS_REA" in names
    assert "DEEM_SATISFIED" not in names
    with pytest.raises(NotImplementedError):
        allium_loaders.load_statutory_floor()
