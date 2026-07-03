"""Composite SourceResolver: dispatch a citation to the eCFR / govinfo / SR-letter resolver.

- CFR sections & appendices  -> eCFR versioner XML (``EcfrResolver``)
- U.S.C. sections            -> govinfo HTML granule via the link service (``UscResolver``)
- SR supervisory letters     -> federalreserve.gov HTML (``SrResolver``)

Each keeps the deterministic, cache-replayable contract; unreachable ⇒ ``unverified``.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from distillcore.models.base import SourceSpan
from distillcore.pipeline.verify import CitationVerdict

from .anchor import CANDIDATE_FLOOR, HIGH_CONFIDENCE, anchor_match
from .citations import (
    CfrAppendixCite,
    CfrCite,
    SrCite,
    UscCite,
    first_resolvable,
    parse_citation,
)
from .ecfr_resolver import EcfrResolver, _support
from .pdfextract import pdf_to_text
from .retrieval import Fetcher, NotAllowedError
from .textextract import html_to_text

_QUOTE_CAP = 600


def _text_span(source_id: str, key: str, citation: str, full_text: str, quote: str) -> SourceSpan:
    start = full_text.find(quote[:80])
    capped = quote[:_QUOTE_CAP]
    return SourceSpan(
        id=f"span-{source_id}-{key}",
        source_id=source_id,
        citation=citation,
        start=start if start >= 0 else None,
        end=(start + len(capped)) if start >= 0 else None,
        quote=capped,
    )


@dataclass
class UscResolver:
    """Resolve a U.S.C. section to its govinfo HTML granule text."""

    fetcher: Fetcher
    edition_year: str = "2024"

    def verify(self, cite: UscCite, expected_actor: str) -> CitationVerdict:
        source_id = f"usc-t{cite.title}-s{cite.section}"
        cached = self.fetcher.first_cached(source_id)
        if cached is not None:
            doc_text = cached.text
        else:
            link = f"https://www.govinfo.gov/link/uscode/{cite.title}/{cite.section}"
            try:
                final = self.fetcher.final_url(link)
                htm = final.replace("/pdf/", "/html/").replace(".pdf", ".htm")
                doc = self.fetcher.fetch(htm, source_id, title=cite.label, notes=cite.raw)
                doc_text = doc.text
            except NotAllowedError:
                raise
            except Exception as exc:  # noqa: BLE001 — unreachable ⇒ unverified
                return CitationVerdict(
                    "unverified", f"fetch failed: {type(exc).__name__}", False, "n/a", None
                )

        text = html_to_text(doc_text)
        idx = text.lower().find(cite.section.lower())
        if idx < 0:
            return CitationVerdict(
                "contradicted",
                f"section {cite.section} not present in granule (F1)",
                False,
                "none",
                None,
            )
        quote = text[idx : idx + _QUOTE_CAP]
        span = _text_span(source_id, cite.section, cite.label, text, quote)
        note = f"{cite.label} present in U.S. Code ({self.edition_year} ed.); text pinned"
        return CitationVerdict("verified", note, True, _support(quote, expected_actor), span)


@dataclass
class SrResolver:
    """Resolve an SR supervisory letter to its federalreserve.gov page text."""

    fetcher: Fetcher

    def verify(self, cite: SrCite, expected_actor: str) -> CitationVerdict:
        source_id = f"sr-{cite.year}-{cite.number}"
        url = (
            f"https://www.federalreserve.gov/supervisionreg/srletters/"
            f"sr{cite.year}{int(cite.number):02d}.htm"
        )
        try:
            doc = self.fetcher.fetch(url, source_id, title=cite.label, notes=cite.raw)
        except NotAllowedError:
            raise
        except Exception as exc:  # noqa: BLE001 — unreachable ⇒ unverified
            return CitationVerdict(
                "unverified", f"fetch failed: {type(exc).__name__}", False, "n/a", None
            )

        text = html_to_text(doc.text)
        marker = f"{cite.year}-{cite.number}"
        idx = text.find(marker)
        if idx < 0 or len(text) < 200:
            return CitationVerdict(
                "unverified",
                f"SR page did not confirm letter {cite.label} (F1)",
                False,
                "none",
                None,
            )
        superseded = any(w in text[:400].lower() for w in ("superseded", "rescinded"))
        # Window on the substantive body (after "SUBJECT:"), skipping the masthead.
        subj = text.find("SUBJECT")
        start = subj if subj >= 0 else idx
        quote = text[start : start + _QUOTE_CAP]
        span = _text_span(source_id, marker, cite.label, text, quote)
        note = f"{cite.label} retrieved from federalreserve.gov; cover-letter text pinned"
        if superseded:
            note += " — NOTE: page indicates superseded/rescinded (F3 — human review)"
        return CitationVerdict(
            "verified", note, not superseded, _support(quote, expected_actor), span
        )


def _attachment_pdf_path(html: str, year: str, num: str) -> str | None:
    pattern = re.compile(rf'href="([^"]*SR{year}{int(num):02d}a\d+\.pdf)"', re.IGNORECASE)
    candidates = [m for m in pattern.findall(html) if "comment" not in m.lower()]
    return sorted(candidates)[0] if candidates else None


@dataclass
class SrAttachmentResolver:
    """Resolve a citation that points *inside* an SR-letter attachment PDF by anchor-matching
    the duty's paraphrased text against the attachment (records anchor_matched=true)."""

    fetcher: Fetcher

    def verify(
        self, *, source: str, citation: str, anchor: str, expected_actor: str
    ) -> CitationVerdict:
        cite = first_resolvable(source)
        if not isinstance(cite, SrCite):
            return CitationVerdict("unverified", "source is not an SR letter", False, "n/a", None)
        year, num = cite.year, cite.number
        htm_url = (
            f"https://www.federalreserve.gov/supervisionreg/srletters/sr{year}{int(num):02d}.htm"
        )
        try:
            htm = self.fetcher.fetch(htm_url, f"sr-{year}-{num}", title=cite.label)
        except NotAllowedError:
            raise
        except Exception as exc:  # noqa: BLE001
            return CitationVerdict(
                "unverified", f"fetch failed: {type(exc).__name__}", False, "n/a", None
            )

        pdf_path = _attachment_pdf_path(htm.text, year, num)
        if pdf_path is None:
            return CitationVerdict(
                "unverified",
                f"no attachment PDF found on the {cite.label} page",
                False,
                "none",
                None,
            )
        pdf_url = "https://www.federalreserve.gov" + pdf_path
        try:
            doc = self.fetcher.fetch_extracted(
                pdf_url, f"sr-{year}-{num}-att", pdf_to_text, title=f"{cite.label} attachment"
            )
        except NotAllowedError:
            raise
        except Exception as exc:  # noqa: BLE001
            return CitationVerdict(
                "unverified", f"PDF fetch failed: {type(exc).__name__}", False, "n/a", None
            )

        score, window = anchor_match(anchor, doc.text)
        source_id = f"sr-{year}-{num}-att"
        if score >= HIGH_CONFIDENCE:
            span = _text_span(source_id, "anchor", f"{cite.label} attachment", doc.text, window)
            note = f"{cite.label} attachment: duty text anchor-matched (score {score:.2f})"
            return CitationVerdict(
                "verified", note, True, _support(window, expected_actor), span, True
            )
        if score >= CANDIDATE_FLOOR:
            note = (
                f"anchor match borderline in {cite.label} attachment (best {score:.2f}); "
                f"candidate recorded — checkpoint §3: {window[:100]!r}"
            )
            return CitationVerdict("unverified", note, False, "n/a", None)
        return CitationVerdict(
            "unverified",
            f"duty text not located in the {cite.label} attachment (best {score:.2f})",
            False,
            "none",
            None,
        )


