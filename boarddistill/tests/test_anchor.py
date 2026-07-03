"""B2-T3 — fuzzy anchor matching + SR attachment-PDF link discovery."""

from __future__ import annotations

from adapters.anchor import CANDIDATE_FLOOR, HIGH_CONFIDENCE, anchor_match, content_words
from adapters.resolvers import _attachment_pdf_path

_DOC = (
    "Composition and Governance Structure. An effective board considers whether its "
    "composition, governance structure, and practices support the board's ability to "
    "oversee the firm. Information Flows. The board directs senior management to provide "
    "timely, accurate, well-organized information sufficient to make sound decisions."
)


def test_content_words_drops_stopwords_and_short() -> None:
    words = content_words("The board shall oversee the risk-management framework")
    assert "oversee" in words
    assert "framework" in words
    assert "the" not in words and "board" not in words  # stopwords


def test_anchor_match_high_for_close_paraphrase() -> None:
    anchor = "Board directs senior management to provide timely, accurate, organized information"
    score, window = anchor_match(anchor, _DOC)
    assert score >= HIGH_CONFIDENCE
    assert "timely" in window


def test_anchor_match_low_for_unrelated_text() -> None:
    score, _ = anchor_match("capital stress testing scenario design methodology", _DOC)
    assert score < CANDIDATE_FLOOR


def test_manual_resolver_source_matching() -> None:
    from adapters.resolvers import ManualResolver

    mr = ManualResolver(fetcher=None)  # type: ignore[arg-type]
    assert mr.matches("Comptroller's Handbook, Corporate and Risk Governance")
    assert mr.matches("FDIC RMS Manual, Management section")
    assert not mr.matches("SR 21-3 / CA 21-1")
    assert not mr.matches("12 CFR 363.5")


def test_attachment_pdf_path_prefers_a1_skips_comment() -> None:
    html = (
        '<a href="/supervisionreg/srletters/SR2103.pdf">letter</a>'
        '<a href="/supervisionreg/srletters/SR2103a1.pdf">attachment</a>'
        '<a href="/supervisionreg/srletters/SR2103aCommentSummaryPublication.pdf">comments</a>'
    )
    assert _attachment_pdf_path(html, "21", "3") == "/supervisionreg/srletters/SR2103a1.pdf"
    assert _attachment_pdf_path("<a href='nothing.htm'>x</a>", "21", "3") is None
