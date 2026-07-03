"""B2-T6 — build instrument-graph v1 from the B2 verification.

One InstrumentNode per instrument the 72 rows cite (statutes, regs, CFR appendices, SR
letters, manuals): stratum, agency, effective date, and treatment_status with evidence.
``bears_on`` is populated from the verified rows so ``baseline_for`` answers for every
verified duty. Fixture graphs are untouched. Treatment-status calls that need judgment are
flagged, not decided (§checkpoint 4).
"""

from __future__ import annotations

import re
from datetime import date
from typing import Any

from distillcore.pipeline.verify import RowVerification
from profiles.lex_balanus.models import InstrumentGraph, InstrumentNode

# Per-instrument metadata (agency, stratum, effective date, treatment). Keys are the
# instrument keys produced by ``instrument_key``.
_META: dict[str, dict[str, Any]] = {
    "12 CFR Part 363": {"agency": "FDIC", "stratum": "regulation", "eff": "1993-07-02"},
    "12 CFR Part 252": {"agency": "FRB", "stratum": "regulation", "eff": "2014-06-01"},
    "12 CFR Part 225": {"agency": "FRB", "stratum": "regulation", "eff": "1984-01-01"},
    "12 CFR Part 9": {"agency": "OCC", "stratum": "regulation", "eff": "1996-12-30"},
    "17 CFR Part 240": {"agency": "SEC", "stratum": "regulation", "eff": "2003-08-29"},
    "12 CFR Part 30 App. A": {
        "agency": "OCC",
        "stratum": "enforceable_guideline",
        "eff": "1995-08-09",
    },
    "12 CFR Part 30 App. D": {
        "agency": "OCC",
        "stratum": "enforceable_guideline",
        "eff": "2014-09-25",
    },
    "12 U.S.C. 1831m": {"agency": "Congress", "stratum": "statute", "eff": "1991-12-19"},
    "12 U.S.C. 5365": {"agency": "Congress", "stratum": "statute", "eff": "2010-07-21"},
    "15 U.S.C. 7262": {"agency": "Congress", "stratum": "statute", "eff": "2002-07-30"},
    "SR 21-3": {"agency": "FRB", "stratum": "guidance", "eff": "2021-02-26"},
    "SR 15-18": {"agency": "FRB", "stratum": "guidance", "eff": "2015-12-18"},
    "SR 12-7": {"agency": "FRB", "stratum": "guidance", "eff": "2012-05-14"},
    "SR 13-1": {"agency": "FRB", "stratum": "guidance", "eff": "2013-01-23"},
    "SR 19-3": {"agency": "FRB", "stratum": "guidance", "eff": "2019-02-26"},
    "SR 12-17": {"agency": "FRB", "stratum": "guidance", "eff": "2012-12-17"},
    "SR 95-51": {
        "agency": "FRB",
        "stratum": "guidance",
        "eff": "1995-11-14",
        "treatment_evidence": "TODO(human) §checkpoint 4: SR 95-51 (1995) may be dated/"
        "informally superseded by later risk-management rating guidance — treatment not decided.",
    },
    "OCC Comptroller's Handbook: Corporate & Risk Governance": {
        "agency": "OCC",
        "stratum": "manual",
        "eff": "2019-07-01",
    },
    "FDIC RMS Manual: Management": {"agency": "FDIC", "stratum": "manual", "eff": "2005-01-01"},
}

# Instruments referenced but not the primary cite of any row (added per B2-T6).
_EXTRA_NODES = [
    {
        "id": "sr-09-4",
        "citation": "SR 09-4",
        "agency": "FRB",
        "stratum": "guidance",
        "effective_date": "2009-03-27",
        "treatment_status": "superseded",
        "treatment_date": "2015-12-18",
        "treatment_evidence": "SR 15-18 fn. 5 supersedes SR 09-4 for GSIBs (cited by s:CAP-11).",
        "bears_on": ["s:CAP-11"],
    }
]


def instrument_key(source_id: str, citation: str) -> str:
    if source_id.startswith("sr-"):
        parts = source_id.split("-")
        return f"SR {parts[1]}-{parts[2]}"
    if source_id.startswith("usc-"):
        m = re.match(r"(\d+ U\.S\.C\. \d+[A-Za-z]?)", citation)
        return m.group(1) if m else citation
    if source_id == "occ-ch-crg":
        return "OCC Comptroller's Handbook: Corporate & Risk Governance"
    if source_id == "fdic-rms-mgmt":
        return "FDIC RMS Manual: Management"
    if source_id.startswith("ecfr-"):
        m = re.match(r"(\d+)\s*CFR\s*(?:Part\s*)?(\d+)", citation)
        if m is None:
            return citation
        if "App." in citation:
            app = re.search(r"App\.\s*([A-Z])", citation)
            letter = app.group(1) if app else "?"
            return f"{m.group(1)} CFR Part {m.group(2)} App. {letter}"
        return f"{m.group(1)} CFR Part {m.group(2)}"
    return citation


def _slug(key: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", key.lower()).strip("-")


def build_instrument_graph(rows: list[RowVerification]) -> InstrumentGraph:
    bears_on: dict[str, list[str]] = {}
    citation_of: dict[str, str] = {}
    for row in rows:
        if row.record.status != "verified" or row.verdict.span is None:
            continue
        key = instrument_key(row.verdict.span.source_id, row.verdict.span.citation)
        bears_on.setdefault(key, [])
        if row.duty_id not in bears_on[key]:
            bears_on[key].append(row.duty_id)
        citation_of.setdefault(key, row.verdict.span.citation)

    nodes: list[InstrumentNode] = []
    for key in sorted(bears_on):
        meta = _META.get(key, {"agency": "unknown", "stratum": "guidance", "eff": "2000-01-01"})
        nodes.append(
            InstrumentNode.model_validate(
                {
                    "id": _slug(key),
                    "citation": key,
                    "agency": meta["agency"],
                    "stratum": meta["stratum"],
                    "effective_date": meta["eff"],
                    "treatment_status": "active",
                    "treatment_evidence": meta.get("treatment_evidence"),
                    "bears_on": sorted(bears_on[key]),
                }
            )
        )
    nodes.extend(InstrumentNode.model_validate(n) for n in _EXTRA_NODES)
    nodes.sort(key=lambda n: n.id)
    return InstrumentGraph(nodes=nodes, edges=[])


def graph_document(graph: InstrumentGraph, rows: list[RowVerification]) -> dict[str, Any]:
    verified = [r.duty_id for r in rows if r.record.status == "verified"]
    covered = {d for n in graph.nodes for d in n.bears_on}
    as_of = date(2026, 6, 30)
    answered = sum(1 for d in verified if graph.baseline_for(d, as_of) is not None)
    return {
        "_meta": "Instrument-graph v1 (B2-T6). One node per instrument the 72 MVP rows cite; "
        "bears_on from B2 verification. Treatment-status judgment calls are flagged, not decided.",
        "coverage": {
            "instruments": len(graph.nodes),
            "verified_duties": len(verified),
            "baseline_answered": answered,
        },
        "graph": graph.model_dump(mode="json"),
        "_verified_not_covered": sorted(set(verified) - covered),
    }
