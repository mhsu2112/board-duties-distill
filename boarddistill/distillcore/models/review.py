"""Findings, reviewer dispositions, and the disposition state machine.

``Finding`` is generic over the profile's ``NormativeKind`` enum. The state machine
here is the profile-independent transition table; the finalization gates that consume
it (verification, normative gate, floor) are wired in T3/T7.
"""

from __future__ import annotations

from enum import Enum
from typing import Generic, Literal, TypeVar

from pydantic import Field

from .base import SourceSpan, StrictModel
from .calculus import EffectClass

DispositionState = Literal[
    "auto_ok",
    "needs_review",
    "reviewer_accepted",
    "reviewer_rejected",
    "reviewer_modified",
]

FindingStatus = Literal["draft", "final"]

# Allowed disposition transitions. A reviewer resolves an open item; an auto-clean
# finding may still be pulled into review. Reviewer verdicts are terminal (only a
# fresh recompute re-opens them, which rebuilds the finding rather than transitioning).
_TRANSITIONS: dict[DispositionState, frozenset[DispositionState]] = {
    "auto_ok": frozenset({"needs_review"}),
    "needs_review": frozenset(
        {"reviewer_accepted", "reviewer_rejected", "reviewer_modified"}
    ),
    "reviewer_accepted": frozenset(),
    "reviewer_rejected": frozenset(),
    "reviewer_modified": frozenset(),
}

# Dispositions that count as a human having resolved the normative question (§2.6).
RESOLVED_DISPOSITIONS: frozenset[DispositionState] = frozenset(
    {"auto_ok", "reviewer_accepted", "reviewer_rejected", "reviewer_modified"}
)


def can_transition(src: DispositionState, dst: DispositionState) -> bool:
    """True iff ``src -> dst`` is a legal disposition move."""
    return dst in _TRANSITIONS[src]


NormativeT = TypeVar("NormativeT", bound=Enum)


class ReviewDisposition(StrictModel):
    """A record of one reviewer action moving a finding's disposition state."""

    finding_id: str
    from_state: DispositionState
    to_state: DispositionState
    reviewer: str
    note: str | None = None


class Finding(StrictModel, Generic[NormativeT]):
    """A distilled finding. ``effect_class`` is computed by diffing against a baseline;
    no baseline ⇒ ``"unresolved"`` (invariant §2.3). Reaching ``final`` is gated by
    verification and the normative gate (T3)."""

    id: str
    provision: str
    as_built_ref: str | None = None
    intended_ref: str | None = None
    operation_ids: list[str] = Field(default_factory=list)
    effect_class: EffectClass
    rationale: str
    baseline: SourceSpan | None = None
    normative_kind: list[NormativeT] = Field(default_factory=list)
    disposition_state: DispositionState = "needs_review"
    force_conversion_declared: bool = False
    confidence: float = Field(ge=0.0, le=1.0)
    verifier_records: list[str] = Field(default_factory=list)
    status: FindingStatus = "draft"
