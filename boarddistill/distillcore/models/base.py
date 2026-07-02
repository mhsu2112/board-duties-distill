"""Profile-independent base models: snapshots, spans, claims, verifier records.

These shapes are shared with the engine. Field names on ``SnapshotDates`` are the
banking profile's; ``lex_allium``'s ``before/reform/current`` maps onto the same
three-date type via profile-supplied aliases (see AGENTS §5).
"""

from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

# The seven authority strata a claim may cite (core vocabulary, profile-agnostic).
AuthorityType = Literal[
    "statute",
    "regulation",
    "enforceable_guideline",
    "guidance",
    "manual",
    "comparator",
    "secondary",
]

VerifierStatus = Literal["unverified", "verified", "contradicted"]


class StrictModel(BaseModel):
    """Base for every canonical model: JSON is the source of truth, extras forbidden."""

    model_config = ConfigDict(extra="forbid")


class SnapshotDates(StrictModel):
    """The three snapshot dates every DutySpec must carry (invariant §2.1).

    Distillation runs at ``inventory_as_of`` — never live law (the snapshot rule).
    """

    inventory_as_of: date
    consolidation_as_of: date
    current_as_of: date


class SnapshotBearing(StrictModel):
    """Mixin that makes ``snapshot_dates`` structurally mandatory.

    A spec constructed without snapshots fails validation — the code-level teeth
    behind invariant §2.1 ("Snapshot present").
    """

    snapshot_dates: SnapshotDates


class SourceSpan(StrictModel):
    """A pointer into source text. Every legal claim resolves to >=1 of these."""

    id: str
    source_id: str
    citation: str
    start: int | None = None
    end: int | None = None
    quote: str | None = None


class LegalClaim(StrictModel):
    """A cited legal assertion. Empty ``source_span_ids`` is a verification failure
    (invariant §2.2) — enforced downstream, not silently here."""

    id: str
    claim: str
    source_span_ids: list[str] = Field(default_factory=list)
    support_type: Literal["quoted", "paraphrased"]
    authority_type: AuthorityType
    as_of_valid: bool
    confidence: float = Field(ge=0.0, le=1.0)
    verifier_status: VerifierStatus = "unverified"


class VerifierRecord(StrictModel):
    """The outcome of checking one claim: how it was checked and what it resolved to."""

    id: str
    claim_id: str
    status: VerifierStatus
    method: Literal["span_present", "quote_match", "cross_reference", "manual", "live_retrieval"]
    checked_span_ids: list[str] = Field(default_factory=list)
    note: str | None = None
