"""B5-T1 — wave plan partition invariants."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from adapters.b1_targets import TARGET_CLUSTERS
from adapters.b5_waves import build_wave_plan

_ROOT = Path(__file__).resolve().parents[1]
_IMPORT = _ROOT / "outputs" / "import" / "imported_duties.json"


@pytest.mark.skipif(not _IMPORT.exists(), reason="imported_duties absent")
def test_every_non_mvp_row_in_exactly_one_wave() -> None:
    duties = json.loads(_IMPORT.read_text())["duties"]
    doc = build_wave_plan(duties)

    non_mvp_ids = {
        d["duty_id"]
        for d in duties
        if (d.get("cluster") or "") not in TARGET_CLUSTERS and d.get("cluster")
    }
    assigned = [r for w in doc["waves"] for rows in w["clusters"].values() for r in rows]

    assert len(assigned) == len(set(assigned))  # no row in two waves
    assert set(assigned) == non_mvp_ids  # exactly the non-MVP rows
    assert doc["counts"]["non_mvp_rows_assigned"] == doc["counts"]["non_mvp_rows_total"]
    assert 4 <= doc["counts"]["waves"] <= 7
    # no MVP cluster leaks into a wave
    wave_clusters = {c for w in doc["waves"] for c in w["clusters"]}
    assert wave_clusters.isdisjoint(TARGET_CLUSTERS)


def test_unassigned_cluster_is_a_hard_error() -> None:
    duties = [
        {"duty_id": "x:NEW-01", "cluster": "Some brand-new cluster nobody mapped"},
    ]
    with pytest.raises(ValueError, match="no wave assignment"):
        build_wave_plan(duties)
