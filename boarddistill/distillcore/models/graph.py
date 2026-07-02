"""The GraphStore protocol: the baseline lookup the classifier diffs against.

Kept profile-independent: the banking ``InstrumentGraph`` (T2) implements this, and
the classifier reads only the structural fields declared on ``BaselineNode``. No
baseline ⇒ the caller must record ``effect_class = "unresolved"`` (invariant §2.3).
"""

from __future__ import annotations

from datetime import date
from typing import Protocol, runtime_checkable


@runtime_checkable
class BaselineNode(Protocol):
    """The minimal shape the classifier needs from a baseline instrument node."""

    id: str
    citation: str
    stratum: str
    treatment_status: str


@runtime_checkable
class GraphStore(Protocol):
    """Resolves the as-built baseline for a duty at a snapshot date."""

    def baseline_for(self, target_ref: str, as_of: date) -> BaselineNode | None:
        """The highest-stratum, active, as-of-valid node bearing on ``target_ref``,
        else ``None`` (no baseline — never guess an effect class)."""
        ...
