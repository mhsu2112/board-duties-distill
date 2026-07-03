"""B6-T3 — engine leakage scan + proposal-set invariants."""

from __future__ import annotations

import json
from pathlib import Path

from adapters.b6_engine import leakage_hit

_ROOT = Path(__file__).resolve().parents[1]
_PROPOSALS = _ROOT / "outputs" / "b6" / "engine_proposals.json"
_BASELINE = _ROOT / "outputs" / "b6" / "baseline_proposals.json"
_POOLED = _ROOT / "data" / "benchmark" / "pooled" / "instruments.json"


def test_leakage_hit_catches_program_and_identifier_references() -> None:
    assert leakage_hit("as per the Master Direction on Priority Sector Lending")
    assert leakage_hit("withdrawn per the Regulations Review Authority")
    assert leakage_hit("see RBI/2015-16/236")
    assert not leakage_hit("banks shall maintain a minimum interest rate on term deposits")


def test_engine_proposals_are_clean_anchored_and_cover_the_corpus() -> None:
    if not (_PROPOSALS.exists() and _POOLED.exists()):
        return
    doc = json.loads(_PROPOSALS.read_text())
    pooled = json.loads(_POOLED.read_text())
    corpus = {s["doc_id"]: s["body"] for s in pooled["instruments"]}
    corpus_ws = {k: "".join(v.split()) for k, v in corpus.items()}

    # every EMITTED operation is anchored (verbatim in some circular body) and non-leaky
    for g in doc["groups"]:
        for op in g["operations"]:
            assert not leakage_hit(op["evidence_quote"] + " " + op["rationale"])
            q = "".join(op["evidence_quote"].split())
            assert any(q in body for body in corpus_ws.values())  # zero unanchored claims

    # the grouping is a partition covering every corpus doc exactly once
    assigned = [d for g in doc["groups"] for d in g["doc_ids"]]
    assert len(assigned) == len(set(assigned))
    assert set(assigned) == set(corpus)
    # DoD: zero UNQUARANTINED leakage (quarantined ones were dropped, not emitted)
    emitted_leaks = sum(
        1 for g in doc["groups"] for op in g["operations"] if leakage_hit(op["evidence_quote"])
    )
    assert emitted_leaks == 0


def test_baseline_covers_corpus_and_is_leakage_free() -> None:
    if not (_BASELINE.exists() and _POOLED.exists()):
        return
    doc = json.loads(_BASELINE.read_text())
    corpus = {s["doc_id"] for s in json.loads(_POOLED.read_text())["instruments"]}
    assigned = [d for g in doc["groups"] for d in g["doc_ids"]]
    assert set(assigned) == corpus  # partition covers every doc
    assert len(assigned) == len(set(assigned))
    assert all(not leakage_hit(g["theme"]) for g in doc["groups"])
