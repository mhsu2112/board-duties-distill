"""B3-T3 — the intended layer: express the B0 decompositions as intended DutySpecs +
Operation records.

Operations are **scaffolded** from ``b0_decompositions.json`` (not re-derived): each B0
operation maps to one ``BankingOperation``, operands preserved verbatim — including the
hand-authored concept-refs and ranges (``b:AUD-01..03``, ``SOX-404b-attestation``), which
are reported as unresolved rather than silently normalized (unresolved-over-guess). One B0
term is amended: ``ASSIGN_DUTY_STANDARD`` → ``ASSIGN_DUTY_PARAMETER`` (B0 TODO-2, resolved
2026-07-02), with the assigned standard carried as the ``verb_standard`` parameter.

The LLM's only job is to draft the consolidated duty *language* for each decomposition —
an **illustrative** consolidation (NG2: non-authoritative), citing every operand. All
structural DutySpec fields are derived deterministically from the operands or left neutral;
nothing is finalized.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from distillcore.llm import LlmHarness, load_template, render
from distillcore.models.base import LegalClaim, StrictModel
from profiles.lex_balanus.enums import (
    STRATUM_RANK,
    Cadence,
    Consequence,
    LegalForce,
    PrimitiveOp,
    RelationType,
    TreatmentStatus,
    VerbStandard,
)
from profiles.lex_balanus.models import BankingOperation, DutySpec

# B0 TODO-2 (resolved 2026-07-02): ASSIGN_DUTY_STANDARD is the pre-amendment name for the
# generalized ASSIGN_DUTY_PARAMETER over {verb_standard, cadence}.
_PRIMITIVE_ALIASES: dict[str, PrimitiveOp] = {
    "ASSIGN_DUTY_STANDARD": PrimitiveOp.ASSIGN_DUTY_PARAMETER,
}

_DEFAULT_SNAPSHOT = {
    "inventory_as_of": "2026-06-05",
    "consolidation_as_of": "2026-06-30",
    "current_as_of": "2026-07-01",
}

# legal_force → authority_type (same vocabulary for the strata a claim may cite).
_FORCE_TO_AUTHORITY = {
    "statute": "statute",
    "regulation": "regulation",
    "enforceable_guideline": "enforceable_guideline",
    "guidance": "guidance",
    "manual": "manual",
}


# --- operation scaffolding -------------------------------------------------------------


def _map_primitive(raw: str) -> PrimitiveOp:
    if raw in _PRIMITIVE_ALIASES:
        return _PRIMITIVE_ALIASES[raw]
    return PrimitiveOp(raw)  # raises ValueError on an unknown primitive (a §14.2 checkpoint)


def scaffold_operation(dec: dict[str, Any], index: int, op: dict[str, Any]) -> BankingOperation:
    """Map one B0 operation dict to a structurally-valid ``BankingOperation`` (the model's
    iff-rules are the teeth). Operands are preserved verbatim."""
    raw = op["primitive"]
    prim = _map_primitive(raw)
    operands = list(op.get("operands", []))
    kwargs: dict[str, Any] = {
        "id": f"op-{dec['id']}-{index}",
        "primitive": prim,
        "operands": operands,
        "actor_with_authority": list(dec.get("actor_with_authority", [])),
        "normative_load": "high" if op.get("effect_class") == "change" else "low",
        "arity": len(operands) if operands else (2 if prim == PrimitiveOp.DEEM_SATISFIED else 1),
    }
    if prim == PrimitiveOp.RELATE_OBLIGATION:
        kwargs["relation"] = RelationType(op["relation"])
    if prim == PrimitiveOp.DEEM_SATISFIED:
        kwargs["satisfied_ref"] = op["satisfied_ref"]
        kwargs["satisfying_ref"] = op["satisfying_ref"]
        kwargs["conditions"] = list(op.get("conditions", []))
    if prim == PrimitiveOp.ASSIGN_DUTY_PARAMETER:
        # ASSIGN_DUTY_STANDARD carried a verb standard; ASSIGN_DUTY_PARAMETER a named param.
        kwargs["parameter"] = op.get("parameter") or "verb_standard"
    return BankingOperation.model_validate(kwargs)


def scaffold_operations(dec: dict[str, Any]) -> list[BankingOperation]:
    return [scaffold_operation(dec, i, op) for i, op in enumerate(dec.get("operations", []))]


# --- operand resolution ----------------------------------------------------------------


def operation_refs(op: BankingOperation) -> list[str]:
    refs = list(op.operands)
    if op.satisfied_ref:
        refs.append(op.satisfied_ref)
    if op.satisfying_ref:
        refs.append(op.satisfying_ref)
    return refs


def resolution_report(ops: list[BankingOperation], inventory_ids: set[str]) -> dict[str, Any]:
    """Split every operand/ref into resolved (a clean inventory row ID) vs. unresolved
    (a hand-authored concept-ref / range). Unresolved refs are documented, not fabricated."""
    resolved: set[str] = set()
    unresolved: set[str] = set()
    for op in ops:
        for ref in operation_refs(op):
            (resolved if ref in inventory_ids else unresolved).add(ref)
    return {
        "resolved": sorted(resolved),
        "unresolved": sorted(unresolved),
        "counts": {"resolved": len(resolved), "unresolved": len(unresolved)},
    }


# --- LLM I/O schema --------------------------------------------------------------------


class IntendedDraft(StrictModel):
    """The LLM's illustrative (NG2) consolidation for one decomposition."""

    decomposition_id: str
    label: str
    object: str
    consolidated_text: str
    operands_cited: list[str] = []  # noqa: RUF012
    notes: str = ""


