"""B6-T2 — RBI adapter-lite: circular parser + pseudonymizer + InstrumentSummary.

Benchmark-grade only (no full Lex profile). Normalizes each pooled circular into an
``InstrumentSummary`` (DutySpec-like: subject, addressee, date, stratum, body, cross-refs) and
**pseudonymizes every RBI identifier** so the LLM-facing corpus cannot be matched, from parametric
memory, to the Master Direction that consolidated it (leakage control §1.3b). The real↔pseudonym
map is written under ``data/benchmark/pseudonym_map/`` — sealed (``benchmark_guard``), restored
only at scoring. Cross-references between circulars are pseudonymized *consistently*, so the
engine can still detect the cross-reference structure (a RESOLVE_CROSS_REFERENCE / RELATE signal)
without seeing real numbers.

RBI instrument strata (for the summaries): Act → Directions/Regulations → circulars/notifications.
Every pooled document is a ``circular``; referenced Acts/Directions are higher strata.
"""

from __future__ import annotations

import hashlib
import re
from typing import Any

from distillcore.models.base import StrictModel

# RBI reference-number patterns. Matching is deliberately broad — over-scrubbing an identifier is
# safe, under-scrubbing leaks. (a) the "RBI/YYYY[-YY]/NN" master number, allowing spaces and a
# 2- or 4-digit second year; (b) any department-code reference anchored on its trailing fiscal
# year "…/<filecode>/YYYY-YY", which every RBI circular number carries.
_RBI_MASTER = re.compile(r"RBI\s*/\s*\d{4}\s*(?:-\s*\d{2,4}\s*)?/\s*\d+")
_DEPT_REF = re.compile(
    r"(?<![\w/])[A-Z][A-Za-z]{1,6}(?:[.\s()]*(?:No|Dir|BC|BP|PCB|Cir|CO|DGBA|Plan|AML|FSD|Leg|"
    r"Ret|IECD|MC|Ref)\.?)*[.\s()]*(?:No\.?\s*)?\d+\s*/\s*[\d.]{3,}\s*/\s*\d{2,4}\s*[-–]\s*\d{2,4}"
)
# Catch-all for a bare circular file reference "<no>/<filecode>/YYYY-YY" — the trailing structure
# every RBI circular number carries. Scrubs tails left by ranges ("5 & 6/…") and colon variants
# the dept pattern misses. The "/YYYY-YY" fiscal-year suffix is specific to RBI refs (safe).
_FILE_REF = re.compile(r"\d+\s*/\s*[\d.]{3,}\s*/\s*\d{2,4}\s*[-–]\s*\d{2,4}")
_KB_CHROME = re.compile(r"^\s*Notifications\s*\(\s*[\d.]+\s*kb\s*\)\s*", re.I)
_HINDI_DATE = re.compile(r"\b(?:Kartik|Chaitra|Vaisakha|Jyaistha|Asadha|Sravana|Bhadra|Asvina|"
                         r"Kartika|Agrahayana|Pausa|Magha|Phalguna)\s+\d{1,2},\s*\d{4}", re.I)
_DATE = re.compile(r"\b(?:January|February|March|April|May|June|July|August|September|October|"
                   r"November|December)\s+\d{1,2},\s*\d{4}")
_ADDRESSEE = re.compile(r"(All [A-Z][^\n]{5,90}?Banks(?:\s*\([^)]{0,40}\))?)")


def _norm_ref(ref: str) -> str:
    """Normalize an RBI reference for cross-circular matching: drop spaces and case."""
    return re.sub(r"[\s.]", "", ref).lower()


def _pseudo(seed: str, prefix: str) -> str:
    return f"{prefix}-{hashlib.sha1(seed.encode()).hexdigest()[:6]}"


class InstrumentSummary(StrictModel):
    """A benchmark-grade normalized circular. ``doc_id`` is the pseudonym; ``body`` and ``subject``
    are pseudonymized. No real RBI identifier appears in any field."""

    doc_id: str
    stratum: str = "circular"
    subject: str
    addressee: str = ""
    date: str = ""
    cross_refs: list[str] = []  # noqa: RUF012 (pseudonyms of referenced circulars)
    body: str


