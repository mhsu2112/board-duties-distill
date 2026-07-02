"""B1-T0 — deterministic selection of the B1 target rows.

The target set is the three MVP clusters plus the two entangled clusters B0's
decompositions operate on (B1_TASKS §1) — ~72 rows. Selection reads the imported drafts
and filters by cluster; it never re-reads or edits the inventory xlsx.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

# Exact cluster strings from the "All Board Duties" sheet (verbatim match).
TARGET_CLUSTERS: frozenset[str] = frozenset(
    {
        "Risk-governance framework / strategy",
        "Audit committee & independence",
        "Capital planning & stress testing",
        "Risk committee architecture",
        "Internal control over financial reporting",
    }
)


def select_targets(duties: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """The target duties, sorted by duty_id for a stable, deterministic order."""
    selected = [d for d in duties if (d.get("cluster") or "") in TARGET_CLUSTERS]
    return sorted(selected, key=lambda d: str(d["duty_id"]))


def build_targets(import_json: Path) -> dict[str, Any]:
    """Read ``imported_duties.json`` and produce the ``targets.json`` document."""
    doc = json.loads(import_json.read_text())
    targets = select_targets(doc["duties"])
    return {
        "_meta": (
            "B1 target rows (B1_TASKS §1): the three MVP clusters + the two entangled "
            "clusters B0 operates on. Selected deterministically from imported_duties.json; "
            "the inventory xlsx is never edited."
        ),
        "clusters": sorted(TARGET_CLUSTERS),
        "count": len(targets),
        "duty_ids": [str(d["duty_id"]) for d in targets],
        "targets": targets,
    }
