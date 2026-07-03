"""T-CALCULUS — Operation envelope iff-rules, composite table, and validate_composition.

Covers test #4 (effect_class vs primitive are distinct value spaces) and the composition
half of test #6 (DEEM_SATISFIED is atomic; a single DEEM_SATISFIED and the
vertical_rationalization composite both validate with residual empty; the forbidden
RESOLVE_CROSS_REFERENCE+FACTOR_EXCEPTION re-expression is a residual).
"""

from __future__ import annotations

from typing import Any, get_args

import pytest
from pydantic import ValidationError

from distillcore.models.calculus import EffectClass
from distillcore.pipeline.operations import validate_composition
from profiles.lex_balanus.composites import (
    COMPOSITES,
    composite_of,
    decompose,
    is_forbidden_composition,
)
from profiles.lex_balanus.enums import PrimitiveOp
from profiles.lex_balanus.models import BankingFinding, BankingOperation


def _op(**over: Any) -> BankingOperation:
    base: dict[str, Any] = {"id": "op", "primitive": "MERGE", "arity": 2, "operands": ["a", "b"]}
    base.update(over)
    return BankingOperation.model_validate(base)


def _finding(fid: str, op_ids: list[str], effect: str = "change") -> BankingFinding:
    return BankingFinding.model_validate(
        {
            "id": fid,
            "provision": "P",
            "operation_ids": op_ids,
            "effect_class": effect,
            "rationale": "r",
            "confidence": 0.8,
        }
    )


# ---- test #4: effect_class and primitive are distinct value spaces ----------------


def test_effect_class_and_primitive_value_spaces_are_disjoint() -> None:
    effect_values = set(get_args(EffectClass))
    primitive_values = {p.value for p in PrimitiveOp}
    assert effect_values.isdisjoint(primitive_values)


def test_effect_class_value_rejected_as_primitive_and_vice_versa() -> None:
    with pytest.raises(ValidationError):
        _op(primitive="change")  # an EffectClass, not a primitive
    with pytest.raises(ValidationError):
        _finding("f", ["o"], effect="MERGE")  # a primitive, not an EffectClass


# ---- generic envelope iff-rules ---------------------------------------------------


def test_relation_iff_relate_obligation() -> None:
    with pytest.raises(ValidationError):
        _op(primitive="RELATE_OBLIGATION")  # relation missing
    _op(primitive="RELATE_OBLIGATION", relation="entity_level_mirror")  # ok
    with pytest.raises(ValidationError):
        _op(primitive="MERGE", relation="implements")  # relation on non-relate


def test_deem_fields_iff_deem_satisfied() -> None:
    with pytest.raises(ValidationError):
        _op(primitive="DEEM_SATISFIED")  # refs + conditions missing
    with pytest.raises(ValidationError):
        _op(primitive="DEEM_SATISFIED", satisfied_ref="a", satisfying_ref="b", conditions=[])
    _op(primitive="DEEM_SATISFIED", satisfied_ref="a", satisfying_ref="b", conditions=["c"])
    with pytest.raises(ValidationError):
        _op(primitive="MERGE", satisfied_ref="a")  # deem field on non-deem


def test_parameter_iff_assign_duty_parameter() -> None:
    with pytest.raises(ValidationError):
        _op(primitive="ASSIGN_DUTY_PARAMETER")  # parameter missing
    _op(primitive="ASSIGN_DUTY_PARAMETER", parameter="cadence")  # ok
    with pytest.raises(ValidationError):
        _op(primitive="MERGE", parameter="cadence")  # parameter on non-param


# ---- composites (§6) ---------------------------------------------------------------


def test_decompose_known_and_atomic_and_unknown() -> None:
    assert [s.primitive for s in decompose("consolidation")] == [
        PrimitiveOp.MERGE,
        PrimitiveOp.CANONICALIZE_DEFINITION,
        PrimitiveOp.RESOLVE_CROSS_REFERENCE,
    ]
    vr_steps = [s.primitive for s in decompose("vertical_rationalization")]
    assert PrimitiveOp.DEEM_SATISFIED in vr_steps
    with pytest.raises(ValueError):
        decompose("DEEM_SATISFIED")  # atomic, not decomposable
    with pytest.raises(KeyError):
        decompose("streamlining")  # unknown


