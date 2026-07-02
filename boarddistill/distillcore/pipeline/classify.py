"""Effect-class helpers (profile-independent).

Two pieces of the classifier land early because the invariants depend on them (§6):
the per-se force-conversion rule (also demanded, as a declaration, by §2.9) and the
ASSIGN_DUTY_PARAMETER effect semantics. The full baseline-diff classifier is wired in T5.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import date
from typing import Any

from ..models.base import SourceSpan
from ..models.calculus import EffectClass
from .protocols import DutyLike, FindingLike, GraphLike, OperationLike

# Per-primitive default effect where no harder rule (force conversion / no baseline /
# parameter re-assignment) applies. Keyed by primitive *name* so it stays profile-neutral.
PRIMITIVE_DEFAULT_EFFECT: dict[str, EffectClass] = {
    "MERGE": "codify",
    "SPLIT": "clarify",
    "INTRODUCE": "fill_gap",
    "REPEAL": "codify",
    "RELOCATE": "change",
    "RELATE_OBLIGATION": "clarify",
    "RELATE_OFFENSE": "clarify",
    "CANONICALIZE_DEFINITION": "change",
    "DEFINE_TERM": "clarify",
    "SUBSTITUTE_TERM": "codify",
    "NORMALIZE_ELEMENTS": "codify",
    "FACTOR_EXCEPTION": "clarify",
    "REGRADE": "change",
    "ELEVATE_GENERAL_RULE": "codify",
    "RESOLVE_CROSS_REFERENCE": "codify",
    "DEEM_SATISFIED": "change",
}

_SEVERITY: dict[EffectClass, int] = {
    "change": 4,
    "clarify": 3,
    "fill_gap": 2,
    "codify": 1,
    "unresolved": 0,
}

# Primitives that actually move content across strata (so a force conversion is
# attributable to them). A parameter/deem/relate op sharing a converted duty does not
# itself convert force — the relocation does.
FORCE_MOVING_PRIMITIVES: frozenset[str] = frozenset(
    {"RELOCATE", "MERGE", "ELEVATE_GENERAL_RULE"}
)

# The value that means a parameter was left unspecified in the as-built spec.
_UNSPECIFIED = "none_specified"
# Which duty attribute each ASSIGN_DUTY_PARAMETER parameter reads.
_PARAM_ATTR = {"verb_standard": "verb_standard", "cadence": "cadence"}


def is_force_conversion(operand_forces: Sequence[Any], output_force: Any) -> bool:
    """True iff the output legal force differs from *all* operand duties' forces — the
    per-se binding-force conversion (§2.9). Empty operands ⇒ not a conversion."""
    return len(operand_forces) > 0 and all(output_force != force for force in operand_forces)


def classify_parameter_assignment(*, prior_explicit: bool, param_anchored: bool) -> EffectClass:
    """Effect of an ASSIGN_DUTY_PARAMETER (§6).

    Re-assigning an already-explicit parameter is ``change`` per se. Assigning where the
    parameter was implicit / none_specified is ``codify`` when a baseline already anchors
    that parameter value (making the implicit standard explicit) and ``clarify`` otherwise.
    Note ``param_anchored`` is about the *parameter*, not the finding's overall baseline.
    """
    if prior_explicit:
        return "change"
    return "codify" if param_anchored else "clarify"


def dominant_effect(effects: Sequence[EffectClass]) -> EffectClass:
    """The most severe effect among a finding's operations (change > clarify > fill_gap
    > codify > unresolved)."""
    return max(effects, key=lambda e: _SEVERITY[e])


def _target_ref(finding: FindingLike, operations: Sequence[OperationLike]) -> str | None:
    if finding.as_built_ref is not None:
        return finding.as_built_ref
    if finding.intended_ref is not None:
        return finding.intended_ref
    for op in operations:
        if op.operands:
            return op.operands[0]
    return None


def _baseline_span(node: Any) -> SourceSpan:
    return SourceSpan(id=f"baseline-{node.id}", source_id=str(node.id), citation=str(node.citation))


def _param_prior_explicit(op: OperationLike, as_built: Mapping[str, DutyLike]) -> bool:
    attr = _PARAM_ATTR.get(str(op.parameter)) if op.parameter is not None else None
    if attr is None or not op.operands:
        return False
    duty = as_built.get(op.operands[0])
    if duty is None:
        return False
    return str(getattr(duty, attr)) != _UNSPECIFIED


def classify_finding(
    finding: FindingLike,
    operations: Sequence[OperationLike],
    as_built: Mapping[str, DutyLike],
    intended: Mapping[str, DutyLike],
    graph: GraphLike,
    as_of: date,
) -> tuple[EffectClass, SourceSpan | None]:
    """Compute a finding's effect class and baseline deterministically.

    Order of rules: no baseline ⇒ ``unresolved`` (never guess); a binding-force
    conversion ⇒ ``change``; ASSIGN_DUTY_PARAMETER ⇒ the parameter rule; DEEM_SATISFIED ⇒
    ``change``; otherwise the most severe per-primitive default.
    """
    target = _target_ref(finding, operations)
    node = graph.baseline_for(target, as_of) if target is not None else None
    if node is None:
        return "unresolved", None
    baseline = _baseline_span(node)

    output_force = (
        intended[finding.intended_ref].legal_force
        if finding.intended_ref is not None and finding.intended_ref in intended
        else None
    )
    for op in operations:
        if str(op.primitive) not in FORCE_MOVING_PRIMITIVES:
            continue
        operand_forces = [as_built[o].legal_force for o in op.operands if o in as_built]
        if output_force is not None and is_force_conversion(operand_forces, output_force):
            return "change", baseline

    primitives = [str(op.primitive) for op in operations]
    if "ASSIGN_DUTY_PARAMETER" in primitives:
        param_op = next(op for op in operations if str(op.primitive) == "ASSIGN_DUTY_PARAMETER")
        prior_explicit = _param_prior_explicit(param_op, as_built)
        effect = classify_parameter_assignment(prior_explicit=prior_explicit, param_anchored=False)
        return effect, baseline
    if "DEEM_SATISFIED" in primitives:
        return "change", baseline
    if not primitives:
        return "unresolved", baseline
    effects = [PRIMITIVE_DEFAULT_EFFECT.get(p, "unresolved") for p in primitives]
    return dominant_effect(effects), baseline


def compute_disposition(
    *,
    effect: EffectClass,
    primitives: Sequence[str],
    normative_kind: Sequence[Any],
    cross_stratum: bool,
    force_conversion: bool,
    deem_against_floor: bool,
) -> str:
    """The default disposition (§2.8 and profile rules): a change / REGRADE / normative /
    cross-stratum / force-converting / floor-touching finding starts in review."""
    if (
        effect == "change"
        or "REGRADE" in primitives
        or len(normative_kind) > 0
        or cross_stratum
        or force_conversion
        or deem_against_floor
    ):
        return "needs_review"
    return "auto_ok"
