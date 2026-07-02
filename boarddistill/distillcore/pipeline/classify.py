"""Effect-class helpers (profile-independent).

Two pieces of the classifier land early because the invariants depend on them (§6):
the per-se force-conversion rule (also demanded, as a declaration, by §2.9) and the
ASSIGN_DUTY_PARAMETER effect semantics. The full baseline-diff classifier is wired in T5.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from ..models.calculus import EffectClass


def is_force_conversion(operand_forces: Sequence[Any], output_force: Any) -> bool:
    """True iff the output legal force differs from *all* operand duties' forces — the
    per-se binding-force conversion (§2.9). Empty operands ⇒ not a conversion."""
    return len(operand_forces) > 0 and all(output_force != force for force in operand_forces)


def classify_parameter_assignment(*, prior_explicit: bool, baseline_present: bool) -> EffectClass:
    """Effect of an ASSIGN_DUTY_PARAMETER (§6).

    Re-assigning an already-explicit parameter is ``change`` per se. Assigning where the
    parameter was implicit / none_specified is ``codify`` when a baseline anchors it
    (making the implicit standard explicit) and ``clarify`` otherwise.
    """
    if prior_explicit:
        return "change"
    return "codify" if baseline_present else "clarify"
