"""B5-T0 — carry-forward tests (all offline, cache-replayed).

Covers: (a) the ten re-pinned rows re-distill anchor-clean from the committed LLM cache;
(c) the residual retries — s:GOV-15 resolves via the SR-letter-body fallback, the other two
re-document without being forced. The T0(b) D7 disposition fix is tested in
``test_b4_reclassify.py``.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from adapters.redistill import TEN_ROWS, redistill_all
from adapters.resolvers import build_resolver
from adapters.retrieval import Fetcher, offline_client
from adapters.retry_residuals import RETRY_IDS, run_retries
from distillcore.llm import LlmHarness

_ROOT = Path(__file__).resolve().parents[1]
_IMPORT = _ROOT / "outputs" / "import" / "imported_duties.json"
_RETAGS = _ROOT / "outputs" / "b2" / "retags.json"
_CACHE = _ROOT / "data" / "llm_cache"
_SOURCES = _ROOT / "data" / "sources"

_ARTIFACTS = _IMPORT.exists() and _RETAGS.exists()


def _drafts() -> dict[str, dict[str, object]]:
    return {d["duty_id"]: d for d in json.loads(_IMPORT.read_text())["duties"]}


@pytest.mark.skipif(not _ARTIFACTS, reason="B-series artifacts absent")
def test_redistill_ten_rows_anchor_clean_from_cache() -> None:
    """Offline replay: the ten re-pinned rows distill anchor-clean, objects resolved."""
    retags = {r["duty_id"]: r for r in json.loads(_RETAGS.read_text())["retags"]}
    harness = LlmHarness(cache_root=_CACHE, live=False)  # replay only; a miss would raise
    rows = redistill_all(harness, _drafts(), retags)

    assert [r.duty_id for r in rows] == sorted(TEN_ROWS)
    assert all(r.anchor_ok for r in rows)
    # each corrected pin now supports a real object (no longer source_mismatch)
    assert all(r.distilled.object.strip() for r in rows)
    assert all("object" not in r.distilled.unresolved_fields for r in rows)


@pytest.mark.skipif(not _ARTIFACTS, reason="B-series artifacts absent")
def test_residual_retries_resolve_one_redocument_two() -> None:
    doc = run_retries(json.loads(_IMPORT.read_text()), _SOURCES)
    assert set(RETRY_IDS) == {o["duty_id"] for o in doc["outcomes"]}
    assert doc["resolved_rows"] == ["s:GOV-15"]
    assert sorted(doc["re_documented_rows"]) == ["s:BCG-14", "s:CAP-10"]

    by_id = {o["duty_id"]: o for o in doc["outcomes"]}
    assert by_id["s:GOV-15"]["status"] == "verified"
    assert by_id["s:GOV-15"]["anchor_matched"] is True
    assert doc["resolved_spans"] and doc["resolved_spans"][0]["source_id"] == "sr-12-17"
    # the two re-documented rows are never forced to verified
    assert by_id["s:BCG-14"]["status"] == "unverified"
    assert by_id["s:CAP-10"]["status"] == "unverified"
    assert by_id["s:CAP-10"]["proposed_record_type"] == "no_board_duty_note"


@pytest.mark.skipif(not _ARTIFACTS, reason="B-series artifacts absent")
def test_sr_letter_body_fallback_verifies_gov15() -> None:
    """The SR-attachment resolver's new body fallback resolves a duty whose substance is inline
    in the letter (no separate attachment PDF)."""
    rows = {d["duty_id"]: d for d in json.loads(_IMPORT.read_text())["duties"]}
    row = rows["s:GOV-15"]
    resolver = build_resolver(Fetcher(_SOURCES, offline_client()))
    verdict = resolver.verify(
        row["source_citations"][0],
        expected_actor=row["board_level"],
        source=row["source"],
        anchor=row["object"],
    )
    assert verdict.status == "verified"
    assert verdict.anchor_matched is True
    assert verdict.span is not None and "letter body" in verdict.span.citation
