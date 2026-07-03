"""B5-T2 — per-wave verification + corpus graph (offline, cache-replayed)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from adapters.b5_graph import all_corpus_rows, corpus_graph_document
from adapters.b5_verify import verify_wave
from adapters.citations import first_cfr
from adapters.resolvers import build_resolver
from adapters.retrieval import Fetcher, offline_client

_ROOT = Path(__file__).resolve().parents[1]
_WAVES = _ROOT / "outputs" / "b5" / "waves.json"
_TARGETS = _ROOT / "outputs" / "b1" / "targets.json"
_IMPORT = _ROOT / "outputs" / "import" / "imported_duties.json"
_CACHE = _ROOT / "data" / "sources"

_ARTIFACTS = _WAVES.exists() and _TARGETS.exists() and _IMPORT.exists() and _CACHE.exists()


def _section(citation: str) -> str:
    cite = first_cfr(citation)
    assert cite is not None
    return cite.section


def test_cfr_section_range_resolves_to_first_section() -> None:
    # the B5-T2 false-contradiction fix: a numeric range keeps its first section...
    assert _section("12 CFR 252.62-252.63") == "252.62"
    assert _section("12 CFR 252.70-252.78") == "252.70"
    assert _section("12 CFR 225.71-.73") == "225.71"
    # ...while a within-section hyphen is preserved (240.13a-14 is a single section)
    assert _section("17 CFR 240.13a-14") == "240.13a-14"


@pytest.mark.skipif(not _ARTIFACTS, reason="B5 artifacts absent")
def test_no_contradictions_across_the_corpus() -> None:
    """After the range fix, no corpus row is contradicted (the three false ones resolved)."""
    waves = json.loads(_WAVES.read_text())
    drafts = {d["duty_id"]: d for d in json.loads(_IMPORT.read_text())["duties"]}
    resolver = build_resolver(Fetcher(_CACHE, offline_client()))
    contradicted = []
    for wave in waves["waves"]:
        for r in verify_wave(wave, drafts, resolver):
            if r.record.status == "contradicted":
                contradicted.append(r.duty_id)
    assert contradicted == []


@pytest.mark.skipif(not _ARTIFACTS, reason="B5 artifacts absent")
def test_corpus_graph_covers_every_verified_duty_no_unknown_agency() -> None:
    waves = json.loads(_WAVES.read_text())
    drafts = {d["duty_id"]: d for d in json.loads(_IMPORT.read_text())["duties"]}
    mvp_targets = json.loads(_TARGETS.read_text())["targets"]
    resolver = build_resolver(Fetcher(_CACHE, offline_client()))

    rows = all_corpus_rows(mvp_targets, waves, drafts, resolver)
    doc = corpus_graph_document(rows)
    assert doc["coverage"]["baseline_answered"] == doc["coverage"]["verified_duties"]
    assert doc["coverage"]["unknown_agency_instruments"] == 0
    assert doc["_verified_not_covered"] == []
    # a B5-domain instrument carries a real stratum (drives cross-stratum classification)
    graph = {n["citation"]: n for n in doc["graph"]["nodes"]}
    assert graph["12 CFR Part 360"]["stratum"] == "regulation"
    assert graph["12 U.S.C. 371c"]["stratum"] == "statute"
