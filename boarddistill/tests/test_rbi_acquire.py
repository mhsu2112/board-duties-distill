"""B6-T1 — RBI appendix parser + acquisition artifacts."""

from __future__ import annotations

import json
from pathlib import Path

from adapters.rbi_acquire import MD_SAMPLE, circular_clean_text, parse_appendix

_ROOT = Path(__file__).resolve().parents[1]
_ANSWER_KEY = _ROOT / "data" / "benchmark" / "answer_key" / "grouping.json"
_CORPUS = _ROOT / "data" / "benchmark" / "corpus"

_APPENDIX_HTML = """
<table>
<tr><td>Sl</td><td>Circular No.</td><td>Date</td><td>Subject</td></tr>
<tr><td>1</td>
    <td><a href="NotificationUser.aspx?Id=819">DBOD.AML.BC.18/14.01.001/2005-06</a></td>
    <td>11.08.2005</td><td>Interest Rate on Savings Deposits</td></tr>
<tr><td>2</td>
    <td><a href="NotificationUser.aspx?Id=12555">DBR.Dir.No.84/13.03.00/2015-16</a></td>
    <td>03.03.2016</td><td>Ceiling rate on deposits</td></tr>
<tr><td>a para citing <a href="NotificationUser.aspx?Id=819">the same one</a></td></tr>
</table>
"""


def test_parse_appendix_extracts_linked_circulars_deduped() -> None:
    entries = parse_appendix(_APPENDIX_HTML)
    ids = {e.circular_id for e in entries}
    assert ids == {"819", "12555"}  # deduped (819 appears twice)
    by_id = {e.circular_id: e for e in entries}
    assert by_id["12555"].circular_ref.startswith("DBR.Dir.No.84")
    assert "Ceiling rate" in by_id["12555"].subject


def test_circular_clean_text_strips_archive_nav() -> None:
    raw = "Real circular body here. 2025 All Months January February March"
    assert circular_clean_text(raw) == "Real circular body here."


def test_acquired_corpus_and_sealed_answer_key_consistent() -> None:
    if not _ANSWER_KEY.exists():
        return  # acquisition not run in this checkout
    doc = json.loads(_ANSWER_KEY.read_text())
    grouping = doc["grouping"]
    md_ids = {m.md_id for m in MD_SAMPLE}
    assert set(grouping.values()) <= md_ids
    # every grouped circular has a corpus text (symmetric: corpus ⊇ answer-key circulars)
    for cid in grouping:
        assert (_CORPUS / f"circ-{cid}.txt").exists()
    # per-MD retrieval had zero misses (100% acquisition)
    assert all(m["missed"] == 0 for m in doc["per_md"])
    assert len(grouping) == sum(m["retrieved"] for m in doc["per_md"])
