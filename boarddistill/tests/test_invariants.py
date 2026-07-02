"""T3 — invariant gates. Covers tests #1, #2, #5, #7, #8, #9."""

from __future__ import annotations

from datetime import date
from typing import Any

from distillcore.models.base import LegalClaim
from distillcore.pipeline.classify import classify_parameter_assignment
from distillcore.pipeline.invariants import (
    can_finalize,
    check_no_baseline_guess,
)
from profiles.lex_balanus.enums import LegalForce
from profiles.lex_balanus.invariants import (
    check_apa_pathway,
    check_binding_force_conservation,
    check_statutory_floor,
    deem_against_floor_op_ids,
)
from profiles.lex_balanus.models import BankingFinding, BankingOperation, DutySpec


def _claim(cid: str, spans: list[str], status: str = "unverified") -> LegalClaim:
    return LegalClaim.model_validate(
        {
            "id": cid,
            "claim": "the board shall approve",
            "source_span_ids": spans,
            "support_type": "quoted",
            "authority_type": "regulation",
            "as_of_valid": True,
            "confidence": 0.9,
            "verifier_status": status,
        }
    )


def _finding(**over: Any) -> BankingFinding:
    base: dict[str, Any] = {
        "id": "f",
        "provision": "P",
        "operation_ids": [],
        "effect_class": "change",
        "rationale": "r",
        "confidence": 0.8,
    }
    base.update(over)
    return BankingFinding.model_validate(base)


def _op(**over: Any) -> BankingOperation:
    base: dict[str, Any] = {"id": "op", "primitive": "REPEAL", "arity": 1, "operands": ["d1"]}
    base.update(over)
    return BankingOperation.model_validate(base)


def _duty(duty_id: str, force: str) -> DutySpec:
    return DutySpec.model_validate(
        {
            "duty_id": duty_id,
            "label": duty_id,
            "layer": "as_built",
            "snapshot_dates": {
                "inventory_as_of": date(2026, 6, 1),
                "consolidation_as_of": date(2026, 6, 30),
                "current_as_of": date(2026, 7, 1),
            },
            "board_level": "full_board",
            "director_class": "any",
            "entity": "BHC",
            "verb_standard": "approve",
            "object": "x",
            "cadence": "annual",
            "legal_force": force,
            "consequence": "supervisory_finding",
            "instrument_id": "i",
            "currency_status": "active",
            "confidence": 0.9,
        }
    )


# ---- #1: a spanless claim blocks final --------------------------------------------


def test_spanless_claim_blocks_final() -> None:
    finding = _finding(effect_class="clarify", normative_kind=[])
    ok, blockers = can_finalize(finding, [_claim("c1", [], status="verified")])
    assert not ok
    assert any("missing source span" in b for b in blockers)


# ---- #2: normative finding with unresolved disposition blocks final ---------------


def test_normative_unresolved_blocks_final() -> None:
    finding = _finding(
        effect_class="change",
        normative_kind=["policy_choice"],
        disposition_state="needs_review",
    )
    ok, blockers = can_finalize(finding, [_claim("c1", ["s1"], status="verified")])
    assert not ok
    assert any("open normative item" in b for b in blockers)

    resolved = _finding(
        effect_class="change",
        normative_kind=["policy_choice"],
        disposition_state="reviewer_accepted",
    )
    ok2, blockers2 = can_finalize(resolved, [_claim("c1", ["s1"], status="verified")])
    assert ok2
    assert blockers2 == []


# ---- #5: no baseline => effect_class must be "unresolved" --------------------------


def test_no_baseline_forces_unresolved() -> None:
    guessed = _finding(id="g", effect_class="change", baseline=None)
    assert check_no_baseline_guess([guessed])  # a change with no baseline is a violation
    honest = _finding(id="h", effect_class="unresolved", baseline=None)
    assert check_no_baseline_guess([honest]) == []


# ---- #7: binding-force conversion + APA pathway -----------------------------------


def test_force_conversion_declared_passes_undeclared_fails() -> None:
    operand_forces = [LegalForce.GUIDANCE, LegalForce.GUIDANCE]
    output_force = LegalForce.REGULATION  # guidance -> regulation, a real conversion
    declared = _finding(effect_class="change", force_conversion_declared=True)
    assert check_binding_force_conservation(declared, operand_forces, output_force) == []

    undeclared = _finding(effect_class="change", force_conversion_declared=False)
    violations = check_binding_force_conservation(undeclared, operand_forces, output_force)
    assert any(v.code == "undeclared_force_conversion" for v in violations)


def test_apa_guidance_action_for_binding_change_fails() -> None:
    finding = _finding(effect_class="change")
    guidance_op = _op(id="gop", primitive="RELOCATE", instrument_required="guidance_action")
    fails = check_apa_pathway(finding, [guidance_op], target_is_binding=True)
    assert any(v.code == "apa_guidance_for_binding" for v in fails)

    rule_op = _op(id="rop", primitive="RELOCATE", instrument_required="rule_apa")
    passes = check_apa_pathway(finding, [rule_op], target_is_binding=True)
    assert passes == []

    no_instrument = _op(id="nop", primitive="RELOCATE")
    missing = check_apa_pathway(finding, [no_instrument], target_is_binding=False)
    assert any(v.code == "apa_missing_instrument" for v in missing)


# ---- #8: statutory floor -----------------------------------------------------------


def test_repeal_of_statute_duty_is_hard_block() -> None:
    duties = {"S1": _duty("S1", "statute")}
    repeal = _op(id="rep", primitive="REPEAL", operands=["S1"])
    violations = check_statutory_floor([repeal], duties, floor_ids=frozenset())
    assert any(v.code == "statutory_floor" for v in violations)


def test_deem_against_floor_passes_but_needs_review() -> None:
    duties = {"S1": _duty("S1", "statute"), "R1": _duty("R1", "regulation")}
    deem = _op(
        id="deem",
        primitive="DEEM_SATISFIED",
        operands=[],
        satisfied_ref="S1",
        satisfying_ref="R1",
        conditions=["external attestation retained"],
    )
    # not a floor-removing op -> no hard block
    assert check_statutory_floor([deem], duties, floor_ids=frozenset()) == []
    # but must be routed to review
    assert deem_against_floor_op_ids([deem], duties, floor_ids=frozenset()) == ["deem"]


# ---- #9: ASSIGN_DUTY_PARAMETER effect semantics -----------------------------------


def test_parameter_assignment_effect_branches() -> None:
    # implicit / none_specified -> codify|clarify (parameter-anchoring-dependent)
    assert classify_parameter_assignment(prior_explicit=False, param_anchored=True) == "codify"
    assert classify_parameter_assignment(prior_explicit=False, param_anchored=False) == "clarify"
    # re-assigning an explicit parameter -> change per se
    assert classify_parameter_assignment(prior_explicit=True, param_anchored=True) == "change"
    assert classify_parameter_assignment(prior_explicit=True, param_anchored=False) == "change"
