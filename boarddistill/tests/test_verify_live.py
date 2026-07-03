"""B1-T2 — citation parsing, the eCFR resolver (offline via fake XML), and a full
72-row verification pass replayed from the committed cache."""

from __future__ import annotations

from pathlib import Path

import httpx
import pytest

from adapters.citations import (
    CfrCite,
    SrCite,
    UnresolvedCite,
    UscCite,
    first_cfr,
    first_resolvable,
    parse_citation,
)
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


def test_resolvable_non_cfr_citation_types() -> None:
    usc = first_resolvable("12 U.S.C. 5365(h)(1)")
    assert usc == UscCite(12, "5365", "(h)(1)", "12 U.S.C. 5365(h)(1)")
    assert first_resolvable("SR 15-18 fn. 5") == SrCite("15", "18", "SR 15-18")
    appx = first_resolvable("12 CFR Part 30, App. D, II.A")
    assert appx is not None and appx.label == "12 CFR Part 30, App. D, II.A"


def test_terse_appendix_resolves_to_part_30() -> None:
    # "App. D, sec. II.A" (no Part) resolves to 12 CFR Part 30 App. D in this corpus
    cite = first_resolvable("App. D, sec. II.A")
    assert cite is not None and cite.label == "12 CFR Part 30, App. D, II.A"


def test_unresolvable_citations_get_reasons() -> None:
    for text, needle in [
        ("Appendix C — Audit committee", "Director's Book"),  # not a CFR appendix
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


def test_ecfr_resolver_defers_non_cfr(tmp_path: Path) -> None:
    # EcfrResolver only handles CFR; U.S.C. is deferred to the composite (UscResolver).
    resolver = EcfrResolver(Fetcher(tmp_path, offline_client()))
    verdict = resolver.verify("12 U.S.C. 5365(i)", expected_actor="Full board")
    assert verdict.status == "unverified"
    assert verdict.span is None


def test_usc_and_sr_resolvers_pin_quotes(tmp_path: Path) -> None:
    from adapters.resolvers import SrResolver, UscResolver

    usc_html = (
        "<html><body><h1>1831m. Early identification</h1>"
        "<p>Each insured depository institution and its board of directors shall...</p>"
        "</body></html>"
    )

    def usc_handler(request: httpx.Request) -> httpx.Response:
        # first_cached miss -> HEAD to resolve the redirect, then GET the html granule
        return httpx.Response(200, text="" if request.method == "HEAD" else usc_html)

    usc = UscResolver(Fetcher(tmp_path, httpx.Client(transport=httpx.MockTransport(usc_handler))))
    v1 = usc.verify(UscCite(12, "1831m", "", "12 U.S.C. 1831m"), "Full board")
    assert v1.status == "verified"
    assert v1.span is not None and "1831m" in v1.span.quote  # type: ignore[operator]

    sr_html = (
        "<html><body><h1>SR 12-17: Consolidated Supervision Framework</h1>"
        "<p>SR 12-17 Attachment: The board of directors should ensure the risk-management "
        "function is independent and has appropriate stature within the organization, with "
        "clear authority and access to the board, consistent with the consolidated "
        "supervision framework for large financial institutions.</p></body></html>"
    )

    def sr_handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text=sr_html)

    sr = SrResolver(Fetcher(tmp_path, httpx.Client(transport=httpx.MockTransport(sr_handler))))
    v2 = sr.verify(SrCite("12", "17", "SR 12-17"), "Full board")
    assert v2.status == "verified"
    assert v2.span is not None


def test_appendix_roman_windowing_not_confused_by_substring() -> None:
    from adapters.ecfr_resolver import _appendix_subsection_window

    text = (
        "I. Introduction A. scope. "
        "II. Standards for Risk Governance Framework A. framework text here. "
        "III. Standards for Board of Directors A. board duty. F. Self-Assessments annual review."
    )
    # 'II.' must not match inside 'III.': II.A descends to the A subsection under II
    # (the Risk-Governance framework text), not the A under III (Board of Directors).
    assert _appendix_subsection_window(text, "II.A").startswith("A. framework text here")
    assert _appendix_subsection_window(text, "III.F").startswith("F. Self-Assessments")


def test_cfr_paragraph_windowing() -> None:
    from adapters.ecfr_resolver import _cfr_paragraph_window

    text = "§ 363.2 Annual reporting. (a) Audited statements. words (b) Management report. more"
    assert _cfr_paragraph_window(text, "(b)").startswith("(b) Management report")
    # no paragraph label -> unchanged
    assert _cfr_paragraph_window(text, "") == text


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

    from adapters.resolvers import build_resolver

    resolver = build_resolver(Fetcher(_CACHE, offline_client()))
    first = verify_targets(targets, resolver)
    assert len(first) == 72
    # 21 (CFR/USC/SR) + 8 appendices + 17 SR-attachment anchor matches, all from cache
    assert sum(1 for r in first if r.record.status == "verified") == 46
    # borderline anchor matches are recorded as candidates, never auto-verified (§3)
    assert any("candidate recorded" in (r.record.note or "") for r in first)
    # every row has a status; verified rows carry a pinned span
    for r in first:
        assert r.record.status in {"verified", "contradicted", "unverified"}
        if r.record.status == "verified":
            assert r.verdict.span is not None

    second = verify_targets(targets, resolver)
    assert [r.record.status for r in second] == [r.record.status for r in first]