# --- intended DutySpec assembly --------------------------------------------------------


def _derive_entity(operands: list[str], drafts: dict[str, Any]) -> str:
    entities = {drafts[o]["entity"] for o in operands if o in drafts and "entity" in drafts[o]}
    if entities == {"IDI"}:
        return "IDI"
    if entities == {"BHC"}:
        return "BHC"
    return "both"


def _derive_force(operands: list[str], drafts: dict[str, Any]) -> str:
    forces = [
        drafts[o]["legal_force"]
        for o in operands
        if o in drafts and "legal_force" in drafts[o]
    ]
    if not forces:
        return "guidance"
    return str(max(forces, key=lambda f: STRATUM_RANK[LegalForce(f)]))


def build_intended_spec(
    dec: dict[str, Any], draft: IntendedDraft, operands: list[str], drafts: dict[str, Any]
) -> DutySpec:
    """Assemble the intended (illustrative, NG2) consolidated DutySpec. ``operands`` is the
    complete, deterministic citation set from the operations (every operand is cited, not
    only the ones the LLM echoed). Structural fields are derived from resolved operands or
    left neutral; verb/cadence are ``none_specified`` (a lever pins no single verb or timing)."""
    force = _derive_force(operands, drafts)
    claim = LegalClaim.model_validate(
        {
            "id": f"claim-i:{dec['id']}",
            "claim": f"[illustrative consolidation — NG2] {draft.consolidated_text}",
            "source_span_ids": [],  # illustrative; operands are cited in source_citations
            "support_type": "paraphrased",
            "authority_type": _FORCE_TO_AUTHORITY[force],
            "as_of_valid": False,
            "confidence": 0.4,
            "verifier_status": "unverified",
        }
    )
    return DutySpec.model_validate(
        {
            "duty_id": f"i:{dec['id']}",
            "label": f"[illustrative consolidation — NG2] {draft.label}",
            "layer": "intended",
            "cluster": dec.get("cluster"),
            "source": dec.get("lever"),
            "board_level": "board",
            "director_class": "all_directors",
            "entity": _derive_entity(operands, drafts),
            "verb_standard": VerbStandard.NONE_SPECIFIED.value,
            "object": draft.object,
            "cadence": Cadence.NONE_SPECIFIED.value,
            "trigger": None,
            "legal_force": force,
            "consequence": Consequence.NONE_SPECIFIED.value,
            "instrument_id": str(dec.get("instrument_required", "")),
            "currency_status": TreatmentStatus.ACTIVE.value,
            "source_citations": operands,
            "claims": [claim.model_dump(mode="json")],
            "confidence": 0.4,
            "snapshot_dates": _DEFAULT_SNAPSHOT,
        }
    )


