"""B5-T1 — the wave plan.

Partition the ~155 non-MVP duty rows into domain waves. The five MVP clusters (the B1 target
set) are already carried through B1-B4 and are excluded here. Every remaining cluster is assigned
to exactly one wave by the deterministic ``_WAVE_OF_CLUSTER`` table below; a non-MVP cluster with
no assignment is a hard error (so a new cluster string can never be silently dropped).

Six waves, each a coherent supervisory domain, sized for a manageable per-wave verify/distill
pass (the MVP experience: ~20-35 rows per pass). Row IDs within a wave/cluster are sorted for a
stable, replayable ``waves.json``.
"""

from __future__ import annotations

from typing import Any

from adapters.b1_targets import TARGET_CLUSTERS

# Wave definitions: wave slug -> ordered list of the inventory cluster strings it covers.
# The union of these clusters must equal (all clusters) minus the five MVP clusters.
WAVES: list[tuple[str, str, list[str]]] = [
    (
        "w1-liquidity-resolution",
        "Liquidity & resolution/recovery",
        [
            "Liquidity risk management",
            "Resolution, recovery & contingency funding",
        ],
    ),
    (
        "w2-opres-cyber-model",
        "Operational resilience, cyber & model risk",
        [
            "Information security & cybersecurity",
            "Operational resilience / business continuity",
            "Model risk governance",
        ],
    ),
    (
        "w3-thirdparty-inccomp",
        "Third-party & incentive compensation",
        [
            "Third-party risk management",
            "Incentive compensation",
        ],
    ),
    (
        "w4-bsa-consumer",
        "BSA/AML & consumer compliance",
        [
            "BSA/AML program",
            "Consumer compliance (CMS)",
        ],
    ),
    (
        "w5-credit-insider",
        "Credit & insider/affiliate lending",
        [
            "Credit risk governance",
            "Insider / affiliate / related-party",
        ],
    ),
    (
        "w6-governance-structural",
        "Governance, independence & structural",
        [
            "Director independence (cross-cutting)",
            "Risk appetite statement",
            "Unique structural duties",
            "Personal liability",
            "Board self-assessment / effectiveness",
            "Director eligibility & continuity",
            "CRO / CRE appointment & compensation",
            "Director training",
            "Fiduciary (trust) governance",
            "Safety-and-soundness baseline",
            "Source of strength / charter sanctity",
        ],
    ),
]

_WAVE_OF_CLUSTER: dict[str, str] = {
    cluster: slug for slug, _title, clusters in WAVES for cluster in clusters
}


def _non_mvp_clusters(duties: list[dict[str, Any]]) -> set[str]:
    return {(d.get("cluster") or "") for d in duties} - set(TARGET_CLUSTERS)


def build_wave_plan(duties: list[dict[str, Any]]) -> dict[str, Any]:
    """Assign every non-MVP row to exactly one wave. Raises on an unassigned cluster."""
    present_non_mvp = _non_mvp_clusters(duties)
    unassigned = sorted(c for c in present_non_mvp if c and c not in _WAVE_OF_CLUSTER)
    if unassigned:
        raise ValueError(f"non-MVP clusters with no wave assignment: {unassigned}")

    # cluster -> sorted row ids (non-MVP only)
    by_cluster: dict[str, list[str]] = {}
    for d in duties:
        cluster = d.get("cluster") or ""
        if cluster in TARGET_CLUSTERS or not cluster:
            continue
        by_cluster.setdefault(cluster, []).append(str(d["duty_id"]))
    for cluster in by_cluster:
        by_cluster[cluster].sort()

    waves: list[dict[str, Any]] = []
    total = 0
    for slug, title, clusters in WAVES:
        cluster_rows = {c: by_cluster.get(c, []) for c in clusters if by_cluster.get(c)}
        count = sum(len(v) for v in cluster_rows.values())
        total += count
        waves.append(
            {
                "wave": slug,
                "title": title,
                "clusters": cluster_rows,
                "row_count": count,
                "cluster_count": len(cluster_rows),
            }
        )

    all_rows = [r for w in waves for rows in w["clusters"].values() for r in rows]
    assert len(all_rows) == len(set(all_rows)), "a row landed in two waves"
    non_mvp_total = sum(
        1 for d in duties if (d.get("cluster") or "") not in TARGET_CLUSTERS and d.get("cluster")
    )
    return {
        "_meta": "B5-T1 wave plan. The ~155 non-MVP duty rows partitioned into six domain waves "
        "(the five MVP clusters excluded — already carried through B1-B4). Deterministic: cluster→"
        "wave is a fixed table, row IDs sorted. Every non-MVP row lands in exactly one wave.",
        "counts": {
            "waves": len(waves),
            "non_mvp_rows_assigned": total,
            "non_mvp_rows_total": non_mvp_total,
            "mvp_clusters_excluded": sorted(TARGET_CLUSTERS),
        },
        "waves": waves,
    }
