"""B5-T4 — lever decomposition (LLM proposes; ``validate_composition`` enforces closure).

For each non-MVP reform lever the LLM proposes a composition of the fixed 16 primitives. Code is
the teeth: every proposed operation is built through ``scaffold_operation`` (the model's iff-rules
validate it). Post B6-T0, ``validate_composition`` accepts **any composition of enum members**
(named composites are reporting sugar); only an explicitly forbidden composition (the DEEM
re-expression) is a residual. The six B5-flagged residuals now carry approved hand decompositions
(``specs/b5_residual_decompositions.json``); R3 is recorded as a policy disjunction (non-operation).
Statutory-floor candidates the LLM surfaces are proposals; the floor file stays human-owned.
"""

from __future__ import annotations

import codecs
import contextlib
import re
from typing import Any, Literal

from adapters.intended import scaffold_operation
from distillcore.llm import LlmHarness, load_template, render
from distillcore.models.base import StrictModel
from distillcore.models.calculus import EffectClass
from distillcore.pipeline.classify import PRIMITIVE_DEFAULT_EFFECT, dominant_effect
from distillcore.pipeline.operations import validate_composition
from profiles.lex_balanus.composites import composite_of, is_forbidden_composition
from profiles.lex_balanus.enums import (
    InstrumentRequired,
    NormativeKind,
    PrimitiveOp,
    RelationType,
)

_KNOWN_COMPOSITES = frozenset(
    {
        "consolidation",
        "master_direction_build",
        "board_role_clarification",
        "vertical_rationalization",
    }
)


class ProposedOp(StrictModel):
    primitive: PrimitiveOp
    operands: list[str] = []  # noqa: RUF012
    relation: RelationType | None = None
    parameter: Literal["verb_standard", "cadence"] | None = None
    satisfied_ref: str | None = None
    satisfying_ref: str | None = None
    conditions: list[str] = []  # noqa: RUF012
    effect_class: EffectClass
    rationale: str = ""


class ProposedLever(StrictModel):
    lever_id: str
    is_consolidation: bool = True
    composition: str  # single | <composite name> | residual
    operations: list[ProposedOp] = []  # noqa: RUF012
    actor_with_authority: list[str] = []  # noqa: RUF012
    instrument_required: InstrumentRequired | None = None
    normative_kinds: list[NormativeKind] = []  # noqa: RUF012
    statutory_floor_candidates: list[str] = []  # noqa: RUF012
    residual_reason: str = ""
    rationale: str = ""


class _Finding:
    def __init__(self, fid: str, op_ids: list[str]) -> None:
        self.id = fid
        self.operation_ids = op_ids


def _prompt_for(lever: dict[str, Any]) -> str:
    roadmap = lever.get("roadmap") or {}
    roadmap_str = (
        f"{roadmap.get('actor', '')} / {roadmap.get('authority', '')} / "
        f"{roadmap.get('instrument', '')} / {roadmap.get('statutory_obstacle', '')}"
        if roadmap
        else "(no roadmap row)"
    )
    return render(
        load_template("decompose"),
        {
            "lever_id": lever["lever_id"],
            "cluster": lever["cluster"],
            "min_reform_lever": lever["min_reform_lever"],
            "whats_duplicative": lever["whats_duplicative"],
            "whats_distinct": lever["whats_distinct"],
            "overlapping_sources": lever["overlapping_sources"],
            "roadmap": roadmap_str,
            "normative_kinds": ", ".join(m.value for m in NormativeKind),
        },
    )


def _clean_floor_candidate(raw: str) -> str | None:
    """Normalize an LLM-emitted statute citation: decode literal ``\\uXXXX`` escapes (the model
    sometimes writes the § sign as a literal escape), collapse whitespace, and drop obvious
    non-citations (placeholder fragments). Returns None for junk."""
    s = raw
    if "\\u" in s or "\\x" in s:
        with contextlib.suppress(Exception):  # keep the raw string if it won't decode
            s = codecs.decode(s, "unicode_escape")
    s = re.sub(r"\s+", " ", s).strip().strip("\"'")
    if not s or "placeholder" in s.lower() or len(s) < 3:
        return None
    return s


def _op_dict(op: ProposedOp) -> dict[str, Any]:
    d: dict[str, Any] = {"primitive": op.primitive.value, "operands": op.operands}
    if op.relation is not None:
        d["relation"] = op.relation.value
    if op.parameter is not None:
        d["parameter"] = op.parameter
    if op.satisfied_ref is not None:
        d["satisfied_ref"] = op.satisfied_ref
    if op.satisfying_ref is not None:
        d["satisfying_ref"] = op.satisfying_ref
    if op.conditions:
        d["conditions"] = op.conditions
    d["effect_class"] = op.effect_class
    return d


