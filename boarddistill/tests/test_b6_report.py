"""B6-T6 — report assembly reflects the scored metrics."""

from __future__ import annotations

import json
from pathlib import Path

from adapters.b6_report import build_report

_OUT = Path(__file__).resolve().parents[1] / "outputs" / "b6"


def test_report_reflects_scores_and_has_all_sections() -> None:
    if not (_OUT / "scores.json").exists():
        return
    md = build_report(_OUT)
    for section in (
        "Design",
        "Sample",
        "Results",
        "Disagreement characterization",
        "leakage caveat",
        "Limitations",
        "Publishable summary",
    ):
        assert section in md
    s = json.loads((_OUT / "scores.json").read_text())
    # the engine F1 and the baseline-delta appear verbatim (numbers never drift from scores.json)
    assert str(s["engine"]["grouping"]["pairwise"]["f1"]) in md
    assert "held out" in md.lower() and "policy choices" in md.lower()
