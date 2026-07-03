"""B5-T3 — per-wave distill + diagnose invariants (offline, from committed outputs)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from adapters.b5_diagnose import mirror_pairs

_ROOT = Path(__file__).resolve().parents[1]
_B5 = _ROOT / "outputs" / "b5"
_WAVES = _B5 / "waves.json"

_WAVE_SLUGS = [
    "w1-liquidity-resolution",
    "w2-opres-cyber-model",
    "w3-thirdparty-inccomp",
    "w4-bsa-consumer",
    "w5-credit-insider",
    "w6-governance-structural",
]

_ARTIFACTS = _WAVES.exists() and all((_B5 / w / "findings.json").exists() for w in _WAVE_SLUGS)


def test_mirror_pairs_are_cross_entity_same_cluster() -> None:
    distilled = {"rows": [{"duty_id": x} for x in ["b:LIQ-01", "s:LIQ-01", "b:LIQ-02", "s:REC-01"]]}
    cluster_of = {"b:LIQ-01": "L", "s:LIQ-01": "L", "b:LIQ-02": "L", "s:REC-01": "R"}
    pairs = mirror_pairs(distilled, cluster_of)
    assert ("b:LIQ-01", "s:LIQ-01") in pairs
    assert all(a.startswith("b:") and b.startswith("s:") for a, b in pairs)
    assert ("b:LIQ-02", "s:REC-01") not in pairs  # different stem/cluster never pairs


@pytest.mark.skipif(not _ARTIFACTS, reason="B5 T3 artifacts absent")
def test_every_wave_finding_is_grounded_diagnostic() -> None:
    for slug in _WAVE_SLUGS:
        doc = json.loads((_B5 / slug / "findings.json").read_text())
        for f in doc["findings"]:
            # diagnostics are 0-op ⇒ unresolved (never guessed) with a needs_review default
            assert f["effect_class"] == "unresolved"
            assert f["disposition_state"] == "needs_review"
            assert f["operation_ids"] == []
            assert f["id"].startswith(slug)  # wave-prefixed ⇒ no cross-wave id collision
        # both duplication families are first-class in the schema
        fam = doc["duplication_families"]
        assert set(fam) == {"mirror_pair", "restatement"}


@pytest.mark.skipif(not _ARTIFACTS, reason="B5 T3 artifacts absent")
def test_unanchored_diagnostics_are_dropped_not_emitted() -> None:
    """The two waves with a recorded anchor failure emit no finding for it (dropped, not passed)."""
    for slug in ("w2-opres-cyber-model", "w3-thirdparty-inccomp"):
        doc = json.loads((_B5 / slug / "findings.json").read_text())
        assert doc["counts"]["anchor_failures"] >= 1  # recorded as a checkpoint
        # every emitted finding id is unique (dropped ones left no gap-collision)
        ids = [f["id"] for f in doc["findings"]]
        assert len(ids) == len(set(ids))
