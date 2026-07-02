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
# e.g. "12 U.S.C. 1831m", "15 U.S.C. 7262(b)", "12 U.S.C. 5365(h)(1)"
_USC_RE = re.compile(
    r"(?P<title>\d+)\s*U\.?\s*S\.?\s*C\.?\s*§?\s*(?P<sec>\d+[A-Za-z]?(?:-\d+)?)(?P<paras>(?:\([^)]*\))*)"
)
# e.g. "SR 12-17", "SR 21-3", "SR 15-18 fn. 5"
_SR_RE = re.compile(r"\bSR\s*(?P<yr>\d{2})-(?P<num>\d{1,2})\b")
# e.g. "12 CFR Part 30, App. D, II.A", "12 CFR Part 363, App. A"
_APPX_RE = re.compile(
    r"(?P<title>\d+)\s*CFR\s*Part\s*(?P<part>\d+)\s*,?\s*App(?:endix|\.)\s*(?P<appx>[A-Z])"
    r"(?:\s*,?\s*(?:secs?\.?)?\s*(?P<sub>[IVX]+\.[A-Za-z0-9().]+))?",
    re.I,
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
class UscCite:
    title: int
    section: str  # e.g. "1831m", "7262", "5365"
    paragraphs: str
    raw: str

    @property
    def label(self) -> str:
        return f"{self.title} U.S.C. {self.section}{self.paragraphs}"


@dataclass(frozen=True)
class SrCite:
    year: str  # "12"
    number: str  # "17"
    raw: str

    @property
    def label(self) -> str:
        return f"SR {self.year}-{self.number}"


@dataclass(frozen=True)
class CfrAppendixCite:
    title: int
    part: str
    appendix: str  # "D"
    subsection: str | None  # "II.A" or None
    raw: str

    @property
    def label(self) -> str:
        base = f"{self.title} CFR Part {self.part}, App. {self.appendix}"
        return f"{base}, {self.subsection}" if self.subsection else base


@dataclass(frozen=True)
class UnresolvedCite:
    raw: str
    reason: str


Resolvable = CfrCite | CfrAppendixCite | UscCite | SrCite
Citation = Resolvable | UnresolvedCite


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
    """Classify ``text`` into resolvable cites, most-reliable type first (CFR section,
    then CFR appendix, then U.S.C., then SR letter), or a single ``UnresolvedCite``."""
    cfr = [
        CfrCite(
            title=int(m.group("title")),
            part=m.group("part"),
            section=f"{m.group('part')}.{m.group('sec')}",
            paragraphs=m.group("paras"),
            raw=m.group(0),
        )
        for m in _CFR_RE.finditer(text)
    ]
    if cfr:
        return list(cfr)

    appx = _APPX_RE.search(text)
    if appx:
        return [
            CfrAppendixCite(
                title=int(appx.group("title")),
                part=appx.group("part"),
                appendix=appx.group("appx").upper(),
                subsection=appx.group("sub"),
                raw=appx.group(0),
            )
        ]

    usc = [
        UscCite(
            title=int(m.group("title")),
            section=m.group("sec"),
            paragraphs=m.group("paras"),
            raw=m.group(0),
        )
        for m in _USC_RE.finditer(text)
    ]
    if usc:
        return list(usc)

    sr = _SR_RE.search(text)
    if sr:
        return [SrCite(year=sr.group("yr"), number=sr.group("num"), raw=sr.group(0))]

    return [UnresolvedCite(raw=text, reason=_unresolved_reason(text))]


def first_resolvable(text: str) -> Resolvable | None:
    for c in parse_citation(text):
        if not isinstance(c, UnresolvedCite):
            return c
    return None


def first_cfr(text: str) -> CfrCite | None:
    for c in parse_citation(text):
        if isinstance(c, CfrCite):
            return c
    return None
