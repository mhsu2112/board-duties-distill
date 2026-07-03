"""Lex-Balanus profile models: DutySpec, the instrument graph, and the profile-bound
Operation / Finding concretizations.

``DutySpec`` inherits ``SnapshotBearing`` so a spec without snapshots fails validation
(invariant §2.1). ``InstrumentGraph`` implements the core ``GraphStore`` protocol; its
``baseline_for`` is the deterministic baseline lookup the classifier diffs against.
"""

from __future__ import annotations

from datetime import date
from typing import Literal, Self

import networkx as nx
from pydantic import Field, model_validator

from distillcore.models.base import LegalClaim, SnapshotBearing, StrictModel
from distillcore.models.calculus import Operation, validate_iff_rules
from distillcore.models.review import Finding

from .enums import (
    STRATUM_RANK,
    Cadence,
    Consequence,
    InstrumentRequired,
    LegalForce,
    NormativeKind,
    PrimitiveOp,
    RelationType,
    TreatmentStatus,
    VerbStandard,
)

# Profile-bound concretizations of the generic core envelopes.
BankingFinding = Finding[NormativeKind]


class BankingOperation(Operation[PrimitiveOp, RelationType, InstrumentRequired]):
    """The banking Operation: the generic envelope with the primitive-keyed iff-rules
    bound to this profile's trigger members (RELATE_OBLIGATION / DEEM_SATISFIED /
    ASSIGN_DUTY_PARAMETER)."""

    @model_validator(mode="after")
    def _check_iff_rules(self) -> Self:
        validate_iff_rules(
            primitive=self.primitive,
            relation=self.relation,
            satisfied_ref=self.satisfied_ref,
            satisfying_ref=self.satisfying_ref,
            conditions=self.conditions,
            parameter=self.parameter,
            relate_primitive=PrimitiveOp.RELATE_OBLIGATION,
            deem_primitive=PrimitiveOp.DEEM_SATISFIED,
            param_primitive=PrimitiveOp.ASSIGN_DUTY_PARAMETER,
        )
        return self

Entity = Literal["BHC", "IDI", "both"]
Layer = Literal["as_built", "intended"]

# Instrument treatments that mean "no longer in force" once their treatment_date passes.
_TERMINAL_TREATMENTS: frozenset[TreatmentStatus] = frozenset(
    {
        TreatmentStatus.SUPERSEDED,
        TreatmentStatus.RESCINDED_FORMAL,
        TreatmentStatus.RESCINDED_INFORMAL,
    }
)


class DutySpec(SnapshotBearing):
    """A single board duty, as-built or intended. Snapshots are mandatory (§2.1)."""

    duty_id: str
    label: str
    layer: Layer
    cluster: str | None = None
    source: str | None = None
    board_level: str
    director_class: str
    entity: Entity
    verb_standard: VerbStandard
    object: str
    cadence: Cadence
    trigger: str | None = None
    legal_force: LegalForce
    consequence: Consequence
    instrument_id: str
    currency_status: TreatmentStatus
    source_citations: list[str] = Field(default_factory=list)
    claims: list[LegalClaim] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)


class ConceptGrounding(StrictModel):
    """Span evidence tying a ``concept_ref`` node to an underlying instrument node (B4-T4).

    A concept node is never free-floating: every one carries ≥1 grounding whose ``quote`` is a
    verbatim span from ``source_id``'s cached text, pinning the concept to a real instrument."""

    instrument_id: str  # id of the underlying InstrumentNode
    source_id: str  # cached source the quote is drawn from
    quote: str  # verbatim span evidence


class InstrumentNode(StrictModel):
    """A node in the instrument hierarchy graph. Structurally a core ``BaselineNode``.

    ``kind == "concept_ref"`` marks a B4-T4 concept node — an operand-level concept the reform
    levers cite (e.g. ``SOX-404b-attestation``) that no single duty row carries. It ``bears_on``
    the concept operand string(s) so ``baseline_for`` can answer for the levers, and is
    ``grounded_to`` its underlying instrument node(s) with span evidence."""

    id: str
    citation: str
    agency: str
    stratum: LegalForce
    effective_date: date
    treatment_status: TreatmentStatus
    treatment_date: date | None = None
    treatment_evidence: str | None = None
    bears_on: list[str] = Field(default_factory=list)
    kind: Literal["instrument", "concept_ref"] = "instrument"
    grounded_to: list[ConceptGrounding] = Field(default_factory=list)


class InstrumentEdge(StrictModel):
    """A directed edge in the instrument graph (e.g. restates / supersedes / cross-refs)."""

    source: str
    target: str
    kind: str = "bears_on"


class InstrumentGraph(StrictModel):
    """The in-memory instrument hierarchy. Implements ``GraphStore`` (§5)."""

    nodes: list[InstrumentNode] = Field(default_factory=list)
    edges: list[InstrumentEdge] = Field(default_factory=list)

    def to_networkx(self) -> nx.DiGraph:
        """Materialize the graph (edges carry ``kind``; nodes carry the model)."""
        graph = nx.DiGraph()
        for node in self.nodes:
            graph.add_node(node.id, node=node)
        for edge in self.edges:
            graph.add_edge(edge.source, edge.target, kind=edge.kind)
        return graph

    def _valid_at(self, node: InstrumentNode, as_of: date) -> bool:
        if node.effective_date > as_of:
            return False
        if node.treatment_status == TreatmentStatus.STALE_UNVERIFIED:
            return False
        retired = (
            node.treatment_status in _TERMINAL_TREATMENTS
            and node.treatment_date is not None
            and node.treatment_date <= as_of
        )
        return not retired

    def baseline_for(self, target_ref: str, as_of: date) -> InstrumentNode | None:
        """Highest-stratum, active, as-of-valid node bearing on ``target_ref``, else None.

        Deterministic: candidates are scanned in insertion order and ``max`` returns the
        first node at the winning stratum, so ties resolve to the earliest-declared node.
        """
        candidates = [
            node
            for node in self.nodes
            if target_ref in node.bears_on and self._valid_at(node, as_of)
        ]
        if not candidates:
            return None
        return max(candidates, key=lambda node: STRATUM_RANK[node.stratum])
