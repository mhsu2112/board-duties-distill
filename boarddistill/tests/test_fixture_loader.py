"""T4 — the three B0 fixtures + the _calculus mirror load, schema-validate, and pass
referential checks; the mirror composes to vertical_rationalization."""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from adapters.fixture_loader import load_fixture, validate_bundle
from profiles.lex_balanus.composites import composite_of

_FIXTURES = Path(__file__).resolve().parent.parent / "data" / "fixtures" / "us-gsib"
_DIRS = ["icfr", "sr12-17", "board-effectiveness", "_calculus"]


@pytest.mark.parametrize("name", _DIRS)
def test_fixture_loads_and_validates(name: str) -> None:
    bundle = load_fixture(_FIXTURES / name)
    assert validate_bundle(bundle) == []
    assert bundle.as_built
    assert bundle.gold_findings


@pytest.mark.parametrize("name", _DIRS)
def test_every_gold_finding_has_a_baseline_or_is_unresolved(name: str) -> None:
    bundle = load_fixture(_FIXTURES / name)
    for finding in bundle.gold_findings:
        assert finding.baseline is not None or finding.effect_class == "unresolved"


def test_icfr_deem_composes_to_single_primitive() -> None:
    bundle = load_fixture(_FIXTURES / "icfr")
    ops_by_id = {op.id: op for op in bundle.gold_operations}
    deem = next(f for f in bundle.gold_findings if f.id == "f-deem")
    assert len(deem.operation_ids) == 1
    assert str(ops_by_id[deem.operation_ids[0]].primitive) == "DEEM_SATISFIED"


def test_calculus_mirror_composes_to_vertical_rationalization() -> None:
    bundle = load_fixture(_FIXTURES / "_calculus")
    ops_by_id = {op.id: op for op in bundle.gold_operations}
    mirror = next(f for f in bundle.gold_findings if f.id == "f-mirror")
    primitives = [ops_by_id[oid].primitive for oid in mirror.operation_ids]
    assert composite_of(primitives) == "vertical_rationalization"
    # DEEM_SATISFIED is present and intact (not decomposed away)
    assert any(str(p) == "DEEM_SATISFIED" for p in primitives)


def test_instrument_graph_baseline_lookups_resolve() -> None:
    bundle = load_fixture(_FIXTURES / "icfr")
    as_of = date(2026, 6, 1)
    baseline = bundle.instrument_graph.baseline_for("b:AUD-ICFR-363", as_of)
    assert baseline is not None
    assert baseline.stratum == "statute"  # FDI Act §36 outranks Part 363


def test_sr1217_relocate_is_a_force_conversion_setup() -> None:
    # as-built guidance duties relocate into a regulation — the §2.9 conversion the
    # fixture exists to exercise.
    bundle = load_fixture(_FIXTURES / "sr12-17")
    as_built = {d.duty_id: d for d in bundle.as_built}
    intended = {d.duty_id: d for d in bundle.intended}
    assert str(as_built["s:GOV-02"].legal_force) == "guidance"
    assert str(intended["s:GOV-02"].legal_force) == "regulation"
