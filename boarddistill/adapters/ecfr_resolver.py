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

from .citations import first_cfr, parse_citation
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

    def verify(self, citation: str, *, expected_actor: str) -> CitationVerdict:
        cfr = first_cfr(citation)
        if cfr is None:
            unresolved = parse_citation(citation)[0]
            reason = getattr(unresolved, "reason", "unresolved citation")
            return CitationVerdict("unverified", reason, False, "n/a", None)

        source_id = f"ecfr-t{cfr.title}-p{cfr.part}"
        url = (
            f"https://www.ecfr.gov/api/versioner/v1/full/{self.as_of}"
            f"/title-{cfr.title}.xml?part={cfr.part}"
        )
        try:
            doc = self.fetcher.fetch(
                url, source_id, title=f"eCFR {cfr.title} CFR part {cfr.part}", notes=cfr.label
            )
        except NotAllowedError:
            raise
        except Exception as exc:  # noqa: BLE001 — unreachable source ⇒ unverified, never a guess
            return CitationVerdict(
                "unverified", f"fetch failed: {type(exc).__name__}", False, "n/a", None
            )

        found = _find_section(doc.text, cfr.section)
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

        full_norm = _normalize(" ".join(ET.fromstring(doc.text).itertext()))
        quote = text[:_QUOTE_CAP]
        start = full_norm.find(text[:80])
        span = SourceSpan(
            id=f"span-{source_id}-{cfr.section}",
            source_id=source_id,
            citation=cfr.label,
            start=start if start >= 0 else None,
            end=(start + len(quote)) if start >= 0 else None,
            quote=quote,
        )
        return CitationVerdict(
            "verified",
            f"{cfr.label} present and in force at {self.as_of}; verbatim text pinned",
            True,
            _support(text, expected_actor),
            span,
        )
