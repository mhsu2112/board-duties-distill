"""B2-T6 — instrument-graph v1 built from the committed cache."""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from adapters.graph_build import build_instrument_graph, graph_document, instrument_key

_XLSX = (
    Path(__file__).resolve().parents[2]
    / "Synthesis"
    / "gsib-board_duties-combined_inventory.xlsx"
)
_CACHE = Path(__file__).resolve().parents[1] / "data" / "sources"


def test_instrument_key_normalization() -> None:
    assert instrument_key("ecfr-t12-p363", "12 CFR 363.5") == "12 CFR Part 363"
    assert instrument_key("ecfr-t12-p30", "12 CFR Part 30, App. D, II.A") == "12 CFR Part 30 App. D"
    assert instrument_key("sr-21-3-att", "SR 21-3 attachment") == "SR 21-3"
    assert instrument_key("usc-t12-s1831m", "12 U.S.C. 1831m") == "12 U.S.C. 1831m"


@pytest.mark.skipif(not _XLSX.exists() or not _CACHE.exists(), reason="xlsx or cache absent")
def test_graph_covers_every_verified_duty_and_flags_supersession() -> None:
    from adapters.b1_targets import select_targets
    from adapters.inventory_xlsx import import_inventory
    from adapters.resolvers import build_resolver
    from adapters.retrieval import Fetcher, offline_client
    from distillcore.pipeline.verify import verify_targets

    duties = [d.model_dump(mode="json") for d in import_inventory(_XLSX).duties]
    rows = verify_targets(select_targets(duties), build_resolver(Fetcher(_CACHE, offline_client())))
    graph = build_instrument_graph(rows)
    doc = graph_document(graph, rows)

    # baseline_for answers for every verified duty
    assert doc["coverage"]["baseline_answered"] == doc["coverage"]["verified_duties"]
    assert doc["_verified_not_covered"] == []
    assert all(n.agency != "unknown" for n in graph.nodes)

    # SR 09-4 is recorded as superseded with evidence
    sr094 = next(n for n in graph.nodes if n.id == "sr-09-4")
    assert str(sr094.treatment_status) == "superseded"
    assert sr094.treatment_evidence and "SR 15-18" in sr094.treatment_evidence

    # baseline_for resolves a verified duty to its instrument stratum
    baseline = graph.baseline_for("b:AUD-02", date(2026, 6, 30))
    assert baseline is not None and str(baseline.stratum) == "regulation"
    # an unverified duty has no baseline node
    assert graph.baseline_for("s:GOV-15", date(2026, 6, 30)) is None
