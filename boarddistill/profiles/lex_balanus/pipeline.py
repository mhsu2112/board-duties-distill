"""Banking pipeline orchestrator (composition root).

Wires the profile-independent stages (distill / align / diagnostics / classify / verify /
operations) to the banking invariants and composite table, and recomputes each finding's
effect class, disposition, and baseline from the specs. The declared operations and the
finding scaffolding (provision, refs, normative_kind, force_conversion_declared) are the
reform input; effect_class / disposition_state / baseline / verifier_records are computed.
"""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

from adapters.fixture_loader import FixtureBundle
from distillcore.models.base import LegalClaim, VerifierRecord, VerifierStatus
from distillcore.models.calculus import Diagnostic
from distillcore.pipeline.align import Alignment, align
from distillcore.pipeline.classify import (
    FORCE_MOVING_PRIMITIVES,
    classify_finding,
    compute_disposition,
    is_force_conversion,
)
from distillcore.pipeline.diagnostics import diagnose
from distillcore.pipeline.distill import distill
from distillcore.pipeline.invariants import InvariantViolation, run_core_invariants
from distillcore.pipeline.operations import Residual, validate_composition
from distillcore.pipeline.verify import verify_claims

from .composites import composite_of
from .enums import is_binding
from .invariants import (
    check_apa_pathway,
    check_binding_force_conservation,
    check_deem_survival,
    check_statutory_floor,
    deem_against_floor_op_ids,
    floor_duty_ids,
)
from .models import BankingFinding, DutySpec


@dataclass(frozen=True)
class RunResult:
    """Everything ``run-fixture`` computes for one bundle."""

    name: str
    computed_findings: list[BankingFinding]
    residuals: list[Residual]
    violations: list[InvariantViolation]
    verifier_records: list[VerifierRecord]
    claim_status: dict[str, VerifierStatus]
    diagnostics: list[Diagnostic]
    alignment: list[Alignment]

    @property
    def ok(self) -> bool:
        return not self.residuals and not self.violations


def run_fixture(bundle: FixtureBundle) -> RunResult:
    if not bundle.as_built:
        raise ValueError(f"fixture {bundle.name!r} has no as-built duties")
    as_of = bundle.as_built[0].snapshot_dates.inventory_as_of

    distill(bundle.as_built, bundle.intended, as_of)  # stage runs; concrete dicts below
    ab = {d.duty_id: d for d in bundle.as_built}
    it = {d.duty_id: d for d in bundle.intended}
    duties_all = {**ab, **it}
    intended_ids = frozenset(it)
    floor_ids = floor_duty_ids()

    alignment = align(bundle.as_built, bundle.intended)
    diagnostics = diagnose(bundle.as_built, bundle.intended, alignment)
    residuals = validate_composition(bundle.gold_findings, bundle.gold_operations, composite_of)

    ops_by_id = {op.id: op for op in bundle.gold_operations}
    deem_floor_ops = set(deem_against_floor_op_ids(bundle.gold_operations, duties_all, floor_ids))

    all_duties = [*bundle.as_built, *bundle.intended]
    verifier_records, claim_status = verify_claims(all_duties, bundle.sources)
    rec_id_by_claim = {r.claim_id: r.id for r in verifier_records}

    violations: list[InvariantViolation] = []
    violations.extend(check_statutory_floor(bundle.gold_operations, duties_all, floor_ids))

    computed: list[BankingFinding] = []
    for declared in bundle.gold_findings:
        ops = [ops_by_id[o] for o in declared.operation_ids if o in ops_by_id]
        effect, baseline = classify_finding(
            declared, ops, ab, it, bundle.instrument_graph, as_of
        )
        primitives = [str(op.primitive) for op in ops]

        output_force = (
            it[declared.intended_ref].legal_force
            if declared.intended_ref is not None and declared.intended_ref in it
            else None
        )
        distinct_forces = {
            str(ab[o].legal_force) for op in ops for o in op.operands if o in ab
        }
        # Force conversion is attributable only to force-moving operations.
        moving_ops = [op for op in ops if str(op.primitive) in FORCE_MOVING_PRIMITIVES]
        moving_operand_forces = [
            ab[o].legal_force for op in moving_ops for o in op.operands if o in ab
        ]
        force_conv = output_force is not None and any(
            is_force_conversion([ab[o].legal_force for o in op.operands if o in ab], output_force)
            for op in moving_ops
        )
        deem_floor = any(op.id in deem_floor_ops for op in ops)

        disposition = compute_disposition(
            effect=effect,
            primitives=primitives,
            normative_kind=declared.normative_kind,
            cross_stratum=len(distinct_forces) > 1,
            force_conversion=force_conv,
            deem_against_floor=deem_floor,
        )

        rec_ids = _verifier_ids_for(declared, duties_all, rec_id_by_claim)
        finding = declared.model_copy(
            update={
                "effect_class": effect,
                "baseline": baseline,
                "disposition_state": disposition,
                "verifier_records": rec_ids,
            }
        )
        computed.append(finding)

        if output_force is not None and moving_operand_forces:
            violations.extend(
                check_binding_force_conservation(finding, moving_operand_forces, output_force)
            )
        target_duty = it.get(declared.intended_ref or "") or ab.get(declared.as_built_ref or "")
        target_binding = is_binding(target_duty.legal_force) if target_duty is not None else False
        violations.extend(check_apa_pathway(finding, ops, target_binding))
        for op in ops:
            violations.extend(check_deem_survival(op, intended_ids))

    all_claims = _dedup_claims(all_duties)
    violations.extend(run_core_invariants(computed, bundle.gold_operations, all_claims).violations)

    return RunResult(
        name=bundle.name,
        computed_findings=computed,
        residuals=residuals,
        violations=violations,
        verifier_records=verifier_records,
        claim_status=claim_status,
        diagnostics=diagnostics,
        alignment=alignment,
    )


