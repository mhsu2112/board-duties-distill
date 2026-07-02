"""Composite SourceResolver: dispatch a citation to the eCFR / govinfo / SR-letter resolver.

- CFR sections & appendices  -> eCFR versioner XML (``EcfrResolver``)
- U.S.C. sections            -> govinfo HTML granule via the link service (``UscResolver``)
- SR supervisory letters     -> federalreserve.gov HTML (``SrResolver``)

Each keeps the deterministic, cache-replayable contract; unreachable ⇒ ``unverified``.
"""

from __future__ import annotations

from dataclasses import dataclass

from distillcore.models.base import SourceSpan
from distillcore.pipeline.verify import CitationVerdict

from .citations import (
    CfrAppendixCite,
    CfrCite,
    SrCite,
    UscCite,
    first_resolvable,
    parse_citation,
)
from .ecfr_resolver import EcfrResolver, _support
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


@dataclass
class CompositeResolver:
    """Dispatches a citation to the resolver for its source type."""

    ecfr: EcfrResolver
    usc: UscResolver
    sr: SrResolver

    def verify(self, citation: str, *, expected_actor: str) -> CitationVerdict:
        cite = first_resolvable(citation)
        if isinstance(cite, CfrCite | CfrAppendixCite):
            return self.ecfr.verify(citation, expected_actor=expected_actor)
        if isinstance(cite, UscCite):
            return self.usc.verify(cite, expected_actor)
        if isinstance(cite, SrCite):
            return self.sr.verify(cite, expected_actor)
        reason = getattr(parse_citation(citation)[0], "reason", "unresolved citation")
        return CitationVerdict("unverified", reason, False, "n/a", None)


def build_resolver(fetcher: Fetcher) -> CompositeResolver:
    return CompositeResolver(EcfrResolver(fetcher), UscResolver(fetcher), SrResolver(fetcher))
