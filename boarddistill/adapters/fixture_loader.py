"""Load and validate a fixture directory into typed models.

A fixture dir holds five files (engine FIXTURE_NOTES conventions, banking variant):
- ``sources.json``          -> ``{"sources": [SourceSpan, ...]}``
- ``instrument_graph.json`` -> ``InstrumentGraph``
- ``as_built.json``         -> ``{"duties": [DutySpec, ...]}``
- ``intended.json``         -> ``{"duties": [DutySpec, ...]}``
- ``gold_findings.json``    -> ``{"operations": [BankingOperation], "findings": [BankingFinding]}``

``load_fixture`` performs schema validation (via ``model_validate``); ``validate_bundle``
adds the referential checks the ``validate-fixtures`` CLI reports on.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from distillcore.models.base import SourceSpan
from profiles.lex_balanus.models import (
    BankingFinding,
    BankingOperation,
    DutySpec,
    InstrumentGraph,
)


@dataclass(frozen=True)
class FixtureBundle:
    """A fully-parsed fixture: specs, graph, sources, and the gold operations/findings."""

    name: str
    sources: list[SourceSpan]
    instrument_graph: InstrumentGraph
    as_built: list[DutySpec]
    intended: list[DutySpec]
    gold_operations: list[BankingOperation]
    gold_findings: list[BankingFinding]


def _read_json(path: Path) -> dict[str, object]:
    data: dict[str, object] = json.loads(path.read_text())
    return data


def load_fixture(directory: Path) -> FixtureBundle:
    """Parse and schema-validate a fixture directory. Raises on any schema violation."""
    sources_raw = _read_json(directory / "sources.json")["sources"]
    as_built_raw = _read_json(directory / "as_built.json")["duties"]
    intended_raw = _read_json(directory / "intended.json")["duties"]
    gold_raw = _read_json(directory / "gold_findings.json")

    sources = [SourceSpan.model_validate(s) for s in _as_list(sources_raw)]
    graph = InstrumentGraph.model_validate(_read_json(directory / "instrument_graph.json"))
    as_built = [DutySpec.model_validate(d) for d in _as_list(as_built_raw)]
    intended = [DutySpec.model_validate(d) for d in _as_list(intended_raw)]
    operations = [BankingOperation.model_validate(o) for o in _as_list(gold_raw["operations"])]
    findings = [BankingFinding.model_validate(f) for f in _as_list(gold_raw["findings"])]

    return FixtureBundle(
        name=directory.name,
        sources=sources,
        instrument_graph=graph,
        as_built=as_built,
        intended=intended,
        gold_operations=operations,
        gold_findings=findings,
    )


def _as_list(value: object) -> list[object]:
    if not isinstance(value, list):
        raise TypeError(f"expected a JSON array, got {type(value).__name__}")
    return value


def validate_bundle(bundle: FixtureBundle) -> list[str]:
    """Referential-integrity problems beyond schema validation. Empty list = clean."""
    problems: list[str] = []
    source_ids = {s.id for s in bundle.sources}
    op_ids = {op.id for op in bundle.gold_operations}
    duty_ids = {d.duty_id for d in bundle.as_built} | {d.duty_id for d in bundle.intended}
    intended_ids = {d.duty_id for d in bundle.intended}

    for duty in [*bundle.as_built, *bundle.intended]:
        for cite in duty.source_citations:
            if cite not in source_ids:
                problems.append(f"duty {duty.duty_id}: source_citation {cite!r} not a known span")
        for claim in duty.claims:
            if not claim.source_span_ids:
                problems.append(f"duty {duty.duty_id}: claim {claim.id} has no source span (§2.2)")
            for span in claim.source_span_ids:
                if span not in source_ids:
                    problems.append(f"claim {claim.id}: span {span!r} not in sources.json")

    for finding in bundle.gold_findings:
        for oid in finding.operation_ids:
            if oid not in op_ids:
                problems.append(f"finding {finding.id}: operation {oid!r} not in gold operations")
        if finding.baseline is None and finding.effect_class != "unresolved":
            problems.append(
                f"finding {finding.id}: effect {finding.effect_class!r} with no baseline (§2.3)"
            )

    for op in bundle.gold_operations:
        if str(op.primitive) == "DEEM_SATISFIED":
            for ref in (op.satisfied_ref, op.satisfying_ref):
                if ref is not None and ref not in duty_ids:
                    problems.append(f"op {op.id}: DEEM ref {ref!r} resolves to no duty")
                if ref is not None and ref not in intended_ids:
                    problems.append(f"op {op.id}: DEEM ref {ref!r} must survive intended (§2.12)")
    return problems
