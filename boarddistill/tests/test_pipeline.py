"""T5 — the pipeline reproduces gold operation+effect for all fixtures, residual empty,
and the §2.9 negative test (undeclared force conversion fails)."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from adapters.fixture_loader import load_fixture
from profiles.lex_balanus.pipeline import eval_fixture, run_fixture

_FIXTURES = Path(__file__).resolve().parent.parent / "data" / "fixtures" / "us-gsib"
_DIRS = ["icfr", "sr12-17", "board-effectiveness", "_calculus"]


@pytest.mark.parametrize("name", _DIRS)
def test_run_fixture_is_clean(name: str) -> None:
    result = run_fixture(load_fixture(_FIXTURES / name))
    assert result.residuals == []
    assert result.violations == []
    assert result.ok


@pytest.mark.parametrize("name", _DIRS)
def test_computed_findings_match_gold_effect_and_disposition(name: str) -> None:
    bundle = load_fixture(_FIXTURES / name)
    result = run_fixture(bundle)
    gold_by_id = {f.id: f for f in bundle.gold_findings}
    computed_by_id = {f.id: f for f in result.computed_findings}
    assert set(gold_by_id) == set(computed_by_id)
    for fid, gold in gold_by_id.items():
        computed = computed_by_id[fid]
        assert computed.operation_ids == gold.operation_ids
        assert computed.effect_class == gold.effect_class, f"{name}/{fid} effect"
        assert computed.disposition_state == gold.disposition_state, f"{name}/{fid} disposition"


def test_every_computed_finding_has_a_baseline_or_is_unresolved() -> None:
    for name in _DIRS:
        result = run_fixture(load_fixture(_FIXTURES / name))
        for f in result.computed_findings:
            assert f.baseline is not None or f.effect_class == "unresolved"


def test_claims_verify_against_present_sources() -> None:
    result = run_fixture(load_fixture(_FIXTURES / "icfr"))
    assert result.claim_status
    assert all(status == "verified" for status in result.claim_status.values())


def test_undeclared_force_conversion_fails() -> None:
    # §2.9 negative test: mutate the sr12-17 RELOCATE finding to drop the declaration.
    bundle = load_fixture(_FIXTURES / "sr12-17")
    mutated_findings = [
        f.model_copy(update={"force_conversion_declared": False}) if f.id == "f-relocate" else f
        for f in bundle.gold_findings
    ]
    mutated = replace(bundle, gold_findings=mutated_findings)
    result = run_fixture(mutated)
    assert any(v.code == "undeclared_force_conversion" for v in result.violations)
    assert not result.ok


@pytest.mark.parametrize("name", _DIRS)
def test_eval_reports_full_agreement(name: str) -> None:
    result = eval_fixture(load_fixture(_FIXTURES / name))
    assert result.effect_agreement == 1.0
    assert result.operation_agreement == 1.0
    assert result.disposition_agreement == 1.0
    assert result.all_match


def test_declared_force_conversion_passes() -> None:
    result = run_fixture(load_fixture(_FIXTURES / "sr12-17"))
    relocate = next(f for f in result.computed_findings if f.id == "f-relocate")
    assert relocate.effect_class == "change"
    assert relocate.force_conversion_declared is True
    assert not any(v.code == "undeclared_force_conversion" for v in result.violations)
