"""Distill stage. In slice one this is deterministic validation only — the fixture
specs are already typed models, so distillation is identity + indexing. The LLM-backed
distiller lands behind this interface later (README roadmap step 4)."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date

from .protocols import DutyLike


@dataclass(frozen=True)
class DistilledSpecs:
    """Indexed as-built / intended duties at a snapshot date."""

    as_built_by_id: dict[str, DutyLike]
    intended_by_id: dict[str, DutyLike]
    as_of: date


def distill(
    as_built: Sequence[DutyLike],
    intended: Sequence[DutyLike],
    as_of: date,
) -> DistilledSpecs:
    return DistilledSpecs(
        as_built_by_id={d.duty_id: d for d in as_built},
        intended_by_id={d.duty_id: d for d in intended},
        as_of=as_of,
    )
