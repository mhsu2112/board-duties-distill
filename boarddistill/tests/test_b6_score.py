"""B6-T5 — scoring metrics (pairwise P/R/F1, ARI) + artifact."""

from __future__ import annotations

import json
from pathlib import Path

from adapters.b6_score import adjusted_rand, pairwise_prf

_SCORES = Path(__file__).resolve().parents[1] / "outputs" / "b6" / "scores.json"


def test_pairwise_perfect_agreement() -> None:
    true = {"a": "X", "b": "X", "c": "Y", "d": "Y"}
    pred = {"a": "1", "b": "1", "c": "2", "d": "2"}  # same partition, different labels
    m = pairwise_prf(true, pred)
    assert m == {"precision": 1.0, "recall": 1.0, "f1": 1.0}
    assert adjusted_rand(true, pred) == 1.0


def test_pairwise_over_split_high_precision_low_recall() -> None:
    # truth: one cluster of 4; pred splits it into two pairs → precision 1, recall < 1
    true = {"a": "X", "b": "X", "c": "X", "d": "X"}
    pred = {"a": "1", "b": "1", "c": "2", "d": "2"}
    m = pairwise_prf(true, pred)
    assert m["precision"] == 1.0
    assert m["recall"] < 1.0  # some same-cluster pairs split apart


def test_pairwise_random_partition_low_ari() -> None:
    true = {"a": "X", "b": "X", "c": "Y", "d": "Y"}
    pred = {"a": "1", "b": "2", "c": "1", "d": "2"}  # orthogonal split
    assert adjusted_rand(true, pred) <= 0.0


def test_scores_artifact_has_engine_baseline_delta_and_opmix() -> None:
    if not _SCORES.exists():
        return
    s = json.loads(_SCORES.read_text())
    assert 0.0 <= s["engine"]["grouping"]["pairwise"]["f1"] <= 1.0
    assert "f1" in s["engine_minus_baseline"] and "ari" in s["engine_minus_baseline"]
    # op-mix concentrates in the PRD-predicted primitives
    assert s["engine"]["operation_mix"]["primary_share"] >= 0.5
    # disagreements are characterized (purity per group), not reconciled
    assert all("purity" in r for r in s["disagreements"])
