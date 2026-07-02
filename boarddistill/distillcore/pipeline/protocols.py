"""Structural protocols the pipeline stages read, so ``distillcore`` stays
profile-independent (the banking models satisfy these; the criminal ones will too)."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import date
from typing import Any, Protocol


class DutyLike(Protocol):
    duty_id: str
    layer: Any
    legal_force: Any
    verb_standard: Any
    cadence: Any
    board_level: str
    object: str

    # read-only so a narrower element type (e.g. list[LegalClaim]) matches covariantly
    @property
    def claims(self) -> Sequence[Any]: ...


class OperationLike(Protocol):
    id: str
    primitive: Any
    operands: list[str]
    relation: Any
    satisfied_ref: str | None
    satisfying_ref: str | None
    instrument_required: Any
    parameter: Any


class FindingLike(Protocol):
    id: str
    as_built_ref: str | None
    intended_ref: str | None
    operation_ids: list[str]
    normative_kind: list[Any]
    force_conversion_declared: bool


class GraphLike(Protocol):
    def baseline_for(self, target_ref: str, as_of: date) -> Any: ...
