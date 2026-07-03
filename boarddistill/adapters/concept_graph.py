"""B4-T4 — concept-node instrument-graph extension.

The B3 classifier left five consolidation levers ``unresolved`` because their operands are
*concept-level* — ``SOX-404b-attestation``, ``Part363-ICFR-assessment``, the D3 committee-
requirements composite, the D6/D7/D8 targets — that no single duty row (and therefore no
instrument node) carries, so ``baseline_for`` had nothing to answer with. This module adds
typed ``concept_ref`` nodes for exactly those operands, each **grounded to its underlying
instrument node(s) with verbatim span evidence** (no free-floating concepts — checkpoint 3).

``baseline_for`` then resolves every lever's target operand, and the mechanical classifier
(B4-T5) can compute a real effect class instead of refusing. The concept nodes carry the
stratum of their highest-force grounding, so a concept baseline diffs at the right level.

Every grounding quote is verified against the committed source cache (``verify_groundings``);
a quote that does not resolve is a bug, never added.
"""

from __future__ import annotations

import glob
import re
from datetime import date
from html import unescape
from pathlib import Path
from typing import Any

from profiles.lex_balanus.models import InstrumentGraph, InstrumentNode

SOURCES_ROOT = Path("data/sources")

# SR 12-17 is a real cited instrument (D6 relocates its attributes into Reg YY) but is not the
# primary cite of any verified row, so the B2 graph has no node for it. Add it as the grounding
# target for the D6 concept.
_SR_12_17_NODE = {
    "id": "sr-12-17",
    "citation": "SR 12-17 / CA 12-14",
    "agency": "FRB",
    "stratum": "guidance",
    "effective_date": "2012-12-17",
    "treatment_status": "active",
    "kind": "instrument",
    "bears_on": [],
}

# Concept nodes. Each: the concept operand string(s) it answers for (``bears_on``), the stratum
# to diff at, and its groundings (underlying instrument node id + cached source + verbatim quote).
_CONCEPT_NODES: list[dict[str, Any]] = [
    {
        "id": "concept-sox-404b-attestation",
        "citation": "SOX 404(b) external attestation (15 U.S.C. 7262(b))",
        "agency": "SEC",
        "stratum": "statute",
        "effective_date": "2002-07-30",
        "bears_on": ["SOX-404b-attestation"],
        "grounded_to": [
            {
                "instrument_id": "15-u-s-c-7262",
                "source_id": "usc-t15-s7262",
                "quote": "An attestation made under this subsection shall be made in accordance "
                "with standards for attestation engagements issued or adopted by the Board.",
            }
        ],
    },
    {
        "id": "concept-part363-icfr-assessment",
        "citation": "Part 363 ICFR management assessment (12 CFR 363.2)",
        "agency": "FDIC",
        "stratum": "regulation",
        "effective_date": "1993-07-02",
        "bears_on": ["Part363-ICFR-assessment"],
        "grounded_to": [
            {
                "instrument_id": "12-cfr-part-363",
                "source_id": "ecfr-t12-p363",
                "quote": "an assessment by management of the effectiveness of such internal "
                "control structure and procedures as of the end of such fiscal year",
            }
        ],
    },
    {
        "id": "concept-appd-committee-expectations",
        "citation": "App. D board/risk-committee expectations (12 CFR Part 30 App. D)",
        "agency": "OCC",
        "stratum": "enforceable_guideline",
        "effective_date": "2014-09-25",
        "bears_on": ["AppD-committee-expectations"],
        "grounded_to": [
            {
                "instrument_id": "12-cfr-part-30-app-d",
                "source_id": "ecfr-t12-p30",
                "quote": "The board of directors or the board's risk committee reviews and "
                "approves the risk governance framework",
            }
        ],
    },
    {
        "id": "concept-appd-bank-committee-expectations",
        "citation": "App. D bank-level committee expectations (12 CFR Part 30 App. D)",
        "agency": "OCC",
        "stratum": "enforceable_guideline",
        "effective_date": "2014-09-25",
        "bears_on": ["AppD-bank-committee-expectations"],
        "grounded_to": [
            {
                "instrument_id": "12-cfr-part-30-app-d",
                "source_id": "ecfr-t12-p30",
                "quote": "The board of directors or the board's risk committee reviews and "
                "approves the risk governance framework",
            }
        ],
    },
    {
        "id": "concept-consolidated-committee-standard",
        "citation": "Consolidated risk-committee standard (12 CFR 252.33)",
        "agency": "FRB",
        "stratum": "regulation",
        "effective_date": "2014-06-01",
        "bears_on": ["consolidated-committee-standard"],
        "grounded_to": [
            {
                "instrument_id": "12-cfr-part-252",
                "source_id": "ecfr-t12-p252",
                "quote": "must maintain a risk committee that approves and periodically reviews "
                "the risk-management policies of the bank holding company's global operations",
            }
        ],
    },
    {
        "id": "concept-d3-committee-requirements",
        "citation": "D3 audit-committee requirements composite (Part 363 App. A + SOX 301 / "
        "Rule 10A-3 + SOX 404(b))",
        "agency": "interagency",
        "stratum": "statute",
        "effective_date": "2002-07-30",
        "bears_on": ["Part363+SOX301+exchange committee requirements"],
        "grounded_to": [
            {
                "instrument_id": "17-cfr-part-240",
                "source_id": "ecfr-t17-p240",
                "quote": "Listing standards relating to audit committees. (a) Pursuant to "
                "section 10A(m) of the Act (15 U.S.C. 78j-1(m)) and section 3 of the "
                "Sarbanes-Oxley Act of 2002",
            },
            {
                "instrument_id": "15-u-s-c-7262",
                "source_id": "usc-t15-s7262",
                "quote": "An attestation made under this subsection shall be made in accordance "
                "with standards for attestation engagements issued or adopted by the Board.",
            },
        ],
    },
    {
        "id": "concept-d6-sr1217-attributes",
        "citation": "D6 SR 12-17 board-governance attributes",
        "agency": "FRB",
        "stratum": "guidance",
        "effective_date": "2012-12-17",
        "bears_on": ["s:GOV-02..13 (SR 12-17 attributes)"],
        "grounded_to": [
            {
                "instrument_id": "sr-12-17",
                "source_id": "sr-12-17",
                "quote": "The board should set direction and oversight for revenue and profit "
                "generation, risk management and control functions",
            }
        ],
    },
    {
        "id": "concept-d7-board-effectiveness",
        "citation": "D7 board-effectiveness assessment (App. D III.F self-assessment + SR 21-3)",
        "agency": "interagency",
        "stratum": "enforceable_guideline",
        "effective_date": "2014-09-25",
        "bears_on": ["AppD-III.F self-assessment", "SR 21-3 assessment"],
        "grounded_to": [
            {
                "instrument_id": "12-cfr-part-30-app-d",
                "source_id": "ecfr-t12-p30",
                "quote": "A covered bank's board of directors should conduct an annual "
                "self-assessment that includes an evaluation of its effectiveness in meeting "
                "the standards in section III of these Guidelines.",
            },
            {
                "instrument_id": "sr-21-3",
                "source_id": "sr-21-3-att",
                "quote": "attributes of effective boards of directors that have been observed "
                "over time in the course of the Federal Reserve's supervision",
            },
        ],
    },
    {
        "id": "concept-d8-vertical-mirror",
        "citation": "D8 BHC/IDI vertical mirror (Reg YY risk committee ↔ App. D)",
        "agency": "interagency",
        "stratum": "regulation",
        "effective_date": "2014-06-01",
        "bears_on": ["<BHC_duty>", "<IDI_duty>"],
        "grounded_to": [
            {
                "instrument_id": "12-cfr-part-252",
                "source_id": "ecfr-t12-p252",
                "quote": "must maintain a risk committee that approves and periodically reviews "
                "the risk-management policies of the bank holding company's global operations",
            },
            {
                "instrument_id": "12-cfr-part-30-app-d",
                "source_id": "ecfr-t12-p30",
                "quote": "The board of directors or the board's risk committee reviews and "
                "approves the risk governance framework",
            },
        ],
    },
]

