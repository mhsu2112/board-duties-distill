"""T1 — core model shapes, snapshot enforcement, and deterministic schema export."""

from __future__ import annotations

from datetime import date
from enum import Enum

import pytest
from pydantic import ValidationError

from distillcore.export_schema import build_schema, canonical_models
from distillcore.models.base import (
    LegalClaim,
    SnapshotBearing,
    SnapshotDates,
    SourceSpan,
    VerifierRecord,
)
from distillcore.models.calculus import Diagnostic, Operation
from distillcore.models.review import Finding, can_transition


class _Prim(Enum):
    MERGE = "MERGE"
    RELATE = "RELATE"


class _Rel(Enum):
    IMPLEMENTS = "implements"


class _Instr(Enum):
    RULE = "rule_apa"


class _Norm(Enum):
    POLICY = "policy_choice"


def _snapshot() -> SnapshotDates:
    return SnapshotDates(
        inventory_as_of=date(2026, 6, 1),
        consolidation_as_of=date(2026, 6, 30),
        current_as_of=date(2026, 7, 1),
    )


def test_snapshot_bearing_requires_snapshot_dates() -> None:
    with pytest.raises(ValidationError):
        SnapshotBearing()  # type: ignore[call-arg]
    assert SnapshotBearing(snapshot_dates=_snapshot()).snapshot_dates.inventory_as_of == date(
        2026, 6, 1
    )


def test_extra_fields_forbidden() -> None:
    with pytest.raises(ValidationError):
        SourceSpan(id="s1", source_id="src", citation="X", bogus="nope")  # type: ignore[call-arg]


def test_legal_claim_confidence_bounds_and_default_status() -> None:
    claim = LegalClaim(
        id="c1",
        claim="the board shall approve",
        source_span_ids=["s1"],
        support_type="quoted",
        authority_type="regulation",
        as_of_valid=True,
        confidence=0.9,
    )
    assert claim.verifier_status == "unverified"
    with pytest.raises(ValidationError):
        LegalClaim(
            id="c2",
            claim="x",
            support_type="quoted",
            authority_type="statute",
            as_of_valid=True,
            confidence=1.5,
        )


def test_legal_claim_allows_empty_spans_at_construction() -> None:
    # Empty spans are a *verification* failure (§2.2), not a construction error.
    claim = LegalClaim(
        id="c3",
        claim="uncited",
        support_type="paraphrased",
        authority_type="guidance",
        as_of_valid=True,
        confidence=0.5,
    )
    assert claim.source_span_ids == []


def test_operation_envelope_parameterizes_over_profile_enums() -> None:
    op = Operation[_Prim, _Rel, _Instr](
        id="op1",
        primitive=_Prim.MERGE,
        operands=["d1", "d2"],
        outputs=["d3"],
        arity=2,
    )
    assert op.primitive is _Prim.MERGE
    assert op.scope == "duty_level"
    assert op.relation is None


def test_finding_generic_and_effect_class_distinct_from_primitive() -> None:
    finding = Finding[_Norm](
        id="f1",
        provision="Part 363",
        effect_class="change",
        rationale="reassigned explicit cadence",
        normative_kind=[_Norm.POLICY],
        confidence=0.8,
    )
    assert finding.disposition_state == "needs_review"
    assert finding.status == "draft"
    # effect_class is a str literal; primitive is an enum — different types.
    assert finding.effect_class == "change"


def test_disposition_transition_table() -> None:
    assert can_transition("needs_review", "reviewer_accepted")
    assert can_transition("auto_ok", "needs_review")
    assert not can_transition("reviewer_accepted", "needs_review")
    assert not can_transition("auto_ok", "reviewer_accepted")


def test_model_json_round_trip() -> None:
    rec = VerifierRecord(id="v1", claim_id="c1", status="verified", method="span_present")
    assert VerifierRecord.model_validate_json(rec.model_dump_json()) == rec
    diag = Diagnostic(kind="overlap", target_ids=["d1"], rationale="near-identical text")
    assert Diagnostic.model_validate_json(diag.model_dump_json()) == diag


def test_schema_export_is_deterministic_and_covers_core_models() -> None:
    first = build_schema()
    second = build_schema()
    assert first == second
    defs = set(first["$defs"])
    assert {"SnapshotDates", "SourceSpan", "LegalClaim", "VerifierRecord", "Diagnostic"} <= defs
    # models are sorted by name for stable output
    names = [m.__name__ for m in canonical_models()]
    assert names == sorted(names)
