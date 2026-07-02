"""Core invariant gates (AGENTS §2 items 1-8) and ``can_finalize()``.

Gate 1 (snapshot present) and gate 4 (closed primitive set) are enforced structurally by
the models (``SnapshotBearing`` / the ``PrimitiveOp`` enum) and are not re-checked here.
Gate 5 (effect_class != primitive) is a type-level fact tested in T-CALCULUS. The
remaining gates that need cross-object context — 2, 3, 6, 7, 8 — live here. Profile
invariants (§2.9-2.12) plug in via ``profiles/lex_balanus/invariants.py``.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any

from ..models.base import LegalClaim
from ..models.review import RESOLVED_DISPOSITIONS, Finding
from .operations import _OperationLike


@dataclass(frozen=True)
class InvariantViolation:
    """A violated gate. ``code`` is a stable machine key; ``message`` is human-facing."""

    code: str
    subject_id: str | None
    message: str


@dataclass
class InvariantReport:
    """Aggregated invariant result. ``ok`` iff no violations."""

    violations: list[InvariantViolation] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.violations

    def extend(self, more: Sequence[InvariantViolation]) -> None:
        self.violations.extend(more)


def check_claim_has_span(claims: Sequence[LegalClaim]) -> list[InvariantViolation]:
    """Gate 2: a claim with empty ``source_span_ids`` is a bug — no uncited legal claim."""
    return [
        InvariantViolation("claim_missing_span", claim.id, "legal claim has no source span")
        for claim in claims
        if not claim.source_span_ids
    ]


def check_no_baseline_guess(findings: Sequence[Finding[Any]]) -> list[InvariantViolation]:
    """Gate 3/5: no baseline ⇒ ``effect_class`` must be ``"unresolved"`` (never guessed)."""
    return [
        InvariantViolation(
            "no_baseline_guess",
            finding.id,
            f"effect_class {finding.effect_class!r} asserted with no baseline",
        )
        for finding in findings
        if finding.baseline is None and finding.effect_class != "unresolved"
    ]


def check_change_regrade_disposition(
    findings: Sequence[Finding[Any]],
    operations: Sequence[_OperationLike],
) -> list[InvariantViolation]:
    """Gate 8: a ``change``-class finding, or one carrying a REGRADE op, must not default
    to ``auto_ok`` — it defaults to ``needs_review``."""
    ops_by_id = {op.id: op for op in operations}
    violations: list[InvariantViolation] = []
    for finding in findings:
        primitives = {
            str(ops_by_id[oid].primitive) for oid in finding.operation_ids if oid in ops_by_id
        }
        if (finding.effect_class == "change" or "REGRADE" in primitives) and (
            finding.disposition_state == "auto_ok"
        ):
            violations.append(
                InvariantViolation(
                    "change_regrade_default",
                    finding.id,
                    "change-class / REGRADE finding may not be auto_ok",
                )
            )
    return violations


def run_core_invariants(
    findings: Sequence[Finding[Any]],
    operations: Sequence[_OperationLike],
    claims: Sequence[LegalClaim],
) -> InvariantReport:
    """Run the context-dependent core gates (2, 3/5, 8)."""
    report = InvariantReport()
    report.extend(check_claim_has_span(claims))
    report.extend(check_no_baseline_guess(findings))
    report.extend(check_change_regrade_disposition(findings, operations))
    return report


def can_finalize(
    finding: Finding[Any],
    claims: Sequence[LegalClaim],
) -> tuple[bool, list[str]]:
    """Whether a finding may reach ``final``, and the blockers preventing it.

    Enforces the normative gate (§2.6), the verification gate (§2.7 — any unverified /
    contradicted / spanless claim blocks), and the unresolved-effect gate (§2.3).
    """
    blockers: list[str] = []
    if finding.normative_kind and finding.disposition_state not in RESOLVED_DISPOSITIONS:
        blockers.append(f"open normative item (disposition={finding.disposition_state})")
    if finding.effect_class == "unresolved":
        blockers.append("unresolved effect class")
    for claim in claims:
        if not claim.source_span_ids:
            blockers.append(f"claim {claim.id}: missing source span")
        elif claim.verifier_status != "verified":
            blockers.append(f"claim {claim.id}: {claim.verifier_status}")
    return (not blockers, blockers)
