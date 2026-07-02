"""B1-T2 — citation parsing, the eCFR resolver (offline via fake XML), and a full
72-row verification pass replayed from the committed cache."""

from __future__ import annotations

from pathlib import Path

import httpx
import pytest

from adapters.citations import CfrCite, UnresolvedCite, first_cfr, parse_citation
from adapters.ecfr_resolver import EcfrResolver, _find_section, _support
from adapters.retrieval import Fetcher, offline_client
from distillcore.pipeline.verify import verify_targets

_XLSX = (
    Path(__file__).resolve().parents[2]
    / "Synthesis"
    / "gsib-board_duties-combined_inventory.xlsx"
)
_CACHE = Path(__file__).resolve().parents[1] / "data" / "sources"

_FAKE_XML = """<?xml version="1.0"?>
<DIV5 N="363" TYPE="PART">
  <DIV8 N="363.5" TYPE="SECTION">
    <HEAD>§ 363.5 Audit committees.</HEAD>
    <P>(a) Composition and duties. Each insured depository institution shall establish an
       audit committee of its board of directors.</P>
  </DIV8>
  <DIV8 N="363.9" TYPE="SECTION">
    <HEAD>§ 363.9 [Reserved]</HEAD>
  </DIV8>
</DIV5>
"""


def _xml_client() -> httpx.Client:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text=_FAKE_XML)

    return httpx.Client(transport=httpx.MockTransport(handler))


# ---- citation parsing --------------------------------------------------------------


def test_parse_cfr_sections() -> None:
    c = first_cfr("12 CFR 252.33(a)(3)(iv)")
    assert isinstance(c, CfrCite)
    assert (c.title, c.part, c.section, c.paragraphs) == (12, "252", "252.33", "(a)(3)(iv)")
    assert first_cfr("17 CFR 240.13a-14").section == "240.13a-14"  # type: ignore[union-attr]
    # a citation carrying both a statute and a CFR section resolves to the CFR one
    assert first_cfr("12 U.S.C. 1831m; 12 CFR 363.5").section == "363.5"  # type: ignore[union-attr]


def test_unresolvable_citations_get_reasons() -> None:
    for text, needle in [
        ("12 U.S.C. 5365(i)", "statute"),
        ("App. D, sec. II.A", "appendix"),
        ("Attachment, Attribute 1, p. 3", "guidance-document"),
        ("Management (local ll. ~11944-12024)", "local line-number"),
    ]:
        got = parse_citation(text)[0]
        assert isinstance(got, UnresolvedCite)
        assert needle in got.reason


# ---- resolver logic (offline, fake XML) --------------------------------------------


def test_resolver_verifies_cfr_section_and_pins_quote(tmp_path: Path) -> None:
    resolver = EcfrResolver(Fetcher(tmp_path, _xml_client()))
    verdict = resolver.verify("12 CFR 363.5", expected_actor="Audit committee")
    assert verdict.status == "verified"
    assert verdict.as_of_valid is True
    assert verdict.support_signal == "strong"
    assert verdict.span is not None
    assert "Audit committees" in verdict.span.quote  # type: ignore[operator]
    assert verdict.span.start is not None and verdict.span.start >= 0


def test_resolver_flags_reserved_as_contradicted(tmp_path: Path) -> None:
    resolver = EcfrResolver(Fetcher(tmp_path, _xml_client()))
    verdict = resolver.verify("12 CFR 363.9", expected_actor="Full board")
    assert verdict.status == "contradicted"
    assert "Reserved" in verdict.note


def test_resolver_missing_section_is_contradicted(tmp_path: Path) -> None:
    resolver = EcfrResolver(Fetcher(tmp_path, _xml_client()))
    verdict = resolver.verify("12 CFR 363.99", expected_actor="Full board")
    assert verdict.status == "contradicted"
    assert "not found" in verdict.note


def test_resolver_non_cfr_is_unverified(tmp_path: Path) -> None:
    resolver = EcfrResolver(Fetcher(tmp_path, offline_client()))
    verdict = resolver.verify("12 U.S.C. 5365(i)", expected_actor="Full board")
    assert verdict.status == "unverified"
    assert verdict.span is None
    assert "statute" in verdict.note


def test_find_section_and_support() -> None:
    found = _find_section(_FAKE_XML, "363.5")
    assert found is not None
    head, text = found
    assert head.startswith("§ 363.5")
    assert _support(text, "Audit committee") == "strong"
    assert _support("nothing relevant here", "Full board") == "none"


# ---- full pass replayed from the committed cache -----------------------------------


@pytest.mark.skipif(not _XLSX.exists() or not _CACHE.exists(), reason="xlsx or cache absent")
def test_full_72_row_pass_from_cache_is_deterministic() -> None:
    from adapters.b1_targets import select_targets
    from adapters.inventory_xlsx import import_inventory

    duties = [d.model_dump(mode="json") for d in import_inventory(_XLSX).duties]
    targets = select_targets(duties)
    assert len(targets) == 72

    resolver = EcfrResolver(Fetcher(_CACHE, offline_client()))
    first = verify_targets(targets, resolver)
    assert len(first) == 72
    assert sum(1 for r in first if r.record.status == "verified") == 16
    # every row has a status; verified rows carry a pinned span
    for r in first:
        assert r.record.status in {"verified", "contradicted", "unverified"}
        if r.record.status == "verified":
            assert r.verdict.span is not None

    second = verify_targets(targets, resolver)
    assert [r.record.status for r in second] == [r.record.status for r in first]
