"""Concrete eCFR-backed SourceResolver for B1 verification.

Resolves CFR section cites to verbatim provision text via the eCFR versioner XML API
(allowlisted ecfr.gov), pins the text as a ``SourceSpan`` with char offsets, and checks
currency (present + not ``[Reserved]``) at the snapshot date. Non-CFR cites resolve to
``unverified`` with a reason. The `support_signal` (does the provision text mention the
stated board actor) is surfaced for human F2 confirmation — never a machine legal claim.
"""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass

from distillcore.models.base import SourceSpan
from distillcore.pipeline.verify import CitationVerdict

from .citations import CfrAppendixCite, CfrCite, first_resolvable, parse_citation
from .retrieval import Fetcher, NotAllowedError

_QUOTE_CAP = 600
_WS = re.compile(r"\s+")


def _normalize(text: str) -> str:
    return _WS.sub(" ", text).strip()


def _section_text(div: ET.Element) -> str:
    return _normalize(" ".join(t for t in div.itertext()))


def _find_section(xml_text: str, section: str) -> tuple[str, str] | None:
    """Return (head, normalized_section_text) for the DIV whose N == section, else None."""
    root = ET.fromstring(xml_text)
    for div in root.iter():
        if div.tag.startswith("DIV") and div.get("N") == section:
            head_el = div.find("HEAD")
            head = _normalize(head_el.text or "") if head_el is not None else ""
            return head, _section_text(div)
    return None


def _find_appendix(xml_text: str, appendix: str) -> tuple[str, str] | None:
    """Return (head, normalized_text) for the appendix DIV (N like 'Appendix D to Part ...')."""
    root = ET.fromstring(xml_text)
    want = f"appendix {appendix.lower()}"
    for div in root.iter():
        if div.tag.startswith("DIV") and (div.get("N") or "").lower().startswith(want):
            head_el = div.find("HEAD")
            head = _normalize(head_el.text or "") if head_el is not None else ""
            return head, _section_text(div)
    return None


def _cfr_paragraph_window(text: str, paragraphs: str) -> str:
    """Window ``text`` onto the first cited paragraph label (e.g. '(b)'), if present."""
    match = re.match(r"\([^)]*\)", paragraphs)
    if not match:
        return text
    pos = text.find(match.group(0), 25)  # skip the section head's own text
    return text[pos:] if pos > 0 else text


def _appendix_subsection_window(text: str, subsection: str) -> str:
    """Window onto a cited appendix subsection like 'II.A' (roman then letter).

    Uses a lookbehind so 'II.' does not match inside 'III.', and takes the last
    occurrence (the body, not the table of contents)."""
    parts = subsection.split(".")
    roman = parts[0]
    letter = parts[1] if len(parts) > 1 else None
    matches = list(re.finditer(rf"(?<![A-Za-z]){re.escape(roman)}\.\s", text))
    if not matches:
        return text
    window = text[matches[-1].start() :]  # last occurrence = body, not the ToC
    if letter:
        idx = window.find(f"{letter}. ")
        if 0 < idx < 4000:
            window = window[idx:]
    return window


def _support(text: str, expected_actor: str) -> str:
    body = text.lower()
    actor = expected_actor.lower()
    if "audit committee" in actor and "audit committee" in body:
        return "strong"
    if "risk committee" in actor and "risk committee" in body:
        return "strong"
    if "board" in actor and ("board of directors" in body or "board" in body):
        return "strong"
    if any(term in body for term in ("board of directors", "director", "committee")):
        return "weak"
    return "none"


