"""B3-T5 — render the three per-cluster consolidation packages (deterministic, no LLM).

One ``package.md`` per MVP cluster with the AGENTS §9 sections: as-built duties, intended
duties, instrument graph, findings, duty crosswalk, authority-to-act, claim verification,
normative review queue, and the blocker summary. Nothing is ``final`` — everything is
blocked pending human review, which is the intended success state (B3-T5).
"""

from __future__ import annotations

from typing import Any

MVP_CLUSTERS = (
    "Risk-governance framework / strategy",
    "Audit committee & independence",
    "Capital planning & stress testing",
)


def cluster_slug(cluster: str) -> str:
    key = {
        "Risk-governance framework / strategy": "risk-governance",
        "Audit committee & independence": "audit-committee",
        "Capital planning & stress testing": "capital-planning",
    }
    return key.get(cluster, cluster.lower().replace(" ", "-")[:20])


def _cell(v: Any) -> str:
    if v is None or v == "":
        return "—"
    if isinstance(v, list):
        return ", ".join(str(x) for x in v) or "—"
    return str(v).replace("\n", " ").replace("|", "\\|")


def _table(headers: list[str], rows: list[list[Any]]) -> str:
    out = ["| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |"]
    for row in rows:
        out.append("| " + " | ".join(_cell(c) for c in row) + " |")
    if not rows:
        out.append("| " + " | ".join("—" for _ in headers) + " |")
    return "\n".join(out) + "\n"


def render_cluster_package(
    cluster: str,
    distilled_rows: list[dict[str, Any]],
    intended_specs: list[dict[str, Any]],
    findings: list[dict[str, Any]],
    excerpts: dict[str, str],
    verification_records: dict[str, dict[str, Any]],
    graph_nodes: list[dict[str, Any]],
) -> str:
    parts: list[str] = [f"# Consolidation package — {cluster}\n"]
    parts.append(
        "> **Status: blocked pending human review.** Every finding below is `draft`; none is "
        "`final`. That is the intended B3 end-state — the package is the review queue, not a "
        "decision. Consolidated/intended duty language is illustrative (NG2), non-authoritative.\n"
    )

    parts.append("## Cluster summary\n")
    parts.append(
        f"- as-built (distilled) duties: {len(distilled_rows)} · intended (illustrative) "
        f"duties: {len(intended_specs)}\n"
        f"- findings: {len(findings)} · final: 0 · in-review: "
        f"{sum(1 for f in findings if f['disposition_state'] == 'needs_review')}\n"
    )

    parts.append("\n## As-built duties (distilled)\n")
    ab_rows = []
    for r in distilled_rows:
        d = r["distilled"]
        ab_rows.append(
            [r["duty_id"], d["verb_standard"], d["object"], d["cadence"], len(d["elements"]),
             "⚠" if not r["anchor_ok"] else "ok"]
        )
    parts.append(_table(["duty_id", "verb", "object", "cadence", "elements", "anchor"], ab_rows))

    parts.append("\n## Intended duties (illustrative — NG2)\n")
    int_rows = [
        [s["duty_id"], s["legal_force"], s["object"], s["entity"], _cell(s["source_citations"])]
        for s in intended_specs
    ]
    parts.append(_table(["duty_id", "force", "object", "entity", "operands cited"], int_rows))

    parts.append("\n## Instrument graph (nodes bearing on this cluster)\n")
    g_rows = [
        [n["id"], n["citation"], n["agency"], n["stratum"], n["treatment_status"]]
        for n in graph_nodes
    ]
    parts.append(_table(["node", "citation", "agency", "stratum", "treatment"], g_rows))

    parts.append("\n## Findings\n")
    f_rows = [
        [f["id"], f["provision"], f["effect_class"], _cell(f["normative_kind"]),
         f["disposition_state"], f["status"]]
        for f in findings
    ]
    f_headers = ["id", "provision", "effect_class", "normative_kind", "disposition", "status"]
    parts.append(_table(f_headers, f_rows))

    parts.append("\n## Duty crosswalk (as-built → intended consolidation)\n")
    cw_rows = []
    for f in findings:
        if f["intended_ref"]:
            cw_rows.append([f["as_built_ref"] or "—", f["intended_ref"], f["effect_class"]])
    parts.append(_table(["as-built duty", "intended home", "effect"], cw_rows))

    parts.append("\n## Authority to act\n")
    at_rows = []
    seen = set()
    for f in findings:
        key = f["provision"]
        if key in seen:
            continue
        seen.add(key)
        at_rows.append([f["provision"], f["effect_class"], f["disposition_state"]])
    parts.append(_table(["provision", "effect_class", "disposition"], at_rows))

    parts.append("\n## Claim verification\n")
    cv_rows = []
    for r in distilled_rows:
        rec = verification_records.get(r["duty_id"], {})
        cv_rows.append([r["duty_id"], rec.get("status", "—"), rec.get("method", "—"),
                        "anchored" if r["duty_id"] in excerpts else "no excerpt"])
    parts.append(_table(["duty_id", "verify status", "method", "distill anchor"], cv_rows))

    parts.append("\n## Normative review queue\n")
    nq_rows = [
        [f["id"], f["provision"], _cell(f["normative_kind"]), f["effect_class"]]
        for f in findings
        if f["normative_kind"] or f["disposition_state"] == "needs_review"
    ]
    parts.append(_table(["finding", "provision", "normative_kind (proposed)", "effect"], nq_rows))

    parts.append("\n## Final-status blocker summary\n")
    blockers = [
        f"- {len(findings)} findings, all `draft` — 0 reach `final`.",
        f"- {sum(1 for f in findings if f['disposition_state'] == 'needs_review')} in "
        "`needs_review` (normative kind proposed, effect=change, or no baseline).",
        "- Intended/consolidated duty language is illustrative (NG2) and unverified — cannot "
        "finalize without human authorization.",
        "- Every normative kind is a proposal; none is resolved (checkpoint discipline).",
    ]
    parts.append("\n".join(blockers) + "\n")
    return "\n".join(parts)


