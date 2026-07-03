"""B6-T1/T2 — RBI acquisition: sampled Master Directions → sealed answer key + pooled corpus.

Each pre-consolidation Master Direction (fetched from web.archive.org, since RBI's 2025 mega
consolidation withdrew the live individual MDs) carries a structured **repeal appendix** that
lists, with a live circular link each, the source circulars it consolidated. That appendix IS the
held-out grouping answer key: circular → this MD. This module fetches each sampled MD, parses its
appendix into (circular_ref, date, subject, circular_id), then fetches each circular's text (live
RBI ``NotificationUser.aspx?Id=``) into the pooled corpus.

Discipline: the answer key (circular→MD map) is written under ``data/benchmark/answer_key/`` and is
never read by the proposal pipeline (``benchmark_guard``). A circular that cannot be retrieved is
dropped from BOTH the corpus and the answer key symmetrically (§1.1). Cache/manifest discipline
throughout; re-runs are replayable.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from adapters.retrieval import Fetcher
from adapters.textextract import html_to_text


# The sampled Master Directions (M. Hsu approved 2026-07-03). ``wayback_id`` is the pre-2025 RBI
# detail-page id served through the archive; ``domain`` is for the selection memo, never the LLM.
@dataclass(frozen=True)
class SampledMD:
    md_id: str
    wayback_id: str
    snapshot: str  # Wayback snapshot year whose capture links the appendix circulars
    title: str
    domain: str


# The acquired sample (M. Hsu approved 2026-07-03). Four MDs whose pre-2025 archived pages link
# every consolidated circular by Id — a fetchable answer key. KYC and Frauds were DROPPED at
# acquisition (§3.3): KYC's repeal list is plain-text (unlinked ⇒ >15% unretrievable), and the
# Frauds MD's archived snapshots are near-empty. The drop is symmetric (corpus + answer key) and
# costs the KYC/AML and governance/fraud domains — a documented sample-spread limitation.
MD_SAMPLE: list[SampledMD] = [
    SampledMD(
        "MD-DEPOSITS",
        "10296",
        "2023",
        "Master Direction – Interest Rate on Deposits, 2016",
        "deposits / interest-rate",
    ),
    SampledMD(
        "MD-INVPF",
        "12473",
        "2024",
        "Master Direction – Classification, Valuation and Operation of Investment Portfolio",
        "prudential / investment",
    ),
    SampledMD(
        "MD-CARDS",
        "12300",
        "2023",
        "Master Direction – Credit Card and Debit Card – Issuance and Conduct, 2022",
        "conduct / payments",
    ),
    SampledMD(
        "MD-PSL",
        "11959",
        "2023",
        "Master Directions – Priority Sector Lending – Targets and Classification",
        "lending / prudential",
    ),
]

DROPPED_MDS: list[dict[str, str]] = [
    {
        "md": "MD-KYC (wb 11566, KYC/AML)",
        "reason": "repeal appendix lists circulars as plain-text references (unlinked) — "
        ">15% unretrievable by Id (§3.3); dropped symmetrically.",
    },
    {
        "md": "MD-FRAUDS (wb 10477, governance/fraud)",
        "reason": "archived snapshots return a near-empty page; the linked appendix could not "
        "be retrieved (§3.3).",
    },
]

_WAYBACK = "https://web.archive.org/web/{snap}id_/https://www.rbi.org.in/Scripts/BS_ViewMasDirections.aspx?id="
_CIRCULAR = "https://www.rbi.org.in/Scripts/NotificationUser.aspx?Id={id}&Mode=0"

_REF_RE = re.compile(
    r"(?:DBOD|DBR|DBS|DPSS|DNBR|DOR|UBD|RPCD|CO\.DGBA|IDMD|FMRD|FED)\.[A-Za-z0-9./() -]{4,50}"
)


def wayback_md_url(wayback_id: str, snapshot: str = "2023") -> str:
    return _WAYBACK.format(snap=snapshot) + wayback_id


def circular_url(circular_id: str) -> str:
    return _CIRCULAR.format(id=circular_id)


@dataclass
class AppendixEntry:
    circular_id: str
    circular_ref: str
    date: str
    subject: str


def parse_appendix(html: str) -> list[AppendixEntry]:
    """Every appendix row that links a source circular (``NotificationUser.aspx?Id=``). The MD's
    own header row and non-circular rows (no Id link) are skipped. De-duplicated by circular_id.

    Whole-page (not repeal-region-scoped): for the four acquired MDs the page is dominated by its
    consolidated-circular appendix, so whole-page ≈ the answer-key list. The one MD where inline
    citations swamped the appendix (KYC) is dropped, not mis-parsed (see ``DROPPED_MDS``)."""
    entries: dict[str, AppendixEntry] = {}
    for row in re.findall(r"<tr[^>]*>(.*?)</tr>", html, re.S):
        idm = re.search(r"NotificationUser\.aspx\?Id=(\d+)", row)
        if not idm:
            continue
        cid = idm.group(1)
        cells = [
            re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", c)).strip()
            for c in re.findall(r"<td[^>]*>(.*?)</td>", row, re.S)
        ]
        joined = " ".join(cells)
        ref_m = _REF_RE.search(joined)
        date_m = re.search(r"\d{2}[./-]\d{2}[./-]\d{2,4}|\b\w+ \d{1,2}, \d{4}", joined)
        # subject = the longest cell that is not the ref/date (heuristic)
        subject = ""
        for c in sorted(cells, key=len, reverse=True):
            if c and not _REF_RE.fullmatch(c) and not re.fullmatch(r"[\d./,\- ]+", c):
                subject = c
                break
        if cid not in entries:
            entries[cid] = AppendixEntry(
                circular_id=cid,
                circular_ref=ref_m.group(0).strip() if ref_m else "",
                date=date_m.group(0) if date_m else "",
                subject=subject[:200],
            )
    return list(entries.values())


@dataclass
class MDAcquisition:
    md: SampledMD
    entries: list[AppendixEntry] = field(default_factory=list)
    md_page_chars: int = 0


def acquire_md_appendix(md: SampledMD, fetcher: Fetcher) -> MDAcquisition:
    doc = fetcher.fetch(
        wayback_md_url(md.wayback_id, md.snapshot), f"rbi-md-{md.md_id}", title=md.title
    )
    entries = parse_appendix(doc.text)
    return MDAcquisition(md=md, entries=entries, md_page_chars=len(html_to_text(doc.text)))


def fetch_circular_text(circular_id: str, fetcher: Fetcher) -> str | None:
    """Fetch a circular's text by Id (live RBI). Returns None on retrieval failure (dropped
    symmetrically from corpus + answer key)."""
    try:
        doc = fetcher.fetch(circular_url(circular_id), f"rbi-circ-{circular_id}")
    except Exception:  # noqa: BLE001 — unreachable ⇒ dropped, documented
        return None
    text = html_to_text(doc.text)
    # trim the RBI site chrome: keep from the notification body
    idx = text.find("Notifications")
    body = text[idx:] if idx > 0 else text
    return body if len(body) > 300 else None


def circular_clean_text(raw: str) -> str:
    """Strip the RBI masthead/nav boilerplate and the trailing month-archive nav from a circular."""
    t = re.sub(r"\s+", " ", raw)
    # drop the trailing year/month archive navigation that every page carries
    t = re.split(r"\b20\d\d All Months January February", t)[0]
    return t.strip()
