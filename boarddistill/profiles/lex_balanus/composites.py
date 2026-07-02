"""Profile composite table and the banking ``decompose()`` / ``composite_of()`` lookups.

A composite is a named, human-approved bundle of primitives (§6). ``DEEM_SATISFIED`` is
atomic: it is never the *name* of a composite and ``decompose()`` refuses to break it
apart. Crucially, no composite re-expresses a deem-satisfaction as
``RESOLVE_CROSS_REFERENCE + FACTOR_EXCEPTION`` — that combination resolves to no
composite, so a finding that tries it is a residual (T5 / test #6).
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass

from distillcore.models.calculus import OperationScope

from .enums import PrimitiveOp, RelationType


@dataclass(frozen=True)
class CompositeStep:
    """One primitive within a composite, with the scope/relation shape it must take."""

    primitive: PrimitiveOp
    scope: OperationScope | None = None
    relation: RelationType | None = None


# Primitives that can never be synthesized from, or broken into, other primitives.
NON_DECOMPOSABLE: frozenset[PrimitiveOp] = frozenset({PrimitiveOp.DEEM_SATISFIED})

# The approved composites (§6). vertical_rationalization is the D8 schema; DEEM_SATISFIED
# rides inside it *intact*, never decomposed.
COMPOSITES: dict[str, tuple[CompositeStep, ...]] = {
    "consolidation": (
        CompositeStep(PrimitiveOp.MERGE),
        CompositeStep(PrimitiveOp.CANONICALIZE_DEFINITION),
        CompositeStep(PrimitiveOp.RESOLVE_CROSS_REFERENCE),
    ),
    "master_direction_build": (
        CompositeStep(PrimitiveOp.INTRODUCE, scope="general_part"),
        CompositeStep(PrimitiveOp.MERGE),
        CompositeStep(PrimitiveOp.REPEAL),
        CompositeStep(PrimitiveOp.RESOLVE_CROSS_REFERENCE),
    ),
    "board_role_clarification": (
        CompositeStep(PrimitiveOp.ASSIGN_DUTY_PARAMETER),
        CompositeStep(PrimitiveOp.SPLIT),
    ),
    "vertical_rationalization": (
        CompositeStep(PrimitiveOp.RELATE_OBLIGATION, relation=RelationType.ENTITY_LEVEL_MIRROR),
        CompositeStep(PrimitiveOp.DEEM_SATISFIED),
        CompositeStep(PrimitiveOp.FACTOR_EXCEPTION),
    ),
}


def decompose(name: str) -> tuple[CompositeStep, ...]:
    """The primitive steps of a named composite.

    Raises for an atomic primitive (e.g. ``DEEM_SATISFIED`` is not decomposable) and for
    an unknown name.
    """
    if name in {p.value for p in NON_DECOMPOSABLE}:
        raise ValueError(f"{name} is atomic and not decomposable")
    if name not in COMPOSITES:
        raise KeyError(f"unknown composite: {name!r}")
    return COMPOSITES[name]


def composite_of(primitives: Iterable[PrimitiveOp]) -> str | None:
    """The composite whose primitive multiset equals ``primitives``, else ``None``.

    Multiset (not order) match, so an operation ordering doesn't matter. Returns ``None``
    for any bundle that is not an approved composite — including the forbidden
    ``{RESOLVE_CROSS_REFERENCE, FACTOR_EXCEPTION}`` deem re-expression.
    """
    want = Counter(primitives)
    for name, steps in COMPOSITES.items():
        if Counter(step.primitive for step in steps) == want:
            return name
    return None