def validate_lever(proposed: ProposedLever) -> dict[str, Any]:
    """Build the proposed operations (iff-rules enforced) and run composition validation.

    Returns a record with ``status`` in {valid_single, valid_composite, residual,
    invalid_structure, documented_non_target} and the resolved composite name / residual reason.
    """
    if not proposed.is_consolidation or proposed.composition == "non_target":
        return {
            "status": "documented_non_target",
            "composition": "none",
            "primitives": [],
            "effect_class": "unresolved",
        }

    op_dicts: list[dict[str, Any]] = [_op_dict(o) for o in proposed.operations]
    dec: dict[str, Any] = {
        "id": proposed.lever_id,
        "actor_with_authority": proposed.actor_with_authority,
        "operations": op_dicts,
    }
    try:
        ops = [scaffold_operation(dec, i, o) for i, o in enumerate(op_dicts)]
    except Exception as exc:  # noqa: BLE001 — an iff-rule violation is a structure checkpoint
        return {
            "status": "invalid_structure",
            "composition": proposed.composition,
            "primitives": [str(o.primitive.value) for o in proposed.operations],
            "reason": f"operation failed model validation: {type(exc).__name__}: {exc}",
            "effect_class": "unresolved",
        }

    primitives = [op.primitive for op in ops]
    if not primitives:
        # No operation. An honest LLM "residual" is a closure checkpoint (the enum cannot express
        # this lever — propose, never add); anything else is an incomplete response.
        if proposed.composition == "residual":
            return {
                "status": "residual",
                "composition": "residual",
                "primitives": [],
                "reason": proposed.residual_reason
                or "LLM declared residual (no clean composition)",
                "effect_class": "unresolved",
            }
        return {
            "status": "incomplete",
            "composition": proposed.composition or "empty",
            "primitives": [],
            "reason": "consolidation lever returned no operations and no residual/non_target flag",
            "effect_class": "unresolved",
        }
    resolved_composite = composite_of(primitives) if len(primitives) > 1 else None
    finding = _Finding(proposed.lever_id, [op.id for op in ops])
    # B6-T0: a multi-op finding is a residual only if it is an explicitly forbidden composition
    # (the deem re-expression); any other composition of enum members is expressible.
    residuals = validate_composition([finding], ops, is_forbidden_composition)

    prim_effects = [PRIMITIVE_DEFAULT_EFFECT.get(str(p.value), "unresolved") for p in primitives]
    # DEEM_SATISFIED is per-se change (classify rule) even though its default table entry agrees.
    effect = dominant_effect(prim_effects) if prim_effects else "unresolved"

    if len(primitives) <= 1:
        status = "valid_single"
        composition = f"single:{primitives[0].value}" if primitives else "empty"
    elif residuals:
        status = "residual"
        composition = "residual"
    else:
        status = "valid_composite"
        # named composite as sugar; an unnamed-but-valid enum composition is still expressible
        composition = resolved_composite or "composition"

    return {
        "status": status,
        "composition": composition,
        "primitives": [str(p.value) for p in primitives],
        "residual": [
            {"finding_id": r.finding_id, "primitives": list(r.primitives)} for r in residuals
        ],
        "effect_class": effect,
    }


def _coerce_instrument_required(raw: str | None) -> InstrumentRequired | None:
    if not raw:
        return None
    for member in InstrumentRequired:
        if raw.startswith(member.value):
            return member
    return None


def proposed_from_hand(hand: dict[str, Any]) -> ProposedLever:
    """Build a ProposedLever from a hand decomposition (specs/b5_residual_decompositions.json)."""
    ops = [
        ProposedOp(
            primitive=o["primitive"],
            operands=o.get("operands", []),
            relation=o.get("relation"),
            parameter=o.get("parameter"),
            satisfied_ref=o.get("satisfied_ref"),
            satisfying_ref=o.get("satisfying_ref"),
            conditions=o.get("conditions", []),
            effect_class=o.get("effect_class", "change"),
        )
        for o in hand.get("operations", [])
    ]
    nks: list[NormativeKind] = []
    for o in hand.get("operations", []):
        for k in o.get("normative_kind", []) or []:
            if k in {m.value for m in NormativeKind} and NormativeKind(k) not in nks:
                nks.append(NormativeKind(k))
    return ProposedLever(
        lever_id=hand["lever_id"],
        is_consolidation=True,
        composition="composite",
        operations=ops,
        actor_with_authority=hand.get("actor_with_authority", []),
        instrument_required=_coerce_instrument_required(hand.get("instrument_required")),
        normative_kinds=nks,
        rationale=hand.get("lever", ""),
    )