@dataclass
class CompositeResolver:
    """Dispatches a citation to the resolver for its source type."""

    ecfr: EcfrResolver
    usc: UscResolver
    sr: SrResolver
    sr_attachment: SrAttachmentResolver

    def verify(
        self, citation: str, *, expected_actor: str, source: str = "", anchor: str = ""
    ) -> CitationVerdict:
        cite = first_resolvable(citation)
        if isinstance(cite, CfrCite | CfrAppendixCite):
            return self.ecfr.verify(citation, expected_actor=expected_actor)
        if isinstance(cite, UscCite):
            return self.usc.verify(cite, expected_actor)
        if isinstance(cite, SrCite):
            return self.sr.verify(cite, expected_actor)
        # unresolved citation — try guidance-document anchor match via the source instrument
        if source and isinstance(first_resolvable(source), SrCite) and anchor:
            return self.sr_attachment.verify(
                source=source, citation=citation, anchor=anchor, expected_actor=expected_actor
            )
        reason = getattr(parse_citation(citation)[0], "reason", "unresolved citation")
        return CitationVerdict("unverified", reason, False, "n/a", None)


def build_resolver(fetcher: Fetcher) -> CompositeResolver:
    return CompositeResolver(
        EcfrResolver(fetcher),
        UscResolver(fetcher),
        SrResolver(fetcher),
        SrAttachmentResolver(fetcher),
    )
