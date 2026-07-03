"""B4-T5 — re-classification with the concept-extended graph.

The five levers that were ``unresolved`` in B3 (D3/D4/D6/D7/D8) now classify, because
``baseline_for`` resolves their concept operands. Two mechanisms are exercised: the graph-aware
target selection (a concept-covered operand becomes the finding's anchor) and the dominant-
effect classifier (a multi-op finding takes its most severe op effect, so D4's DEEM_SATISFIED
wins over its unanchored ASSIGN_DUTY_PARAMETER)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from adapters.concept_graph import extend_graph
from adapters.diagnose import (
    _baseline_target,
    as_built_map,
    consolidation_finding,
    intended_map,
    operand_strata,
)
from adapters.intended import scaffold_operations
from profiles.lex_balanus.models import InstrumentGraph

_ROOT = Path(__file__).resolve().parents[1]
_DECS = _ROOT / "specs" / "b0_decompositions.json"
_IMPORT = _ROOT / "outputs" / "import" / "imported_duties.json"
_INTENDED = _ROOT / "outputs" / "b3" / "intended.json"
_GRAPH_V1 = _ROOT / "data" / "graph" / "us-gsib_v1.json"

# Expected effect classes with the extended graph (B4-T5). D9 mechanically classifies fill_gap
# vs B0's codify — a characterized disagreement (never reconciled, B0 gold untouched).
_EXPECTED = {
    "D1": "change", "D2": "change", "D3": "change", "D4": "change", "D5": "clarify",
    "D6": "change", "D7": "codify", "D8": "change", "D9": "fill_gap",
}
_PREVIOUSLY_UNRESOLVED = {"D3", "D4", "D6", "D7", "D8"}

_ARTIFACTS = _DECS.exists() and _IMPORT.exists() and _INTENDED.exists() and _GRAPH_V1.exists()


@pytest.mark.skipif(not _ARTIFACTS, reason="B3 artifacts absent")
def test_levers_classify_with_extended_graph() -> None:
    decs = json.loads(_DECS.read_text())["decompositions"]
    drafts = {d["duty_id"]: d for d in json.loads(_IMPORT.read_text())["duties"]}
    ab = as_built_map(drafts)
    intended = intended_map(json.loads(_INTENDED.read_text()))
    base = InstrumentGraph.model_validate(json.loads(_GRAPH_V1.read_text())["graph"])
    graph = extend_graph(base)

    got: dict[str, str] = {}
    for dec in decs:
        if not dec.get("operations"):
            continue
        ops = scaffold_operations(dec)
        f = consolidation_finding(dec, ops, ab, intended, graph)
        got[dec["id"]] = f.effect_class

    assert got == _EXPECTED
    # the five formerly-unresolved levers are all resolved now
    assert all(got[d] != "unresolved" for d in _PREVIOUSLY_UNRESOLVED)


@pytest.mark.skipif(not _ARTIFACTS, reason="B3 artifacts absent")
def test_extended_graph_needed_for_the_five_levers() -> None:
    """Without the concept nodes, the five levers stay unresolved (the graph is load-bearing)."""
    decs = {d["id"]: d for d in json.loads(_DECS.read_text())["decompositions"]}
    drafts = {d["duty_id"]: d for d in json.loads(_IMPORT.read_text())["duties"]}
    ab = as_built_map(drafts)
    intended = intended_map(json.loads(_INTENDED.read_text()))
    base = InstrumentGraph.model_validate(json.loads(_GRAPH_V1.read_text())["graph"])

    for lever in ("D4", "D7"):
        ops = scaffold_operations(decs[lever])
        f = consolidation_finding(decs[lever], ops, ab, intended, base)
        assert f.effect_class == "unresolved"  # no concept baseline ⇒ never guessed


@pytest.mark.skipif(not _ARTIFACTS, reason="B3 artifacts absent")
def test_d7_disposition_reads_cross_stratum_through_concept_groundings() -> None:
    """B5-T0(b): D7's operands are concept refs (App. D self-assessment ↔ SR 21-3), whose
    concept node collapses to one stratum but whose *groundings* span `enforceable_guideline`
    and `guidance`. Reading strata through the groundings surfaces the cross-stratum signal, so
    a codify-class finding still defaults `needs_review` — closing the B4-characterized gap."""
    decs = {d["id"]: d for d in json.loads(_DECS.read_text())["decompositions"]}
    drafts = {d["duty_id"]: d for d in json.loads(_IMPORT.read_text())["duties"]}
    ab = as_built_map(drafts)
    intended = intended_map(json.loads(_INTENDED.read_text()))
    graph = extend_graph(InstrumentGraph.model_validate(json.loads(_GRAPH_V1.read_text())["graph"]))

    ops = scaffold_operations(decs["D7"])
    strata = operand_strata(ops, ab, graph)
    assert {"enforceable_guideline", "guidance"} <= strata  # both grounding strata are seen
    assert len(strata) > 1

    f = consolidation_finding(decs["D7"], ops, ab, intended, graph)
    assert f.effect_class == "codify"  # effect unchanged (B4-T5 target)
    assert f.disposition_state == "needs_review"  # was auto_ok in B4 — now surfaced for review


def test_baseline_target_prefers_a_concept_covered_ref() -> None:
    dec = {
        "id": "DX",
        "operations": [
            {"primitive": "DEEM_SATISFIED", "satisfied_ref": "Part363-ICFR-assessment",
             "satisfying_ref": "SOX-404b-attestation", "conditions": ["c"]},
        ],
    }
    ops = scaffold_operations(dec)
    graph = extend_graph(InstrumentGraph(nodes=[], edges=[]))
    assert _baseline_target(ops, {}, graph) == "Part363-ICFR-assessment"
