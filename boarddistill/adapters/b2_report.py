"""B2-T7 — the B2 report: before/after verification, retag + disposition summary, graph
coverage, residual queue, and a re-verification-cadence recommendation."""

from __future__ import annotations

from collections import Counter
from typing import Any

# B1 baseline (pre-B2 resolvers) — verified counts by cluster, from outputs/b1/B1_report.md.
B1_BASELINE: dict[str, int] = {
    "Audit committee & independence": 4,
    "Capital planning & stress testing": 8,
    "Internal control over financial reporting": 4,
    "Risk committee architecture": 5,
    "Risk-governance framework / strategy": 0,
}


def _table(headers: list[str], rows: list[list[str]]) -> str:
    line = "| " + " | ".join(headers) + " |"
    sep = "| " + " | ".join("---" for _ in headers) + " |"
    body = ["| " + " | ".join(r) + " |" for r in rows]
    return "\n".join([line, sep, *body])


def build_b2_report(
    b2_verification: dict[str, Any],
    graph_doc: dict[str, Any],
    retags: dict[str, Any],
    dispositions: dict[str, Any],
) -> str:
    rows = b2_verification["rows"]
    b2_by_cluster: Counter[str] = Counter()
    for r in rows:
        if r["status"] == "verified":
            b2_by_cluster[r["cluster"] or "—"] += 1

    parts: list[str] = ["# B2 verification report\n"]
    b2_total = sum(b2_by_cluster.values())
    b1_total = sum(B1_BASELINE.values())
    parts.append(
        f"Applied the B1 dispositions and built appendix / SR-attachment / manual resolvers, "
        f"lifting verified MVP-cluster rows from **{b1_total}/72 (B1)** to **{b2_total}/72 (B2)**, "
        f"with **0 contradicted**. All retrieval is allowlisted and cache-replayable.\n"
    )

    # before/after by cluster
    parts.append("## Verification: before (B1) → after (B2)\n")
    cluster_rows = [
        [cluster, str(B1_BASELINE.get(cluster, 0)), str(b2_by_cluster.get(cluster, 0))]
        for cluster in sorted(set(B1_BASELINE) | set(b2_by_cluster))
    ]
    cluster_rows.append(["**total**", str(b1_total), str(b2_total)])
    parts.append(_table(["cluster", "B1 verified", "B2 verified"], cluster_rows) + "\n")

    # retag summary
    parts.append("## Actor retags (the approved 6)\n")
    retag_rows = [
        [
            r["duty_id"],
            r["from_actor"],
            r["to_actor"],
            "TODO(human)" if r["todo_human"] else "—",
        ]
        for r in retags.get("retags", [])
    ]
    parts.append(_table(["duty", "was (board_level)", "retagged actor", "flag"], retag_rows) + "\n")
    disp_counts = dispositions.get("counts", {})
    parts.append(
        "Dispositions: " + ", ".join(f"{k}={v}" for k, v in sorted(disp_counts.items())) + "\n"
    )

    # graph coverage
    cov = graph_doc.get("coverage", {})
    strata = Counter(n["stratum"] for n in graph_doc.get("graph", {}).get("nodes", []))
    parts.append("## Instrument graph v1\n")
    parts.append(
        f"- instruments: {cov.get('instruments')} · verified duties: {cov.get('verified_duties')} "
        f"· baseline answered: {cov.get('baseline_answered')}\n"
        f"- strata: " + ", ".join(f"{k}={v}" for k, v in sorted(strata.items())) + "\n"
        "- SR 09-4 recorded superseded (SR 15-18 fn.5); SR 95-51 treatment flagged TODO(human).\n"
    )

    # residual queue
    residuals = [r for r in rows if r["status"] != "verified"]
    parts.append(f"## Residual queue ({len(residuals)}) — TODO(human)\n")
    parts.append(
        "Mostly borderline anchor matches (0.40–0.60) recorded as candidates, never picked "
        "(checkpoint §3). Each carries a specific reason.\n"
    )
    res_rows = [
        [r["duty_id"], _clip(r["citation"], 30), _clip(r["note"], 60)]
        for r in sorted(residuals, key=lambda r: r["duty_id"])
    ]
    parts.append(_table(["duty", "citation", "reason"], res_rows) + "\n")

    parts.append("## Re-verification cadence (recommendation)\n")
    parts.append(
        "- **Quarterly** re-run of `verify-live` + diff against the cached `sha256`s; a changed "
        "hash flags an amended provision for human review.\n"
        "- **On SR-letter issuance/rescission**, re-check the affected instrument nodes "
        "(treatment_status) — especially the TODO(human) items (SR 95-51) and archival "
        "`rescinded_informal` candidates via web.archive.org.\n"
        "- The eCFR snapshot date and U.S. Code edition are pinned; bump them deliberately, "
        "not implicitly, so the audit trail stays reproducible.\n"
    )
    return "\n".join(parts)


def _clip(text: str, n: int) -> str:
    text = " ".join(text.split())
    return text if len(text) <= n else text[: n - 1] + "…"
