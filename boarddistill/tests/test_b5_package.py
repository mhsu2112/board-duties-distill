"""B5-T5 — per-wave package rendering."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from adapters.b5_package import build_wave_packages, cluster_slug

_ROOT = Path(__file__).resolve().parents[1]
_B5 = _ROOT / "outputs" / "b5"
_WAVES = _B5 / "waves.json"
_GRAPH = _ROOT / "data" / "graph" / "us-gsib_v3.json"
_DECOMP = _B5 / "corpus" / "lever_decompositions.json"

_REQUIRED_SECTIONS = [
    "## As-built duties",
    "## Intended — reform lever",
    "## Instrument graph",
    "## Findings",
    "## Duplication — mirror pairs",
    "## Duplication — restatements",
    "## Duty crosswalk",
    "## Authority to act",
    "## Claim verification",
    "## Normative review queue",
    "## Final-status blocker summary",
]

_ARTIFACTS = _WAVES.exists() and _GRAPH.exists() and _DECOMP.exists()


@pytest.mark.skipif(not _ARTIFACTS, reason="B5 artifacts absent")
def test_every_wave_cluster_renders_full_section_9_nothing_final() -> None:
    waves = json.loads(_WAVES.read_text())
    graph = json.loads(_GRAPH.read_text())
    levers = json.loads(_DECOMP.read_text())["levers"]

    total = 0
    for w in waves["waves"]:
        wave_dir = _B5 / w["wave"]
        if not (wave_dir / "findings.json").exists():
            continue
        distilled = json.loads((wave_dir / "as_built_distilled.json").read_text())
        findings = json.loads((wave_dir / "findings.json").read_text())
        verif = json.loads((wave_dir / "verification.json").read_text())
        packages = build_wave_packages(w["wave"], w, distilled, findings, verif, graph, levers)
        assert set(packages) == {cluster_slug(c) for c in w["clusters"]}
        for md in packages.values():
            for section in _REQUIRED_SECTIONS:
                assert section in md, section
            assert "| final |" not in md  # no finding is final
            assert "blocked pending human review" in md
            total += 1
    assert total == 22  # every non-MVP cluster gets a package