def parse_circular(text: str) -> dict[str, Any]:
    """Extract raw (pre-pseudonym) fields from a cleaned circular text."""
    t = _KB_CHROME.sub("", text).strip()
    own_master = _RBI_MASTER.search(t)
    own_dept = _DEPT_REF.search(t)
    date_m = _DATE.search(t)
    addr_m = _ADDRESSEE.search(t)
    # subject = the leading title, up to the first identifier/date
    cut = min(
        [m.start() for m in (own_master, own_dept, date_m) if m] or [min(len(t), 160)]
    )
    subject = re.sub(r"\s+", " ", t[:cut]).strip(" -–:")[:200]
    own_refs = [m.group(0) for m in (own_master, own_dept) if m]
    return {
        "subject": subject or t[:120],
        "date": date_m.group(0) if date_m else "",
        "addressee": addr_m.group(1).strip() if addr_m else "",
        "own_refs": own_refs,
        "body": t,
    }


def build_pseudonym_map(corpus: dict[str, str]) -> dict[str, Any]:
    """Assign a stable ``doc_id`` per corpus circular and a global reference→pseudonym map. A
    reference that resolves to a corpus circular maps to its doc_id; any other reference to a stable
    ``EXT-…`` token (an out-of-corpus instrument). Deterministic (sha1), no randomness."""
    doc_id: dict[str, str] = {cid: _pseudo(cid, "DOC") for cid in sorted(corpus)}
    ref_to_doc: dict[str, str] = {}
    for cid in sorted(corpus):
        parsed = parse_circular(corpus[cid])
        for ref in parsed["own_refs"]:
            ref_to_doc[_norm_ref(ref)] = doc_id[cid]
    return {"doc_id": doc_id, "ref_to_doc": ref_to_doc}


def _scrub(text: str, ref_to_doc: dict[str, str], cross: set[str]) -> str:
    """Replace every RBI identifier with its pseudonym; record which corpus docs are cross-ref'd."""

    def repl(m: re.Match[str]) -> str:
        raw = m.group(0)
        key = _norm_ref(raw)
        if key in ref_to_doc:
            cross.add(ref_to_doc[key])
            return ref_to_doc[key]
        return _pseudo(key, "EXT")

    out = _RBI_MASTER.sub(repl, text)
    out = _DEPT_REF.sub(repl, out)
    out = _FILE_REF.sub(repl, out)  # catch ref tails the dept pattern missed
    out = _HINDI_DATE.sub("", out)
    return out


def normalize_corpus(
    corpus: dict[str, str], pmap: dict[str, Any]
) -> list[InstrumentSummary]:
    """Pseudonymized ``InstrumentSummary`` per circular. The self-reference is dropped from
    ``cross_refs`` (a circular does not cross-reference itself)."""
    doc_id = pmap["doc_id"]
    ref_to_doc = pmap["ref_to_doc"]
    out: list[InstrumentSummary] = []
    for cid in sorted(corpus):
        parsed = parse_circular(corpus[cid])
        cross: set[str] = set()
        body = _scrub(parsed["body"], ref_to_doc, cross)
        subject = _scrub(parsed["subject"], ref_to_doc, set())
        cross.discard(doc_id[cid])
        out.append(
            InstrumentSummary(
                doc_id=doc_id[cid],
                subject=re.sub(r"\s+", " ", subject).strip()[:200],
                addressee=parsed["addressee"],
                date=parsed["date"],
                cross_refs=sorted(cross),
                body=re.sub(r"\s+", " ", body).strip(),
            )
        )
    return out


def has_leaked_identifier(text: str) -> bool:
    """True iff a real RBI identifier survived pseudonymization (a §1.3 leakage-scan failure)."""
    return bool(_RBI_MASTER.search(text) or _DEPT_REF.search(text) or _FILE_REF.search(text))