# --- assembly -------------------------------------------------------------------------


def _duty_cluster_of(verification: dict[str, Any]) -> dict[str, str]:
    return {row["duty_id"]: row.get("cluster", "") for row in verification["rows"]}


def _verification_records(verification: dict[str, Any]) -> dict[str, dict[str, Any]]:
    records = {r["claim_id"]: r for r in verification["records"]}
    out: dict[str, dict[str, Any]] = {}
    for row in verification["rows"]:
        rec = records.get(f"claim-{row['duty_id']}")
        if rec:
            out[row["duty_id"]] = rec
    return out


def _excerpts(verification: dict[str, Any]) -> dict[str, str]:
    records = {r["claim_id"]: r for r in verification["records"]}
    spans = {s["id"]: s for s in verification["spans"]}
    out: dict[str, str] = {}
    for row in verification["rows"]:
        rec = records.get(f"claim-{row['duty_id']}")
        if rec and rec["checked_span_ids"]:
            span = spans.get(rec["checked_span_ids"][0])
            if span:
                out[row["duty_id"]] = span["quote"]
    return out


def _graph_nodes_for(cluster_duties: set[str], graph_doc: dict[str, Any]) -> list[dict[str, Any]]:
    nodes = graph_doc["graph"]["nodes"]
    return [n for n in nodes if set(n.get("bears_on", [])) & cluster_duties]


def build_packages(
    distilled_doc: dict[str, Any],
    intended_doc: dict[str, Any],
    findings_doc: dict[str, Any],
    verification: dict[str, Any],
    graph_doc: dict[str, Any],
) -> dict[str, str]:
    """Return ``{cluster_slug: package_markdown}`` for the three MVP clusters."""
    cluster_of = _duty_cluster_of(verification)
    excerpts = _excerpts(verification)
    vrecords = _verification_records(verification)
    finding_cluster = findings_doc["finding_cluster"]

    packages: dict[str, str] = {}
    for cluster in MVP_CLUSTERS:
        distilled_rows = [
            r for r in distilled_doc["rows"] if cluster_of.get(r["duty_id"]) == cluster
        ]
        intended_specs = [
            d["intended_spec"] for d in intended_doc["decompositions"] if d["cluster"] == cluster
        ]
        findings = [
            f for f in findings_doc["findings"] if finding_cluster.get(f["id"]) == cluster
        ]
        cluster_duties = {r["duty_id"] for r in distilled_rows}
        graph_nodes = _graph_nodes_for(cluster_duties, graph_doc)
        packages[cluster_slug(cluster)] = render_cluster_package(
            cluster, distilled_rows, intended_specs, findings, excerpts, vrecords, graph_nodes
        )
    return packages
