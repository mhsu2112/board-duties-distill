"""B3-T4 — diagnose + classify (offline): mechanical consolidation-finding classification,
diagnostic anchoring, and the B0-vs-LLM duplicate divergence."""

from __future__ import annotations

from typing import Any

from adapters.diagnose import (
    Diagnostic,
    DiagnosticSet,
    _decomp_normative_kinds,
    b0_duplicate_pairs,
    consolidation_finding,
    diagnostic_anchor_ok,
    diagnostic_finding,
    duplicate_divergence,
    llm_duplicate_pairs,
)
from adapters.intended import scaffold_operations
from profiles.lex_balanus.models import DutySpec, InstrumentGraph

_SNAP = {
    "inventory_as_of": "2026-06-05",
    "consolidation_as_of": "2026-06-30",
    "current_as_of": "2026-07-01",
}


def _spec(duty_id: str, layer: str, force: str, **kw: Any) -> DutySpec:
    base: dict[str, Any] = {
        "duty_id": duty_id,
        "label": duty_id,
        "layer": layer,
        "board_level": "board",
        "director_class": "all",
        "entity": "both",
        "verb_standard": "none_specified",
        "object": "x",
        "cadence": "none_specified",
        "legal_force": force,
        "consequence": "none_specified",
        "instrument_id": "i",
        "currency_status": "active",
        "confidence": 0.5,
        "snapshot_dates": _SNAP,
    }
    base.update(kw)
    return DutySpec.model_validate(base)


_DEC_DEEM: dict[str, Any] = {
    "id": "D1",
    "cluster": "Risk-governance framework / strategy",
    "lever": "deem lever",
    "actor_with_authority": ["FRB"],
    "operations": [
        {
            "primitive": "DEEM_SATISFIED",
            "satisfied_ref": "b:RGC-07",
            "satisfying_ref": "b:RGC-02",
            "conditions": ["same risk profile"],
            "effect_class": "change",
            "normative_kind": ["policy_choice", "not_a_real_kind"],
        }
    ],
}


def _graph_covering(target: str) -> InstrumentGraph:
    return InstrumentGraph.model_validate(
        {
            "nodes": [
                {
                    "id": "n1",
                    "citation": "12 CFR Part 252",
                    "agency": "FRB",
                    "stratum": "regulation",
                    "effective_date": "2014-06-01",
                    "treatment_status": "active",
                    "bears_on": [target],
                }
            ],
            "edges": [],
        }
    )


def test_decomp_normative_kinds_filters_to_enum() -> None:
    # "not_a_real_kind" is dropped; only enum members survive.
    assert _decomp_normative_kinds(_DEC_DEEM) == ["policy_choice"]


def test_consolidation_finding_deem_is_change_and_in_review() -> None:
    ops = scaffold_operations(_DEC_DEEM)
    ab = {"b:RGC-02": _spec("b:RGC-02", "as_built", "regulation"),
          "b:RGC-07": _spec("b:RGC-07", "as_built", "guidance")}
    intended = {"i:D1": _spec("i:D1", "intended", "regulation")}
    graph = _graph_covering("b:RGC-07")  # target = as_built_ref = first resolved operand
    f = consolidation_finding(_DEC_DEEM, ops, ab, intended, graph)
    assert f.effect_class == "change"  # DEEM_SATISFIED rule
    assert f.disposition_state == "needs_review"
    assert [str(k) for k in f.normative_kind] == ["policy_choice"]


def test_consolidation_finding_no_baseline_is_unresolved() -> None:
    ops = scaffold_operations(_DEC_DEEM)
    ab = {"b:RGC-02": _spec("b:RGC-02", "as_built", "regulation"),
          "b:RGC-07": _spec("b:RGC-07", "as_built", "guidance")}
    intended = {"i:D1": _spec("i:D1", "intended", "regulation")}
    empty_graph = InstrumentGraph.model_validate({"nodes": [], "edges": []})
    f = consolidation_finding(_DEC_DEEM, ops, ab, intended, empty_graph)
    assert f.effect_class == "unresolved"  # no baseline ⇒ never guessed
    assert f.baseline is None


def test_diagnostic_anchor_whitespace_insensitive_and_catches_fabrication() -> None:
    corpus = "The audit committee shall meet at least annually with the auditor."
    ok = Diagnostic.model_validate({"kind": "undefined_term", "target_ids": ["b:AUD-01"],
                                    "evidence_quote": "meet at least  annually", "rationale": "r"})
    bad = Diagnostic.model_validate({"kind": "undefined_term", "target_ids": ["b:AUD-01"],
                                     "evidence_quote": "the board shall hire a consultant",
                                     "rationale": "r"})
    assert diagnostic_anchor_ok(ok, corpus) is True
    assert diagnostic_anchor_ok(bad, corpus) is False


def test_diagnostic_finding_is_unresolved_and_in_review() -> None:
    d = Diagnostic.model_validate({"kind": "duplicate_duty",
                                   "target_ids": ["b:AUD-01", "b:AUD-02"],
                                   "evidence_quote": "", "normative_kind": ["policy_choice"],
                                   "rationale": "dup"})
    f = diagnostic_finding("Audit committee & independence", 0, d, anchor_ok=True)
    assert f.effect_class == "unresolved"  # 0-op diagnostic
    assert f.disposition_state == "needs_review"
    assert f.as_built_ref == "b:AUD-01"


def test_b0_duplicate_pairs_from_relate_and_deem() -> None:
    decs = [
        {"operations": [
            {"primitive": "RELATE_OBLIGATION", "operands": ["b:RGC-02", "b:RGC-07", "x-concept"]},
            {
                "primitive": "DEEM_SATISFIED",
                "satisfied_ref": "b:CAP-01",
                "satisfying_ref": "b:CAP-02",
            },
        ]}
    ]
    inv = {"b:RGC-02", "b:RGC-07", "b:CAP-01", "b:CAP-02"}
    pairs = b0_duplicate_pairs(decs, inv)
    assert frozenset({"b:RGC-02", "b:RGC-07"}) in pairs  # concept-ref excluded from pairs
    assert frozenset({"b:CAP-01", "b:CAP-02"}) in pairs
    assert all("x-concept" not in p for p in pairs)


def test_duplicate_divergence_records_both_directions() -> None:
    decs = [
        {"operations": [{"primitive": "RELATE_OBLIGATION", "operands": ["b:RGC-02", "b:RGC-07"]}]}
    ]
    ds = DiagnosticSet.model_validate({
        "cluster": "c",
        "diagnostics": [
            {"kind": "duplicate_duty", "target_ids": ["b:AUD-01", "b:AUD-02"],
             "evidence_quote": "", "rationale": "r"},
        ],
    })
    div = duplicate_divergence(decs, [ds], inventory={"b:RGC-02", "b:RGC-07"})
    assert div["counts"]["b0_only"] == 1  # RGC pair unseen by LLM
    assert div["counts"]["llm_only"] == 1  # AUD pair unseen by B0
    assert div["counts"]["agreed"] == 0


def test_llm_duplicate_pairs_expands_triples() -> None:
    ds = DiagnosticSet.model_validate({
        "cluster": "c",
        "diagnostics": [
            {"kind": "duplicate_duty", "target_ids": ["a", "b", "c"], "evidence_quote": "",
             "rationale": "r"},
            {"kind": "undefined_term", "target_ids": ["d"], "evidence_quote": "", "rationale": "r"},
        ],
    })
    pairs = llm_duplicate_pairs([ds])
    assert pairs == {frozenset({"a", "b"}), frozenset({"a", "c"}), frozenset({"b", "c"})}
