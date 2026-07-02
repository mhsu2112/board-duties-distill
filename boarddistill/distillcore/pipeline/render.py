"""Render the consolidation package (``package.md``) from the JSON stage outputs.

Profile-independent: reads only the written JSON (as_built / intended / instrument_graph
/ findings / verification / review_queue), so the same renderer serves any profile.
Sections and their order follow AGENTS §9.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .verify import finalization_blocker_lines


def _load(path: Path) -> dict[str, Any]:
    data: dict[str, Any] = json.loads(path.read_text())
    return data


def _table(headers: list[str], rows: list[list[str]]) -> str:
    line = "| " + " | ".join(headers) + " |"
    sep = "| " + " | ".join("---" for _ in headers) + " |"
    body = ["| " + " | ".join(_cell(c) for c in row) + " |" for row in rows]
    return "\n".join([line, sep, *body]) if rows else line + "\n" + sep + "\n| _(none)_ |"


def _cell(value: Any) -> str:
    if isinstance(value, list):
        return ", ".join(str(v) for v in value) if value else "—"
    return str(value) if value not in (None, "") else "—"


def render_package(fixture_out: Path) -> str:
    as_built = _load(fixture_out / "as_built.json")["duties"]
    intended = _load(fixture_out / "intended.json")["duties"]
    graph = _load(fixture_out / "instrument_graph.json")
    findings_doc = _load(fixture_out / "findings.json")
    verification = _load(fixture_out / "verification.json")
    review_queue = _load(fixture_out / "review_queue.json")

    findings = findings_doc["findings"]
    ops_by_id = {op["id"]: op for op in findings_doc["operations"]}

    parts: list[str] = [f"# Consolidation package — {fixture_out.name}\n"]

    # 1. snapshot dates
    snap = as_built[0]["snapshot_dates"] if as_built else {}
    parts.append("## Snapshot dates\n")
    parts.append(
        f"- inventory_as_of: {snap.get('inventory_as_of', '—')}\n"
        f"- consolidation_as_of: {snap.get('consolidation_as_of', '—')}\n"
        f"- current_as_of: {snap.get('current_as_of', '—')}\n"
    )

    # 2. cluster summary
    parts.append("## Cluster summary\n")
    parts.append(
        f"- as-built duties: {len(as_built)} · intended duties: {len(intended)}\n"
        f"- findings: {len(findings)} · residuals: {len(findings_doc.get('residuals', []))} "
        f"· invariant violations: {len(findings_doc.get('invariant_violations', []))}\n"
    )

    # 3 + 4. duty tables
    duty_headers = ["duty_id", "actor/level", "verb", "object", "cadence", "force", "instrument"]

    def _duty_rows(duties: list[dict[str, Any]]) -> list[list[str]]:
        return [
            [
                d["duty_id"],
                d["board_level"],
                d["verb_standard"],
                d["object"],
                d["cadence"],
                d["legal_force"],
                d["instrument_id"],
            ]
            for d in duties
        ]

    parts.append("## As-built duties\n")
    parts.append(_table(duty_headers, _duty_rows(as_built)) + "\n")
    parts.append("## Intended duties\n")
    parts.append(_table(duty_headers, _duty_rows(intended)) + "\n")

    # 5. instrument-graph summary
    parts.append("## Instrument graph\n")
    graph_rows = [
        [n["id"], n["citation"], n["agency"], n["stratum"], n["treatment_status"]]
        for n in graph.get("nodes", [])
    ]
    parts.append(
        _table(["node", "citation", "agency", "stratum", "treatment_status"], graph_rows) + "\n"
    )

    # 6. findings table
    parts.append("## Findings\n")
    finding_rows: list[list[str]] = []
    for f in findings:
        ops = [ops_by_id[o] for o in f["operation_ids"] if o in ops_by_id]
        primitives = [op["primitive"] for op in ops]
        actors = sorted({a for op in ops for a in op.get("actor_with_authority", [])})
        instruments = sorted(
            {op["instrument_required"] for op in ops if op.get("instrument_required")}
        )
        finding_rows.append(
            [
                f.get("intended_ref") or f.get("as_built_ref") or f["provision"],
                ", ".join(primitives),
                f["effect_class"],
                ", ".join(f.get("normative_kind", [])) or "—",
                ", ".join(actors) or "—",
                ", ".join(instruments) or "—",
                f["disposition_state"],
            ]
        )
    parts.append(
        _table(
            [
                "duty",
                "primitive",
                "effect_class",
                "normative_kind",
                "actor",
                "instrument",
                "disposition",
            ],
            finding_rows,
        )
        + "\n"
    )

    # 7. duty crosswalk
    parts.append("## Duty crosswalk (old citation → intended home)\n")
    intended_ids = {d["duty_id"] for d in intended}
    crosswalk_rows = [
        [
            d["duty_id"],
            d["instrument_id"],
            d["duty_id"] if d["duty_id"] in intended_ids else "consolidated / retired",
        ]
        for d in as_built
    ]
    parts.append(_table(["old duty", "old instrument", "intended home"], crosswalk_rows) + "\n")

    # 8. authority-to-act table
    parts.append("## Authority to act\n")
    authority_rows = []
    for f in findings:
        ops = [ops_by_id[o] for o in f["operation_ids"] if o in ops_by_id]
        actors = sorted({a for op in ops for a in op.get("actor_with_authority", [])})
        instruments = sorted(
            {op["instrument_required"] for op in ops if op.get("instrument_required")}
        )
        authority_rows.append(
            [f["provision"], ", ".join(actors) or "—", ", ".join(instruments) or "—"]
        )
    parts.append(
        _table(["provision", "actor_with_authority", "instrument_required"], authority_rows) + "\n"
    )

    # 9. claim-verification table
    parts.append("## Claim verification\n")
    claim_rows = [
        [r["claim_id"], r["status"], r["method"], r.get("note") or "—"]
        for r in verification.get("records", [])
    ]
    parts.append(_table(["claim", "status", "method", "note"], claim_rows) + "\n")

    # 10. normative review queue
    parts.append("## Normative review queue\n")
    queue_rows = [
        [q["finding_id"], q["provision"], q["effect_class"], ", ".join(q["normative_kind"]) or "—"]
        for q in review_queue.get("needs_review", [])
    ]
    parts.append(
        _table(["finding", "provision", "effect_class", "normative_kind"], queue_rows) + "\n"
    )

    # 11. final-status blocker summary
    parts.append("## Final-status blocker summary\n")
    blocker_lines = finalization_blocker_lines(findings, verification.get("claim_status", {}))
    parts.append("\n".join(blocker_lines) + "\n")

    return "\n".join(parts)
