"""Diagnostics stage: turn alignment deltas into typed ``Diagnostic`` signals
(force change, cadence change, verb change). These feed the operations/classify stages;
they are evidence, not conclusions."""

from __future__ import annotations

from collections.abc import Sequence

from ..models.calculus import Diagnostic
from .align import Alignment
from .protocols import DutyLike

_FIELD_KIND = {
    "legal_force": "force_change",
    "cadence": "cadence_change",
    "verb_standard": "verb_change",
}


def diagnose(
    as_built: Sequence[DutyLike],
    intended: Sequence[DutyLike],
    alignment: Sequence[Alignment],
) -> list[Diagnostic]:
    ab = {d.duty_id: d for d in as_built}
    it = {d.duty_id: d for d in intended}
    diagnostics: list[Diagnostic] = []
    for al in alignment:
        if al.status != "modified":
            continue
        for field, kind in _FIELD_KIND.items():
            if field in al.changed_fields:
                before = getattr(ab[al.duty_id], field)
                after = getattr(it[al.duty_id], field)
                diagnostics.append(
                    Diagnostic(
                        kind=kind,
                        target_ids=[al.duty_id],
                        rationale=f"{field}: {before} -> {after}",
                    )
                )
    return diagnostics
