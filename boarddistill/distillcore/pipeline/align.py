"""Align stage: the as-built ↔ intended crosswalk (unchanged / modified / new / removed),
by duty id and a fixed set of comparable fields. Deterministic (sorted by duty id)."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from .protocols import DutyLike

_COMPARED_FIELDS = ("legal_force", "verb_standard", "cadence", "object", "board_level")


@dataclass(frozen=True)
class Alignment:
    duty_id: str
    status: str  # "unchanged" | "modified" | "new" | "removed"
    changed_fields: tuple[str, ...]


def _changed(a: DutyLike, b: DutyLike) -> tuple[str, ...]:
    return tuple(f for f in _COMPARED_FIELDS if getattr(a, f) != getattr(b, f))


def align(as_built: Sequence[DutyLike], intended: Sequence[DutyLike]) -> list[Alignment]:
    ab = {d.duty_id: d for d in as_built}
    it = {d.duty_id: d for d in intended}
    out: list[Alignment] = []
    for duty_id in sorted(ab.keys() | it.keys()):
        if duty_id in ab and duty_id in it:
            changed = _changed(ab[duty_id], it[duty_id])
            out.append(Alignment(duty_id, "modified" if changed else "unchanged", changed))
        elif duty_id in it:
            out.append(Alignment(duty_id, "new", ()))
        else:
            out.append(Alignment(duty_id, "removed", ()))
    return out
