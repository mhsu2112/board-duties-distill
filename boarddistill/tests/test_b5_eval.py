"""B5-T7 — corpus eval: citation-integrity gate + funnel + closure."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from adapters.b5_eval import closure_result, corpus_funnel

_ROOT = Path(__file__).resolve().parents[1]
_B5 = _ROOT / "outputs" / "b5"
_EVAL = _B5 / "eval.json"
_DECOMP = _B5 / "corpus" / "lever_decompositions.json"


def test_corpus_funnel_counts() -> None:
    status = ["verified"] * 3 + ["unverified", "contradicted"]
    f = corpus_funnel(status, {"MVP": 2, "B5": 1}, {"MVP": 4})
    assert f["rows"] == 5
    assert f["verified"] == 3 and f["unverified"] == 1 and f["contradicted"] == 1
    assert f["distilled"] == 3 and f["classified_findings"] == 4


def test_closure_result_counts_residuals_as_checkpoints() -> None:
    doc = {
        "counts": {"levers": 3, "by_status": {"valid_single": 1, "residual": 2}},
        "residual_checkpoints": [{"lever_id": "A"}, {"lever_id": "B"}],
    }
    r = closure_result(doc)
    assert r["clean"] == 1 and r["residuals"] == 2
    assert not r["sixteen_primitive_set_held_trivially"]


@pytest.mark.skipif(not _EVAL.exists(), reason="B5-T7 artifact absent")
def test_citation_integrity_gate_holds_zero() -> None:
    doc = json.loads(_EVAL.read_text())
    integ = doc["integrity"]
    assert integ["hallucinated_citation_rate"] == 0.0
    assert integ["release_gate"] == "PASS"
    assert integ["emitted_unanchored_claims"] == 0
    # the funnel shows no contradiction survived and the closure result is present
    assert doc["funnel"]["contradicted"] == 0
    assert doc["closure"]["clean"] + doc["closure"]["residuals"] > 0


@pytest.mark.skipif(not (_EVAL.exists() and _DECOMP.exists()), reason="artifacts absent")
def test_report_and_eval_consistent_with_decomposition() -> None:
    ev = json.loads(_EVAL.read_text())
    dec = json.loads(_DECOMP.read_text())
    assert ev["closure"]["residuals"] == dec["counts"]["residuals"]
    assert (_B5 / "B5_report.md").exists()
