"""B1-T0 — deterministic selection of the 72 MVP-cluster target rows."""

from __future__ import annotations

from pathlib import Path

import pytest

from adapters.b1_targets import TARGET_CLUSTERS, build_targets, select_targets
from adapters.inventory_xlsx import import_inventory

_XLSX = (
    Path(__file__).resolve().parents[2]
    / "Synthesis"
    / "gsib-board_duties-combined_inventory.xlsx"
)

pytestmark = pytest.mark.skipif(not _XLSX.exists(), reason="inventory xlsx not present")


def _import_doc() -> dict[str, object]:
    result = import_inventory(_XLSX)
    return {"duties": [d.model_dump(mode="json") for d in result.duties]}


def test_selects_seventy_two_rows_in_target_clusters() -> None:
    targets = select_targets(_import_doc()["duties"])  # type: ignore[arg-type]
    assert len(targets) == 72
    assert {t["cluster"] for t in targets} == set(TARGET_CLUSTERS)


def test_selection_is_stable_and_sorted() -> None:
    doc = _import_doc()
    first = select_targets(doc["duties"])  # type: ignore[arg-type]
    second = select_targets(doc["duties"])  # type: ignore[arg-type]
    ids = [t["duty_id"] for t in first]
    assert ids == sorted(ids)
    assert [t["duty_id"] for t in second] == ids


def test_build_targets_document(tmp_path: Path) -> None:
    import json

    import_path = tmp_path / "imported_duties.json"
    import_path.write_text(json.dumps(_import_doc()))
    doc = build_targets(import_path)
    assert doc["count"] == 72
    assert len(doc["duty_ids"]) == 72
    assert doc["clusters"] == sorted(TARGET_CLUSTERS)
    # every emitted target still carries its (unverified) claim — nothing is finalized here
    for target in doc["targets"]:
        assert target["claims"]
        assert all(c["verifier_status"] == "unverified" for c in target["claims"])
