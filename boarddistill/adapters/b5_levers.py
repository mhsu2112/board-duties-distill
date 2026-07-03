"""B5-T4 (extraction) — the remaining reform levers to decompose.

Reads the inventory's ``Duplicate Clusters`` sheet (the per-cluster "Minimum reform lever")
for the non-MVP clusters — the ~22 levers beyond the MVP five — and enriches each with the
matching ``Reform Roadmap`` row (actor, authority, instrument, statutory obstacle). Deterministic
and read-only: the xlsx is never modified. The LLM decomposition (adapters.b5_decompose) consumes
these records; this module only sources and structures them.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from openpyxl import load_workbook

from adapters.b1_targets import TARGET_CLUSTERS

# Clusters that are explicitly NOT consolidation targets in the inventory (documented, not
# decomposed): personal liability runs to the individual, not a board action; the "unique
# structural" GSIB duties are retained by distinct purpose.
_NON_CONSOLIDATION_CLUSTERS: frozenset[str] = frozenset(
    {
        "Personal & individual-director liability",
        "Personal liability",
        "Unique structural duties",
    }
)

# Explicit cluster -> Reform Roadmap row index (0-based within the data rows) for the clusters
# that carry a roadmap entry. Kept explicit (auditable) rather than fuzzy-matched.
_ROADMAP_FOR_CLUSTER: dict[str, str] = {
    "Risk appetite statement": "Single consolidated risk-appetite statement",
    "Director independence (cross-cutting)": "Single 'independent director' definition",
    "Resolution, recovery & contingency funding": "Integrate recovery",
    "Information security & cybersecurity": "One enterprise information-security program",
    "Incentive compensation": "Dodd-Frank §956",
    "Third-party risk management": "Quantitative 'critical activity' threshold",
    "Board self-assessment / effectiveness": "board-effectiveness assessment",
    "Operational resilience / business continuity": "risk-appetite",  # folds into risk-appetite
}


def _slug(cluster: str) -> str:
    return "L-" + re.sub(r"[^a-z0-9]+", "-", cluster.lower()).strip("-")[:20]


def _sheet_rows(path: Path, sheet: str) -> list[tuple[Any, ...]]:
    wb = load_workbook(path, read_only=True, data_only=True)
    try:
        return [tuple(r) for r in wb[sheet].iter_rows(values_only=True)]
    finally:
        wb.close()


def _roadmap_index(path: Path) -> list[dict[str, str]]:
    rows = _sheet_rows(path, "Reform Roadmap")
    # header is row index 2: Reform | Actor | Authority | Instrument | Difficulty | ... | Statutory
    out: list[dict[str, str]] = []
    for r in rows[3:]:
        if not r or r[0] is None:
            continue
        out.append(
            {
                "reform": str(r[0]),
                "actor": str(r[1]) if len(r) > 1 and r[1] else "",
                "authority": str(r[2]) if len(r) > 2 and r[2] else "",
                "instrument": str(r[3]) if len(r) > 3 and r[3] else "",
                "difficulty": str(r[4]) if len(r) > 4 and r[4] else "",
                "statutory_obstacle": str(r[7]) if len(r) > 7 and r[7] else "",
            }
        )
    return out


def _match_roadmap(cluster: str, roadmap: list[dict[str, str]]) -> dict[str, str] | None:
    needle = _ROADMAP_FOR_CLUSTER.get(cluster)
    if not needle:
        return None
    for row in roadmap:
        if needle.lower() in row["reform"].lower():
            return row
    return None


def extract_levers(path: Path) -> dict[str, Any]:
    """The non-MVP reform levers, each with cluster context + roadmap enrichment."""
    rows = _sheet_rows(path, "Duplicate Clusters")
    roadmap = _roadmap_index(path)
    levers: list[dict[str, Any]] = []
    for r in rows[3:]:  # header at index 2
        cluster = r[0]
        if cluster is None or str(cluster) in TARGET_CLUSTERS:
            continue
        cluster = str(cluster)
        lever = {
            "lever_id": _slug(cluster),
            "cluster": cluster,
            "duty_count": r[1],
            "redundancy": str(r[2]) if len(r) > 2 and r[2] else "",
            "overlapping_sources": str(r[3]) if len(r) > 3 and r[3] else "",
            "whats_duplicative": str(r[4]) if len(r) > 4 and r[4] else "",
            "whats_distinct": str(r[5]) if len(r) > 5 and r[5] else "",
            "min_reform_lever": str(r[6]) if len(r) > 6 and r[6] else "",
            "non_consolidation": cluster in _NON_CONSOLIDATION_CLUSTERS,
            "roadmap": _match_roadmap(cluster, roadmap),
        }
        levers.append(lever)
    levers.sort(key=lambda x: x["lever_id"])
    return {
        "_meta": "B5-T4 lever source: the non-MVP clusters' minimum reform levers (Duplicate "
        "Clusters sheet) + Reform Roadmap enrichment. Read-only from the inventory xlsx.",
        "counts": {
            "levers": len(levers),
            "consolidation_targets": sum(1 for x in levers if not x["non_consolidation"]),
            "non_consolidation": sum(1 for x in levers if x["non_consolidation"]),
        },
        "levers": levers,
        "roadmap_rows": roadmap,
    }
