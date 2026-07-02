"""Composition validation: every finding must reduce to a single primitive or a known
profile composite; anything else is a residual (§10). ``run-fixture`` fails on a
non-empty residual list.

Profile-independent: the composite lookup is injected, so the criminal profile reuses
this unchanged.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Any, Protocol


class _OperationLike(Protocol):
    id: str
    primitive: Any


class _FindingLike(Protocol):
    id: str
    operation_ids: list[str]


@dataclass(frozen=True)
class Residual:
    """A finding the calculus cannot express as one primitive or a known composite —
    a candidate for the §14.2 checkpoint (propose a primitive, never add one silently)."""

    finding_id: str
    primitives: tuple[str, ...]
    reason: str


def validate_composition(
    findings: Sequence[_FindingLike],
    operations: Sequence[_OperationLike],
    resolve_composite: Callable[[Sequence[Any]], str | None],
) -> list[Residual]:
    """Residuals for every finding whose operations are neither a single primitive nor a
    recognized composite. A finding with 0 or 1 operations is always expressible."""
    ops_by_id = {op.id: op for op in operations}
    residuals: list[Residual] = []
    for finding in findings:
        primitives = [ops_by_id[oid].primitive for oid in finding.operation_ids if oid in ops_by_id]
        if len(primitives) <= 1:
            continue
        if resolve_composite(primitives) is None:
            residuals.append(
                Residual(
                    finding_id=finding.id,
                    primitives=tuple(str(p) for p in primitives),
                    reason="not a single primitive or a known composite",
                )
            )
    return residuals
