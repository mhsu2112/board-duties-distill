"""Deterministic citation parsing for B1 verification.

Extracts machine-resolvable CFR section cites from the free-text inventory citations.
Statute (U.S.C.) cites, CFR appendices, SR-letter attachment locations, examination-manual
components, and local line-number references are *not* section-addressable in this pass and
are returned as ``UnresolvedCite`` with a precise reason — an honest input to the review
queue, not a guess.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

# e.g. "12 CFR 363.5", "12 CFR 252.33(a)(3)(iv)", "17 CFR 240.13a-14", "12 CFR 225.8(e)(1)(iii)"
_CFR_RE = re.compile(
    r"(?P<title>\d+)\s*CFR\s*(?:part\s*)?(?P<part>\d+)\.(?P<sec>[0-9][0-9A-Za-z\-]*)"
    r"(?P<paras>(?:\([^)]*\))*)"
)


@dataclass(frozen=True)
class CfrCite:
    title: int
    part: str
    section: str  # e.g. "363.5"
    paragraphs: str  # e.g. "(a)(3)(iv)" or ""
    raw: str

    @property
    def label(self) -> str:
        return f"{self.title} CFR {self.section}{self.paragraphs}"


@dataclass(frozen=True)
class UnresolvedCite:
    raw: str
    reason: str


Citation = CfrCite | UnresolvedCite


def _unresolved_reason(text: str) -> str:
    s = text.lower()
    if "u.s.c" in s:
        return "statute cite (U.S.C.); primary text at govinfo/uscode — not resolved in B1-T2"
    if "app." in s or "appendix" in s:
        return "CFR/guidance appendix — not section-addressable in this pass"
    if "local ll" in s or re.search(r"\bll\.", s):
        return "local line-number reference (guidance doc); no addressable primary source"
    if "attachment" in s or "attribute" in s or re.search(r"\bfn\.", s):
        return "guidance-document location (SR-letter attachment / manual); no addressable source"
    if s.startswith("sr ") or " sr " in s[:6]:
        return "SR supervisory letter; retrievable at federalreserve.gov but not parsed in B1-T2"
    if "cfr" in s and "part" in s:
        return "part-level CFR cite; no addressable section"
    return "unrecognized or non-primary citation form"


def parse_citation(text: str) -> list[Citation]:
    """Return the resolvable CFR cites in ``text`` (in order), or a single
    ``UnresolvedCite`` with a reason if none are section-addressable."""
    cites: list[Citation] = []
    for m in _CFR_RE.finditer(text):
        cites.append(
            CfrCite(
                title=int(m.group("title")),
                part=m.group("part"),
                section=f"{m.group('part')}.{m.group('sec')}",
                paragraphs=m.group("paras"),
                raw=m.group(0),
            )
        )
    if cites:
        return cites
    return [UnresolvedCite(raw=text, reason=_unresolved_reason(text))]


def first_cfr(text: str) -> CfrCite | None:
    for c in parse_citation(text):
        if isinstance(c, CfrCite):
            return c
    return None
