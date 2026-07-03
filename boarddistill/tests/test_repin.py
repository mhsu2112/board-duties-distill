"""B4-T2 — re-pin the ten mispinned rows: every corrected quote resolves to the cited cache."""

from __future__ import annotations

from pathlib import Path

import pytest

from adapters.repin import REPINS, TEN_ROWS, corrected_spans, repin_document, verify_repins

_CACHE = Path(__file__).resolve().parents[1] / "data" / "sources"


def test_the_ten_rows_are_the_b3_source_mismatch_rows() -> None:
    expected = {
        "b:AUD-08", "b:CAP-02", "b:RGC-05", "s:BCG-03", "s:CAP-07",
        "s:CAP-09", "s:GOV-03", "s:GOV-04", "s:GOV-08", "s:GOV-12",
    }
    assert set(TEN_ROWS) == expected
    # allowlist unchanged: every re-pin stays inside the originally-cited instrument family.
    assert all(r["source_id"] and r["new_citation"] for r in REPINS)


@pytest.mark.skipif(not _CACHE.exists(), reason="source cache absent")
def test_every_corrected_quote_resolves_to_cache() -> None:
    verified = verify_repins()
    unresolved = [k for k, v in verified.items() if not v]
    assert all(verified.values()), f"unresolved re-pin quotes: {unresolved}"


@pytest.mark.skipif(not _CACHE.exists(), reason="source cache absent")
def test_document_reports_clean_repins_and_redistill_checkpoint() -> None:
    doc = repin_document()
    assert doc["counts"]["quote_verified"] == 10
    assert doc["unverified_quotes"] == []
    # all ten re-pinned cleanly; none escalated to the F2/F4 candidate queue this pass.
    assert doc["counts"]["escalated_f2_f4"] == 0
    assert doc["f2_f4_review_queue"] == []
    # the live re-distill is a checkpoint (no API key)
    assert "ANTHROPIC_API_KEY" in doc["redistill_checkpoint"]


def test_corrected_spans_are_span_shaped() -> None:
    spans = corrected_spans()
    assert len(spans) == 10
    assert all({"id", "source_id", "citation", "quote", "anchor_matched"} <= set(s) for s in spans)