def test_composite_lookup_and_deem_not_reexpressible() -> None:
    mirror = [
        PrimitiveOp.RELATE_OBLIGATION,
        PrimitiveOp.DEEM_SATISFIED,
        PrimitiveOp.FACTOR_EXCEPTION,
    ]
    assert composite_of(mirror) == "vertical_rationalization"
    # the forbidden deem re-expression resolves to no composite
    assert composite_of([PrimitiveOp.RESOLVE_CROSS_REFERENCE, PrimitiveOp.FACTOR_EXCEPTION]) is None
    assert "DEEM_SATISFIED" not in COMPOSITES


def test_b5_residual_closure_composites_recognized() -> None:
    """B6-T0: the three approved B5-residual-closure composites are named composites (sugar)."""
    assert (
        composite_of(
            [PrimitiveOp.MERGE, PrimitiveOp.FACTOR_EXCEPTION, PrimitiveOp.RELATE_OBLIGATION]
        )
        == "partial_consolidation"
    )
    assert (
        composite_of(
            [
                PrimitiveOp.INTRODUCE,
                PrimitiveOp.DEEM_SATISFIED,
                PrimitiveOp.FACTOR_EXCEPTION,
                PrimitiveOp.RESOLVE_CROSS_REFERENCE,
            ]
        )
        == "safe_harbor_template"
    )
    assert (
        composite_of(
            [PrimitiveOp.DEFINE_TERM, PrimitiveOp.SPLIT, PrimitiveOp.ASSIGN_DUTY_PARAMETER]
        )
        == "tiered_attention"
    )


def test_unnamed_enum_composition_is_expressible_after_relaxation() -> None:
    """B6-T0: any composition of enum members is expressible (not a residual), named or not —
    only a forbidden composition (the deem re-expression) is a residual."""
    ops = [
        _op(id="o1", primitive="RELATE_OBLIGATION", relation="parallel_distinct_purpose"),
        _op(id="o2", primitive="MERGE"),
        _op(id="o3", primitive="RESOLVE_CROSS_REFERENCE", arity=1),
        _op(id="o4", primitive="FACTOR_EXCEPTION", arity=1),
    ]
    findings = [_finding("f_r1", ["o1", "o2", "o3", "o4"])]
    # not a named composite, but a valid enum composition ⇒ no residual
    assert composite_of([o.primitive for o in ops]) is None
    assert validate_composition(findings, ops, is_forbidden_composition) == []
    assert not is_forbidden_composition([o.primitive for o in ops])


def test_streamlining_and_burden_reduction_are_not_calculus() -> None:
    for bad in ("streamlining", "burden_reduction"):
        assert bad not in {p.value for p in PrimitiveOp}
        assert bad not in set(get_args(EffectClass))
        assert bad not in COMPOSITES


# ---- validate_composition (composition half of #6) --------------------------------


def test_single_deem_satisfied_has_no_residual() -> None:
    ops = [
        _op(
            id="o1",
            primitive="DEEM_SATISFIED",
            satisfied_ref="a",
            satisfying_ref="b",
            conditions=["c"],
        )
    ]
    findings = [_finding("f1", ["o1"])]
    assert validate_composition(findings, ops, is_forbidden_composition) == []


def test_vertical_rationalization_composite_validates_with_deem_intact() -> None:
    ops = [
        _op(id="o1", primitive="RELATE_OBLIGATION", relation="entity_level_mirror"),
        _op(
            id="o2",
            primitive="DEEM_SATISFIED",
            satisfied_ref="idi",
            satisfying_ref="bhc",
            conditions=["documented reliance"],
        ),
        _op(id="o3", primitive="FACTOR_EXCEPTION", arity=1),
    ]
    findings = [_finding("f_mirror", ["o1", "o2", "o3"])]
    assert validate_composition(findings, ops, is_forbidden_composition) == []
    assert any(o.primitive == PrimitiveOp.DEEM_SATISFIED for o in ops)


def test_forbidden_deem_reexpression_is_a_residual() -> None:
    ops = [
        _op(id="o1", primitive="RESOLVE_CROSS_REFERENCE", arity=1),
        _op(id="o2", primitive="FACTOR_EXCEPTION", arity=1),
    ]
    findings = [_finding("f_bad", ["o1", "o2"])]
    residuals = validate_composition(findings, ops, is_forbidden_composition)
    assert len(residuals) == 1
    assert residuals[0].finding_id == "f_bad"
