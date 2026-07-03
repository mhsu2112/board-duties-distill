"""B6-T2 — RBI adapter-lite: parse, pseudonymize, leakage scan, round-trip."""

from __future__ import annotations

import json
from pathlib import Path

from adapters.rbi_adapter import (
    build_pseudonym_map,
    has_leaked_identifier,
    normalize_corpus,
    parse_circular,
)

_ROOT = Path(__file__).resolve().parents[1]
_POOLED = _ROOT / "data" / "benchmark" / "pooled" / "instruments.json"
_MAP = _ROOT / "data" / "benchmark" / "pseudonym_map" / "map.json"

_CIRC_A = (
    "Notifications ( 73 kb ) Placement of Deposits with Other Banks RBI/2015-16/236 "
    "DCBR.BPD.(PCB).Cir.No. 8/16.20.000/2015-16 November 19, 2015 "
    "All Primary (Urban) Co-operative Banks Dear Sir Please refer to our circular "
    "BPD.PCB.Cir.46/16.20.00/2002-03 dated May 17, 2003."
)
_CIRC_B = (
    "Notifications ( 7 kb ) Ceiling on deposits BPD.PCB.Cir.46/16.20.00/2002-03 "
    "May 17, 2003 All Primary (Urban) Co-operative Banks Dear Sir text."
)


def test_parse_circular_fields() -> None:
    p = parse_circular(_CIRC_A)
    assert "Placement of Deposits" in p["subject"]
    assert p["date"] == "November 19, 2015"
    assert "Co-operative Banks" in p["addressee"]
    assert any("RBI/2015-16/236" in r for r in p["own_refs"])


def test_pseudonymize_removes_all_identifiers_and_preserves_cross_ref() -> None:
    corpus = {"A": _CIRC_A, "B": _CIRC_B}
    pmap = build_pseudonym_map(corpus)
    instruments = {s.doc_id: s for s in normalize_corpus(corpus, pmap)}

    # no real RBI identifier survives in any field
    for s in instruments.values():
        assert not has_leaked_identifier(s.body + " " + s.subject)
    # A references B's circular number → A.cross_refs contains B's doc_id (structure preserved)
    doc_a, doc_b = pmap["doc_id"]["A"], pmap["doc_id"]["B"]
    assert doc_b in instruments[doc_a].cross_refs
    assert doc_a not in instruments[doc_a].cross_refs  # no self-reference


def test_has_leaked_identifier_catches_raw_ref() -> None:
    assert has_leaked_identifier("see RBI/2015-16/236 for details")
    assert has_leaked_identifier("DBOD.Dir.BC.51/13.03.00/2002-03")
    assert not has_leaked_identifier("see DOC-89eefe for details")


def test_pooled_corpus_has_zero_leakage_and_sealed_map_round_trips() -> None:
    if not (_POOLED.exists() and _MAP.exists()):
        return
    pooled = json.loads(_POOLED.read_text())
    for s in pooled["instruments"]:
        assert not has_leaked_identifier(s["body"] + " " + s["subject"])
    mp = json.loads(_MAP.read_text())
    # round-trip: every pooled doc_id is a value in the sealed real→pseudonym map
    doc_ids = set(mp["doc_id"].values())
    assert {s["doc_id"] for s in pooled["instruments"]} == doc_ids