@dataclass
class EcfrResolver:
    """Injectable resolver. ``fetcher`` owns the network + cache; ``as_of`` is the eCFR
    version date to read (the B1 snapshot)."""

    fetcher: Fetcher
    as_of: str = "2026-06-30"

    def verify(
        self, citation: str, *, expected_actor: str, source: str = "", anchor: str = ""
    ) -> CitationVerdict:
        cite = first_resolvable(citation)
        if isinstance(cite, CfrCite):
            return self._verify_cfr(cite, expected_actor)
        if isinstance(cite, CfrAppendixCite):
            return self._verify_appendix(cite, expected_actor)
        reason = getattr(parse_citation(citation)[0], "reason", "non-CFR citation")
        return CitationVerdict("unverified", reason, False, "n/a", None)

    def _fetch_part(self, title: int, part: str, label: str) -> tuple[str, str] | str:
        """Fetch a part's eCFR XML; return (source_id, text) or an error note."""
        source_id = f"ecfr-t{title}-p{part}"
        url = (
            f"https://www.ecfr.gov/api/versioner/v1/full/{self.as_of}/title-{title}.xml?part={part}"
        )
        try:
            doc = self.fetcher.fetch(
                url, source_id, title=f"eCFR {title} CFR part {part}", notes=label
            )
        except NotAllowedError:
            raise
        except Exception as exc:  # noqa: BLE001 — unreachable ⇒ unverified, never a guess
            return f"fetch failed: {type(exc).__name__}"
        return source_id, doc.text

    def _span(
        self, source_id: str, key: str, citation: str, doc_text: str, text: str
    ) -> SourceSpan:
        full_norm = _normalize(" ".join(ET.fromstring(doc_text).itertext()))
        quote = text[:_QUOTE_CAP]
        start = full_norm.find(text[:80])
        return SourceSpan(
            id=f"span-{source_id}-{key}",
            source_id=source_id,
            citation=citation,
            start=start if start >= 0 else None,
            end=(start + len(quote)) if start >= 0 else None,
            quote=quote,
        )

    def _verify_cfr(self, cfr: CfrCite, expected_actor: str) -> CitationVerdict:
        fetched = self._fetch_part(cfr.title, cfr.part, cfr.label)
        if isinstance(fetched, str):
            return CitationVerdict("unverified", fetched, False, "n/a", None)
        source_id, doc_text = fetched
        found = _find_section(doc_text, cfr.section)
        if found is None:
            return CitationVerdict(
                "contradicted",
                f"section {cfr.section} not found in {cfr.title} CFR part {cfr.part} (F1)",
                False,
                "none",
                None,
            )
        head, text = found
        if "[reserved]" in head.lower() or "[reserved]" in text.lower():
            return CitationVerdict(
                "contradicted",
                f"{cfr.label} is [Reserved] (F3 stale-as-current)",
                False,
                "none",
                None,
            )
        window = _cfr_paragraph_window(text, cfr.paragraphs) if cfr.paragraphs else text
        span = self._span(source_id, cfr.section, cfr.label, doc_text, window)
        return CitationVerdict(
            "verified",
            f"{cfr.label} present and in force at {self.as_of}; verbatim text pinned",
            True,
            _support(window, expected_actor),
            span,
        )

    def _verify_appendix(self, cite: CfrAppendixCite, expected_actor: str) -> CitationVerdict:
        fetched = self._fetch_part(cite.title, cite.part, cite.label)
        if isinstance(fetched, str):
            return CitationVerdict("unverified", fetched, False, "n/a", None)
        source_id, doc_text = fetched
        found = _find_appendix(doc_text, cite.appendix)
        if found is None:
            return CitationVerdict(
                "contradicted",
                f"Appendix {cite.appendix} not found in {cite.title} CFR part {cite.part} (F1)",
                False,
                "none",
                None,
            )
        _head, text = found
        window = _appendix_subsection_window(text, cite.subsection) if cite.subsection else text
        key = f"app{cite.appendix}-{cite.subsection or 'full'}"
        span = self._span(source_id, key, cite.label, doc_text, window)
        return CitationVerdict(
            "verified",
            f"{cite.label} present and in force at {self.as_of}; verbatim text pinned",
            True,
            _support(window, expected_actor),
            span,
        )