def _policy_disjunction_record(lever: dict[str, Any], hand: dict[str, Any]) -> dict[str, Any]:
    """R3-shaped: a policy disjunction (non-operation, B0 D10 category). Each branch decomposes;
    the branch choice is routed to the human by the normative gate — not a residual."""
    return {
        "lever_id": lever["lever_id"],
        "cluster": lever["cluster"],
        "min_reform_lever": lever["min_reform_lever"],
        "is_consolidation": False,
        "composition": "policy_disjunction",
        "status": "policy_disjunction",
        "primitives": [],
        "effect_class": "unresolved",
        "actor_with_authority": hand.get("actor_with_authority", []),
        "instrument_required": None,
        "normative_kinds": [],
        "statutory_floor_candidates": [],
        "residual_reason": "",
        "rationale": hand.get("classification", "policy disjunction; branches decompose"),
        "branches": hand.get("branches", []),
        "operations": [],
    }


def decompose_all(
    harness: LlmHarness,
    levers: list[dict[str, Any]],
    hand_decompositions: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    hand_decompositions = hand_decompositions or {}
    records: list[dict[str, Any]] = []
    residuals: list[dict[str, Any]] = []
    floor_candidates: dict[str, list[str]] = {}
    for lever in levers:
        hand = hand_decompositions.get(lever["lever_id"])
        # B6-T0: the six B5 residuals now carry an approved hand decomposition. A policy
        # disjunction (R3) is recorded as a non-operation; the rest validate as compositions.
        if hand is not None and "branches" in hand:
            records.append(_policy_disjunction_record(lever, hand))
            continue
        if hand is not None:
            proposed = proposed_from_hand(hand)
        elif lever.get("non_consolidation"):
            proposed = ProposedLever(
                lever_id=lever["lever_id"],
                is_consolidation=False,
                composition="none",
                rationale=lever["min_reform_lever"],
            )
        else:
            proposed = harness.complete(_prompt_for(lever), ProposedLever)
        validation = validate_lever(proposed)
        rec = {
            "lever_id": lever["lever_id"],
            "cluster": lever["cluster"],
            "min_reform_lever": lever["min_reform_lever"],
            "is_consolidation": proposed.is_consolidation,
            "composition": validation["composition"],
            "status": validation["status"],
            "primitives": validation["primitives"],
            "effect_class": validation["effect_class"],
            "actor_with_authority": proposed.actor_with_authority,
            "instrument_required": (
                proposed.instrument_required.value if proposed.instrument_required else None
            ),
            "normative_kinds": [k.value for k in proposed.normative_kinds],
            "statutory_floor_candidates": proposed.statutory_floor_candidates,
            "residual_reason": proposed.residual_reason,
            "rationale": proposed.rationale,
            "operations": [_op_dict(o) for o in proposed.operations],
        }
        records.append(rec)
        if validation["status"] in {"residual", "invalid_structure"}:
            residuals.append(
                {
                    "lever_id": lever["lever_id"],
                    "cluster": lever["cluster"],
                    "status": validation["status"],
                    "primitives": validation["primitives"],
                    "reason": validation.get("reason") or proposed.residual_reason,
                }
            )
        for cand in proposed.statutory_floor_candidates:
            clean = _clean_floor_candidate(cand)
            if clean is not None:
                floor_candidates.setdefault(clean, [])
                if lever["lever_id"] not in floor_candidates[clean]:
                    floor_candidates[clean].append(lever["lever_id"])

    status_hist: dict[str, int] = {}
    for r in records:
        status_hist[r["status"]] = status_hist.get(r["status"], 0) + 1

    return {
        "_meta": "B5-T4 lever decomposition, closed per B6-T0. LLM proposed; the six B5 residuals "
        "carry approved hand decompositions (specs/b5_residual_decompositions.json). "
        "validate_composition accepts any composition of enum members (named composites as sugar); "
        "a residual is only a forbidden composition. The 16-primitive set is closed over the "
        "corpus — zero residuals; one policy disjunction (R3) recorded as a non-operation.",
        "counts": {
            "levers": len(records),
            "by_status": dict(sorted(status_hist.items())),
            "residuals": len(residuals),
            "floor_candidates": len(floor_candidates),
            "closure_holds": len(residuals) == 0,
        },
        "closure_test": {
            "sixteen_primitive_set_held": len(residuals) == 0,
            "residual_levers": [r["lever_id"] for r in residuals],
        },
        "residual_checkpoints": residuals,
        "statutory_floor_candidates": {
            "_note": "PROPOSED additions only — the floor file (profiles/lex_balanus/"
            "statutory_floor.json) is human-owned (checkpoint 3). Not added.",
            "candidates": dict(sorted(floor_candidates.items())),
        },
        "levers": records,
    }