# --- driver ----------------------------------------------------------------------------


@dataclass
class IntendedResult:
    dec_id: str
    cluster: str
    spec: DutySpec
    operations: list[BankingOperation]
    resolution: dict[str, Any]
    operand_coverage_ok: bool  # LLM cited every operand it was given


def _prompt_for(dec: dict[str, Any], ops: list[BankingOperation], drafts: dict[str, Any]) -> str:
    op_lines = []
    for op in ops:
        refs = ", ".join(operation_refs(op)) or "(no operands)"
        op_lines.append(f"- {op.primitive.value}: {refs}")
    operand_labels = []
    for ref in sorted({r for op in ops for r in operation_refs(op)}):
        label = drafts.get(ref, {}).get("label", "") if isinstance(drafts.get(ref), dict) else ""
        operand_labels.append(f"- {ref}: {label}" if label else f"- {ref}")
    return render(
        load_template("intended"),
        {
            "dec_id": dec["id"],
            "cluster": str(dec.get("cluster", "")),
            "lever": str(dec.get("lever", "")),
            "instrument_required": str(dec.get("instrument_required", "")),
            "operations": "\n".join(op_lines),
            "operands": "\n".join(operand_labels),
        },
    )


def _all_operands(ops: list[BankingOperation]) -> list[str]:
    seen: list[str] = []
    for op in ops:
        for ref in operation_refs(op):
            if ref not in seen:
                seen.append(ref)
    return seen


def build_intended(
    harness: LlmHarness, dec: dict[str, Any], drafts: dict[str, Any], inventory_ids: set[str]
) -> IntendedResult:
    ops = scaffold_operations(dec)
    operands = _all_operands(ops)
    draft = harness.complete(_prompt_for(dec, ops, drafts), IntendedDraft)
    coverage_ok = set(operands).issubset(set(draft.operands_cited)) if operands else True
    return IntendedResult(
        dec_id=dec["id"],
        cluster=str(dec.get("cluster", "")),
        spec=build_intended_spec(dec, draft, operands, drafts),
        operations=ops,
        resolution=resolution_report(ops, inventory_ids),
        operand_coverage_ok=coverage_ok,
    )


def build_all(
    harness: LlmHarness, decompositions: list[dict[str, Any]], drafts: dict[str, Any]
) -> list[IntendedResult]:
    inventory_ids = set(drafts)
    return [
        build_intended(harness, dec, drafts, inventory_ids)
        for dec in decompositions
        if dec.get("operations")
    ]


# --- document --------------------------------------------------------------------------


def intended_document(results: list[IntendedResult]) -> dict[str, Any]:
    total_unresolved = sorted(
        {r for res in results for r in res.resolution["unresolved"]}
    )
    return {
        "_meta": "B3-T3 intended layer. B0 decompositions expressed as illustrative (NG2, "
        "non-authoritative) consolidated DutySpecs + Operation records scaffolded from "
        "b0_decompositions.json (operands verbatim). ASSIGN_DUTY_STANDARD amended to "
        "ASSIGN_DUTY_PARAMETER (B0 TODO-2). Nothing finalized.",
        "counts": {
            "decompositions": len(results),
            "operations": sum(len(r.operations) for r in results),
            "operand_coverage_ok": sum(1 for r in results if r.operand_coverage_ok),
            "unresolved_operand_refs": len(total_unresolved),
        },
        "unresolved_operand_refs": total_unresolved,
        "by_cluster": sorted({r.cluster for r in results}),
        "decompositions": [
            {
                "decomposition_id": r.dec_id,
                "cluster": r.cluster,
                "operand_coverage_ok": r.operand_coverage_ok,
                "resolution": r.resolution,
                "intended_spec": r.spec.model_dump(mode="json"),
                "operations": [op.model_dump(mode="json") for op in r.operations],
            }
            for r in results
        ],
    }
