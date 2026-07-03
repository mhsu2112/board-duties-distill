"""B4-T4 — concept-node graph extension: baseline_for answers for every B0 concept operand,
and every concept is grounded to an instrument with cache-verified span evidence."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import pytest

from adapters.concept_graph import (
    B0_CONCEPT_OPERANDS,
    concept_nodes,
    extend_graph,
    verify_groundings,
)
from profiles.lex_balanus.models import InstrumentGraph

_CACHE = Path(__file__).resolve().parents[1] / "data" / "sources"
_GRAPH_V1 = Path(__file__).resolve().parents[1] / "data" / "graph" / "us-gsib_v1.json"
_AS_OF = date(2026, 6, 30)


def test_concept_nodes_are_typed_and_grounded() -> None:
    nodes = concept_nodes()
    assert nodes, "expected concept nodes"
    for n in nodes:
        assert n.kind == "concept_ref"
        assert n.grounded_to, f"{n.id} is free-floating (no grounding) — checkpoint 3"
        assert n.bears_on, f"{n.id} answers for no operand"


@pytest.mark.skipif(not _CACHE.exists(), reason="source cache absent")
def test_every_grounding_quote_resolves_to_cache() -> None:
    verified = verify_groundings()
    assert all(verified.values()), f"ungrounded quotes: {[k for k, v in verified.items() if not v]}"


@pytest.mark.skipif(not _GRAPH_V1.exists(), reason="graph v1 absent")
def test_baseline_for_answers_every_b0_concept_operand() -> None:
    base = InstrumentGraph.model_validate(json.loads(_GRAPH_V1.read_text())["graph"])
    extended = extend_graph(base)
    for operand in B0_CONCEPT_OPERANDS:
        assert extended.baseline_for(operand, _AS_OF) is not None, f"unanswered operand: {operand}"


@pytest.mark.skipif(not _GRAPH_V1.exists(), reason="graph v1 absent")
def test_extension_preserves_existing_instrument_coverage() -> None:
    base = InstrumentGraph.model_validate(json.loads(_GRAPH_V1.read_text())["graph"])
    extended = extend_graph(base)
    # a real verified duty still resolves to its instrument stratum (concept nodes don't shadow)
    b = extended.baseline_for("b:AUD-02", _AS_OF)
    assert b is not None and str(b.stratum) == "regulation" and b.kind == "instrument"
    # the SR 12-17 grounding target node was added
    assert any(n.id == "sr-12-17" for n in extended.nodes)