def _verifier_ids_for(
    finding: BankingFinding,
    duties_all: Mapping[str, DutySpec],
    rec_id_by_claim: dict[str, str],
) -> list[str]:
    ids: list[str] = []
    for ref in (finding.as_built_ref, finding.intended_ref):
        duty = duties_all.get(ref) if ref is not None else None
        if duty is None:
            continue
        for claim in duty.claims:
            if claim.id in rec_id_by_claim and rec_id_by_claim[claim.id] not in ids:
                ids.append(rec_id_by_claim[claim.id])
    return ids


def _dedup_claims(duties: Sequence[DutySpec]) -> list[LegalClaim]:
    seen: dict[str, LegalClaim] = {}
    for duty in duties:
        for claim in duty.claims:
            seen.setdefault(claim.id, claim)
    return list(seen.values())


def write_outputs(result: RunResult, bundle: FixtureBundle, outdir: Path) -> Path:
    """Write the per-fixture JSON stage outputs (§9). Returns the fixture output dir."""
    dest = outdir / result.name
    dest.mkdir(parents=True, exist_ok=True)

    _dump(dest / "as_built.json", {"duties": [d.model_dump(mode="json") for d in bundle.as_built]})
    _dump(dest / "intended.json", {"duties": [d.model_dump(mode="json") for d in bundle.intended]})
    _dump(dest / "instrument_graph.json", bundle.instrument_graph.model_dump(mode="json"))
    _dump(
        dest / "findings.json",
        {
            "findings": [f.model_dump(mode="json") for f in result.computed_findings],
            "operations": [o.model_dump(mode="json") for o in bundle.gold_operations],
            "residuals": [r.__dict__ for r in result.residuals],
            "invariant_violations": [v.__dict__ for v in result.violations],
            "diagnostics": [d.model_dump(mode="json") for d in result.diagnostics],
        },
    )
    _dump(
        dest / "verification.json",
        {
            "records": [r.model_dump(mode="json") for r in result.verifier_records],
            "claim_status": result.claim_status,
        },
    )
    _dump(
        dest / "review_queue.json",
        {
            "needs_review": [
                {
                    "finding_id": f.id,
                    "provision": f.provision,
                    "effect_class": f.effect_class,
                    "normative_kind": list(f.normative_kind),
                    "disposition_state": f.disposition_state,
                }
                for f in result.computed_findings
                if f.disposition_state == "needs_review"
            ]
        },
    )
    return dest


def _dump(path: Path, data: object) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")