# Every B0 concept operand baseline_for must answer for after the extension (DoD).
B0_CONCEPT_OPERANDS: frozenset[str] = frozenset(
    op for node in _CONCEPT_NODES for op in node["bears_on"]
)


def _despace(s: str) -> str:
    return re.sub(r"\s+", "", s)


def _cached_text(source_id: str) -> str:
    paths = [p for p in glob.glob(str(SOURCES_ROOT / source_id / "*")) if "manifest" not in p]
    if not paths:
        raise FileNotFoundError(f"no cached source for {source_id!r}")
    raw = Path(paths[0]).read_text(errors="ignore")
    return re.sub(r"\s+", " ", unescape(re.sub(r"<[^>]+>", " ", raw)))


def verify_groundings() -> dict[str, bool]:
    """True per grounding iff its quote resolves (whitespace-insensitive) to its cached source."""
    out: dict[str, bool] = {}
    for node in _CONCEPT_NODES:
        for i, g in enumerate(node["grounded_to"]):
            ok = _despace(g["quote"]) in _despace(_cached_text(g["source_id"]))
            out[f"{node['id']}[{i}]"] = ok
    return out


def concept_nodes() -> list[InstrumentNode]:
    return [
        InstrumentNode.model_validate(
            {"treatment_status": "active", **n, "kind": "concept_ref"}
        )
        for n in _CONCEPT_NODES
    ]


def extend_graph(base: InstrumentGraph) -> InstrumentGraph:
    """Return ``base`` plus the SR 12-17 grounding node and the concept nodes."""
    nodes = [*base.nodes]
    if not any(n.id == "sr-12-17" for n in nodes):
        nodes.append(InstrumentNode.model_validate(_SR_12_17_NODE))
    nodes.extend(concept_nodes())
    nodes.sort(key=lambda n: n.id)
    return InstrumentGraph(nodes=nodes, edges=list(base.edges))


def extended_graph_document(base_doc: dict[str, Any]) -> dict[str, Any]:
    base = InstrumentGraph.model_validate(base_doc["graph"])
    extended = extend_graph(base)
    verified = verify_groundings()
    as_of = date(2026, 6, 30)
    answered = {op: extended.baseline_for(op, as_of) is not None for op in B0_CONCEPT_OPERANDS}
    return {
        "_meta": "B4-T4 concept-node extension of instrument-graph v1. Typed concept_ref nodes "
        "for the operand-level concepts the reform levers cite, each grounded to underlying "
        "instrument node(s) with verbatim span evidence. baseline_for now answers for every B0 "
        "concept operand.",
        "coverage": {
            **base_doc.get("coverage", {}),
            "concept_nodes": len(_CONCEPT_NODES),
            "grounded_all_verified": all(verified.values()),
            "b0_concept_operands_answered": sum(answered.values()),
            "b0_concept_operands_total": len(B0_CONCEPT_OPERANDS),
        },
        "grounding_verification": verified,
        "concept_operands_answered": answered,
        "graph": extended.model_dump(mode="json"),
    }
