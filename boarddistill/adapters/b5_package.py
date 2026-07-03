"""B5-T5 — per-wave, per-cluster consolidation packages.

Renders ``outputs/b5/<wave>/<cluster>/package.md`` with the AGENTS §9 sections, reusing the
B3 table helpers. The "intended" layer here is the cluster's B5-T4 reform lever (its validated
composition / residual checkpoint), and the authority-to-act table is drawn from the lever's
actor + instrument_required. Both duplication families render in separate tables. Nothing is
``final`` — every package is a review queue, the intended end-state.
"""

from __future__ import annotations

import re
from typing import Any

from adapters.b3_package import _cell, _table
from adapters.diagnose import MIRROR_PAIR, RESTATEMENT, duplication_family


def cluster_slug(cluster: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", cluster.lower()).strip("-")[:32]


def _lever_for(cluster: str, levers: list[dict[str, Any]]) -> dict[str, Any] | None:
    return next((x for x in levers if x["cluster"] == cluster), None)


def render_cluster_package(
    wave: str,
    cluster: str,
    distilled_rows: list[dict[str, Any]],
    findings: list[dict[str, Any]],
    excerpts: dict[str, str],
    vrecords: dict[str, dict[str, Any]],
    graph_nodes: list[dict[str, Any]],
    finding_kind: dict[str, str],
    lever: dict[str, Any] | None,
) -> str:
    parts: list[str] = [f"# Consolidation package — {cluster}\n"]
    parts.append(f"> Wave: `{wave}`. ")
    parts.append(
        "**Status: blocked pending human review.** Every finding is `draft`; none is `final`. "
        "The reform lever below is an illustrative (NG2) proposal, not an adopted instrument.\n"
    )

    verified = sum(
        1 for r in distilled_rows if vrecords.get(r["duty_id"], {}).get("status") == "verified"
    )
    parts.append("## Cluster summary\n")
    parts.append(
        f"- distilled duties: {len(distilled_rows)} (verified: {verified}) · findings: "
        f"{len(findings)} · final: 0 · in-review: "
        f"{sum(1 for f in findings if f['disposition_state'] == 'needs_review')}\n"
    )

    parts.append("\n## As-built duties (distilled)\n")
    ab_rows = [
        [
            r["duty_id"],
            r["distilled"]["verb_standard"],
            r["distilled"]["object"],
            r["distilled"]["cadence"],
            r["distilled"].get("legal_force", "—"),
            "⚠" if not r["anchor_ok"] else "ok",
        ]
        for r in distilled_rows
    ]
    parts.append(_table(["duty_id", "verb", "object", "cadence", "force", "anchor"], ab_rows))

    parts.append("\n## Intended — reform lever (illustrative, NG2)\n")
    if lever is not None:
        parts.append(
            _table(
                ["lever", "status", "composition", "primitives", "effect", "instrument_required"],
                [
                    [
                        lever["min_reform_lever"],
                        lever["status"],
                        lever["composition"],
                        _cell(lever["primitives"]),
                        lever["effect_class"],
                        lever["instrument_required"],
                    ]
                ],
            )
        )
        if lever["status"] == "residual":
            parts.append(
                f"> **Residual checkpoint** — the 16-primitive set did not cleanly express this "
                f"lever in the automated pass: {lever['residual_reason']}\n"
            )
    else:
        parts.append("> No reform lever mapped to this cluster.\n")

    parts.append("\n## Instrument graph (nodes bearing on this cluster)\n")
    parts.append(
        _table(
            ["node", "citation", "agency", "stratum", "treatment"],
            [
                [n["id"], n["citation"], n["agency"], n["stratum"], n["treatment_status"]]
                for n in graph_nodes
            ],
        )
    )

    parts.append("\n## Findings\n")
    parts.append(
        _table(
            ["id", "provision", "effect_class", "normative_kind", "disposition", "status"],
            [
                [f["id"], f["provision"], f["effect_class"], _cell(f["normative_kind"]),
                 f["disposition_state"], f["status"]]
                for f in findings
            ],
        )
    )

    def _family_rows(family: str) -> list[list[Any]]:
        return [
            [f["id"], f["provision"], _cell(f["normative_kind"]), f["disposition_state"]]
            for f in findings
            if duplication_family(finding_kind.get(f["id"], "")) == family
        ]

    fam_headers = ["id", "provision", "normative_kind", "disposition"]
    parts.append("\n## Duplication — mirror pairs (cross-layer / cross-entity)\n")
    parts.append("> Parallel obligations across layer/entity (BHC↔IDI). Lever: reliance / DEEM.\n")
    parts.append(_table(fam_headers, _family_rows(MIRROR_PAIR)))
    parts.append("\n## Duplication — restatements (same text repeated)\n")
    parts.append("> Same obligation restated. Lever: MERGE / RESOLVE_CROSS_REFERENCE.\n")
    parts.append(_table(fam_headers, _family_rows(RESTATEMENT)))

    parts.append("\n## Duty crosswalk (as-built citation → intended home)\n")
    intended_home = lever["composition"] if lever else "—"
    cw_rows = [
        [r["duty_id"], vrecords.get(r["duty_id"], {}).get("status", "—"),
         _cell((vrecords.get(r["duty_id"], {}) or {}).get("checked_span_ids")), intended_home]
        for r in distilled_rows
    ]
    parts.append(
        _table(["duty_id", "verify status", "pinned span", "intended home (lever)"], cw_rows)
    )

    parts.append("\n## Authority to act\n")
    if lever is not None:
        parts.append(
            _table(
                ["reform lever", "actor_with_authority", "instrument_required", "normative_kinds"],
                [[
                    lever["min_reform_lever"], _cell(lever["actor_with_authority"]),
                    lever["instrument_required"], _cell(lever["normative_kinds"]),
                ]],
            )
        )
    else:
        parts.append(_table(["reform lever", "actor_with_authority", "instrument_required"], []))

    parts.append("\n## Claim verification\n")
    parts.append(
        _table(
            ["duty_id", "verify status", "method", "distill anchor"],
            [
                [r["duty_id"], vrecords.get(r["duty_id"], {}).get("status", "—"),
                 vrecords.get(r["duty_id"], {}).get("method", "—"),
                 "anchored" if r["duty_id"] in excerpts else "no excerpt"]
                for r in distilled_rows
            ],
        )
    )

    parts.append("\n## Normative review queue\n")
    parts.append(
        _table(
            ["finding", "provision", "normative_kind (proposed)", "effect"],
            [
                [f["id"], f["provision"], _cell(f["normative_kind"]), f["effect_class"]]
                for f in findings
                if f["normative_kind"] or f["disposition_state"] == "needs_review"
            ],
        )
    )

    parts.append("\n## Final-status blocker summary\n")
    residual_note = (
        "- Reform lever is a **residual checkpoint** (enum did not cleanly express it) — human "
        "decomposition required.\n"
        if lever and lever["status"] == "residual"
        else ""
    )
    parts.append(
        f"- {len(findings)} findings, all `draft` — 0 reach `final`.\n"
        f"- {sum(1 for f in findings if f['disposition_state'] == 'needs_review')} in "
        "`needs_review` (0-op diagnostic ⇒ unresolved effect + needs_review default).\n"
        f"{residual_note}"
        "- Reform lever is illustrative (NG2); cannot finalize without human authorization.\n"
        "- Every normative kind is a proposal; none is resolved (checkpoint discipline).\n"
    )
    return "\n".join(parts)


def build_wave_packages(
    wave: str,
    wave_doc: dict[str, Any],
    distilled_doc: dict[str, Any],
    findings_doc: dict[str, Any],
    verif: dict[str, Any],
    graph_doc: dict[str, Any],
    levers: list[dict[str, Any]],
) -> dict[str, str]:
    """Return ``{cluster_slug: markdown}`` for each cluster in the wave."""
    from adapters.b3_package import _excerpts, _verification_records

    cluster_of = {rid: cl for cl, ids in wave_doc["clusters"].items() for rid in ids}
    excerpts = _excerpts(verif)
    vrecords = _verification_records(verif)
    finding_cluster = findings_doc["finding_cluster"]
    finding_kind = findings_doc.get("finding_kind", {})
    nodes = graph_doc["graph"]["nodes"]

    packages: dict[str, str] = {}
    for cluster in wave_doc["clusters"]:
        distilled_rows = [
            r for r in distilled_doc["rows"] if cluster_of.get(r["duty_id"]) == cluster
        ]
        findings = [f for f in findings_doc["findings"] if finding_cluster.get(f["id"]) == cluster]
        cluster_duties = {r["duty_id"] for r in distilled_rows}
        graph_nodes = [n for n in nodes if set(n.get("bears_on", [])) & cluster_duties]
        packages[cluster_slug(cluster)] = render_cluster_package(
            wave, cluster, distilled_rows, findings, excerpts, vrecords, graph_nodes,
            finding_kind, _lever_for(cluster, levers),
        )
    return packages
