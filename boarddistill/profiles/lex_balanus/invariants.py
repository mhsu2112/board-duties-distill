"""Banking-profile invariants (AGENTS §2 items 9-12) and the statutory-floor loader.

These consume the core ``InvariantViolation`` shape. The pipeline (T5) assembles the
per-finding context (operand duties, output force, target binding, surviving intended
ids) and calls these checks.
"""

from __future__ import annotations

import json
from collections.abc import Sequence
from functools import lru_cache
from pathlib import Path
from typing import Any

from distillcore.pipeline.classify import is_force_conversion
from distillcore.pipeline.invariants import InvariantViolation

from .enums import InstrumentRequired, LegalForce
from .models import BankingFinding, BankingOperation, DutySpec

_FLOOR_PATH = Path(__file__).resolve().parent / "statutory_floor.json"

# Primitives that would remove a duty (the statutory floor forbids these on floor duties).
_FLOOR_REMOVING_PRIMITIVES = frozenset({"REPEAL", "MERGE"})


@lru_cache(maxsize=1)
def load_statutory_floor() -> dict[str, Any]:
    """The human-owned statutory-floor definition (draft v1; TODO(human) §14.4)."""
    data: dict[str, Any] = json.loads(_FLOOR_PATH.read_text())
    return data


def floor_duty_ids() -> frozenset[str]:
    """The explicit floor duty-id list (in addition to any statute-stratum duty)."""
    return frozenset(load_statutory_floor().get("floor_duty_ids", []))


def _is_floor_duty(duty: DutySpec, floor_ids: frozenset[str]) -> bool:
    return duty.legal_force == LegalForce.STATUTE or duty.duty_id in floor_ids


def check_binding_force_conservation(
    finding: BankingFinding,
    operand_forces: Sequence[LegalForce],
    output_force: LegalForce,
) -> list[InvariantViolation]:
    """§2.9 (per-se): if the output force differs from all operand forces, the finding is
    ``change`` mechanically and must declare the conversion. Undeclared ⇒ violation."""
    if not is_force_conversion(operand_forces, output_force):
        return []
    violations: list[InvariantViolation] = []
    if finding.effect_class != "change":
        violations.append(
            InvariantViolation(
                "force_conversion_not_change",
                finding.id,
                "binding-force conversion must be classified change",
            )
        )
    if not finding.force_conversion_declared:
        violations.append(
            InvariantViolation(
                "undeclared_force_conversion",
                finding.id,
                "binding-force conversion must set force_conversion_declared=True (§2.9)",
            )
        )
    return violations


def check_statutory_floor(
    operations: Sequence[BankingOperation],
    duties_by_id: dict[str, DutySpec],
    floor_ids: frozenset[str] | None = None,
) -> list[InvariantViolation]:
    """§2.10 (hard block): no REPEAL or MERGE may remove a statute-stratum or floor duty."""
    ids = floor_duty_ids() if floor_ids is None else floor_ids
    violations: list[InvariantViolation] = []
    for op in operations:
        if str(op.primitive) not in _FLOOR_REMOVING_PRIMITIVES:
            continue
        for operand_id in op.operands:
            duty = duties_by_id.get(operand_id)
            if duty is not None and _is_floor_duty(duty, ids):
                violations.append(
                    InvariantViolation(
                        "statutory_floor",
                        op.id,
                        f"{op.primitive} would remove floor duty {operand_id}",
                    )
                )
    return violations


def deem_against_floor_op_ids(
    operations: Sequence[BankingOperation],
    duties_by_id: dict[str, DutySpec],
    floor_ids: frozenset[str] | None = None,
) -> list[str]:
    """§2.10: DEEM_SATISFIED against a floor duty is permitted (the duty survives) but
    always ``needs_review``. Returns those op ids so the pipeline can force review."""
    ids = floor_duty_ids() if floor_ids is None else floor_ids
    flagged: list[str] = []
    for op in operations:
        if str(op.primitive) != "DEEM_SATISFIED":
            continue
        for ref in (op.satisfied_ref, op.satisfying_ref):
            duty = duties_by_id.get(ref) if ref is not None else None
            if duty is not None and _is_floor_duty(duty, ids):
                flagged.append(op.id)
                break
    return flagged


def check_apa_pathway(
    finding: BankingFinding,
    operations_of_finding: Sequence[BankingOperation],
    target_is_binding: bool,
) -> list[InvariantViolation]:
    """§2.11: a ``change`` must carry a non-null ``instrument_required``; a binding change
    via ``guidance_action`` is not a lawful pathway."""
    if finding.effect_class != "change":
        return []
    instruments = [
        op.instrument_required for op in operations_of_finding if op.instrument_required is not None
    ]
    violations: list[InvariantViolation] = []
    if not instruments:
        violations.append(
            InvariantViolation(
                "apa_missing_instrument",
                finding.id,
                "change-class finding must carry a non-null instrument_required",
            )
        )
    if target_is_binding and InstrumentRequired.GUIDANCE_ACTION in instruments:
        violations.append(
            InvariantViolation(
                "apa_guidance_for_binding",
                finding.id,
                "guidance_action is not a lawful pathway for a binding change (§2.11)",
            )
        )
    return violations


def check_deem_survival(
    operation: BankingOperation,
    intended_duty_ids: frozenset[str],
) -> list[InvariantViolation]:
    """§2.12 (survival half): both refs of a DEEM_SATISFIED must survive in the intended
    spec (distinct from MERGE, which collapses to one). The model half — both refs present,
    conditions non-empty — is enforced on ``BankingOperation``."""
    if str(operation.primitive) != "DEEM_SATISFIED":
        return []
    violations: list[InvariantViolation] = []
    for ref in (operation.satisfied_ref, operation.satisfying_ref):
        if ref is not None and ref not in intended_duty_ids:
            violations.append(
                InvariantViolation(
                    "deem_survival",
                    operation.id,
                    f"DEEM_SATISFIED ref {ref!r} does not survive in the intended spec",
                )
            )
    return violations
