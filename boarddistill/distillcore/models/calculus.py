"""Calculus shapes: effect class, diagnostics, and the generic Operation envelope.

The ``Operation`` envelope is generic over the profile's primitive / relation /
instrument-required enums (AGENTS §5). A profile parameterizes it — e.g.
``Operation[PrimitiveOp, RelationType, InstrumentRequired]`` — and layers the
primitive-keyed iff-rules on top (T-CALCULUS). ``effect_class`` and ``primitive``
are deliberately different types and are never conflated (invariant §2.5).
"""

from __future__ import annotations

from collections.abc import Sequence
from enum import Enum
from typing import Generic, Literal, TypeVar

from pydantic import Field

from .base import StrictModel

# Effect class is a fixed core vocabulary; "unresolved" is the no-baseline sentinel
# (invariant §2.3 — never guessed).
EffectClass = Literal["codify", "clarify", "fill_gap", "change", "unresolved"]

OperationScope = Literal["duty_level", "general_part"]
NormativeLoad = Literal["low", "med", "high"]
# The parameter set ASSIGN_DUTY_PARAMETER ranges over (the approved generalization
# of ASSIGN_DUTY_STANDARD; B0 TODO 2). This is a fixed core literal, not a profile enum.
DutyParameter = Literal["verb_standard", "cadence"]


class Diagnostic(StrictModel):
    """A signal raised during alignment/diagnosis; points at duties and source spans."""

    kind: str
    target_ids: list[str] = Field(default_factory=list)
    rationale: str
    source_span_ids: list[str] = Field(default_factory=list)


PrimitiveT = TypeVar("PrimitiveT", bound=Enum)
RelationT = TypeVar("RelationT", bound=Enum)
InstrumentReqT = TypeVar("InstrumentReqT", bound=Enum)


class Operation(StrictModel, Generic[PrimitiveT, RelationT, InstrumentReqT]):
    """Generic operation envelope. Structural fields live here; the primitive-keyed
    iff-rules (relation iff RELATE_*, refs iff DEEM_SATISFIED, parameter iff
    ASSIGN_DUTY_PARAMETER) are bound by the profile in T-CALCULUS."""

    id: str
    primitive: PrimitiveT
    operands: list[str] = Field(default_factory=list)
    outputs: list[str] = Field(default_factory=list)
    arity: int
    inverse: str | None = None
    scope: OperationScope = "duty_level"
    diagnostics_triggering: list[str] = Field(default_factory=list)
    normative_load: NormativeLoad = "low"
    actor_with_authority: list[str] = Field(default_factory=list)
    instrument_required: InstrumentReqT | None = None
    relation: RelationT | None = None
    satisfied_ref: str | None = None
    satisfying_ref: str | None = None
    conditions: list[str] = Field(default_factory=list)
    parameter: DutyParameter | None = None


def validate_iff_rules(
    *,
    primitive: Enum,
    relation: Enum | None,
    satisfied_ref: str | None,
    satisfying_ref: str | None,
    conditions: Sequence[str],
    parameter: str | None,
    relate_primitive: Enum,
    deem_primitive: Enum,
    param_primitive: Enum,
) -> None:
    """The three envelope iff-rules (AGENTS §5), generic over which primitive triggers
    each. A profile binds the trigger members; this is the profile-independent logic.

    - ``relation`` set **iff** primitive is the RELATE primitive.
    - ``satisfied_ref``/``satisfying_ref``/``conditions`` set **iff** DEEM_SATISFIED,
      and for DEEM both refs are required and ``conditions`` non-empty (§2.12 model half).
    - ``parameter`` set **iff** primitive is ASSIGN_DUTY_PARAMETER.
    """
    if (relation is not None) != (primitive == relate_primitive):
        raise ValueError(f"relation must be set iff primitive is {relate_primitive.value}")

    is_deem = primitive == deem_primitive
    has_deem_fields = (
        satisfied_ref is not None or satisfying_ref is not None or len(conditions) > 0
    )
    if is_deem:
        if satisfied_ref is None or satisfying_ref is None or len(conditions) == 0:
            raise ValueError(
                "DEEM_SATISFIED requires satisfied_ref, satisfying_ref, and non-empty conditions"
            )
    elif has_deem_fields:
        raise ValueError(
            "satisfied_ref/satisfying_ref/conditions may be set iff primitive is DEEM_SATISFIED"
        )

    if (parameter is not None) != (primitive == param_primitive):
        raise ValueError(f"parameter must be set iff primitive is {param_primitive.value}")
