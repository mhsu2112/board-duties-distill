"""B6-T5 — scoring (structural only; dials held out).

The SINGLE place the sealed answer key is read (via ``benchmark_guard.unseal_read``). Computes,
for both the engine and the plain-LLM baseline, the §1.4 structural metrics against RBI's
circular→MD grouping: pairwise precision / recall / F1 and the Adjusted Rand Index over the pooled
corpus. Also the operation-mix check (engine PRD §18 prediction) and a characterized disagreement
table. RBI's substantive policy choices are never scored (held-out dials).
"""

from __future__ import annotations

import json
from collections import Counter
from math import comb
from pathlib import Path
from typing import Any

from adapters.benchmark_guard import ANSWER_KEY_DIR, PSEUDONYM_DIR, unseal_read

_PRED_OPS_PRIMARY = frozenset(
    {"MERGE", "REPEAL", "CANONICALIZE_DEFINITION", "RESOLVE_CROSS_REFERENCE"}
)


def _doc_to_md() -> dict[str, str]:
    """doc_id (pseudonym) → md_id, by composing the sealed pseudonym map with the answer key."""
    key = json.loads(unseal_read(ANSWER_KEY_DIR / "grouping.json"))
    pmap = json.loads(unseal_read(PSEUDONYM_DIR / "map.json"))
    real_of_doc = {doc: real for real, doc in pmap["doc_id"].items()}
    grouping = key["grouping"]  # real_cid → md_id
    return {doc: grouping[real] for doc, real in real_of_doc.items() if real in grouping}


def _doc_to_group(proposal: dict[str, Any]) -> dict[str, str]:
    return {d: g["group_id"] for g in proposal["groups"] for d in g["doc_ids"]}


def pairwise_prf(true: dict[str, str], pred: dict[str, str]) -> dict[str, float]:
    ids = sorted(set(true) & set(pred))
    tp = fp = fn = 0
    for i in range(len(ids)):
        ti, pi = true[ids[i]], pred[ids[i]]
        for j in range(i + 1, len(ids)):
            same_true = ti == true[ids[j]]
            same_pred = pi == pred[ids[j]]
            if same_pred and same_true:
                tp += 1
            elif same_pred:
                fp += 1
            elif same_true:
                fn += 1
    prec = tp / (tp + fp) if tp + fp else 0.0
    rec = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * prec * rec / (prec + rec) if prec + rec else 0.0
    return {"precision": round(prec, 3), "recall": round(rec, 3), "f1": round(f1, 3)}


def adjusted_rand(true: dict[str, str], pred: dict[str, str]) -> float:
    ids = sorted(set(true) & set(pred))
    n = len(ids)
    if n < 2:
        return 1.0
    ct = Counter((true[i], pred[i]) for i in ids)
    a = Counter(true[i] for i in ids)
    b = Counter(pred[i] for i in ids)
    sum_c = sum(comb(v, 2) for v in ct.values())
    sum_a = sum(comb(v, 2) for v in a.values())
    sum_b = sum(comb(v, 2) for v in b.values())
    expected = sum_a * sum_b / comb(n, 2)
    max_index = (sum_a + sum_b) / 2
    return round((sum_c - expected) / (max_index - expected), 3) if max_index != expected else 1.0


def score_grouping(true: dict[str, str], proposal: dict[str, Any]) -> dict[str, Any]:
    pred = _doc_to_group(proposal)
    return {
        "pairwise": pairwise_prf(true, pred),
        "adjusted_rand_index": adjusted_rand(true, pred),
        "n_groups": len({g["group_id"] for g in proposal["groups"]}),
    }


def operation_mix(engine: dict[str, Any]) -> dict[str, Any]:
    mix = Counter(op["primitive"] for g in engine["groups"] for op in g["operations"])
    total = sum(mix.values())
    primary = sum(v for k, v in mix.items() if k in _PRED_OPS_PRIMARY)
    return {
        "total_operations": total,
        "by_primitive": dict(sorted(mix.items())),
        "primary_share": round(primary / total, 3) if total else 0.0,
        "prd_prediction": "concentrates in {MERGE, REPEAL, CANONICALIZE_DEFINITION, "
        "RESOLVE_CROSS_REFERENCE} (§18)",
    }


def survival_repeal(true: dict[str, str], engine: dict[str, Any]) -> dict[str, Any]:
    """All consolidated circulars are formally repealed in the appendices, so the 'repealed set' is
    the whole corpus — repeal *precision* is trivially high. The informative signal (which
    within-group circular survives as the home) is not distinguished by RBI's flat appendix, so
    recall is over the whole corpus and characterized, not over-claimed."""
    repealed_pred = {
        d
        for g in engine["groups"]
        for op in g["operations"]
        if op["primitive"] == "REPEAL"
        for d in op["doc_ids"]
        if d in true
    }
    return {
        "repealed_predicted": len(repealed_pred),
        "corpus_all_repealed": len(true),
        "precision_vs_appendix": 1.0 if repealed_pred else 0.0,
        "recall_over_corpus": round(len(repealed_pred) / len(true), 3) if true else 0.0,
        "note": "every consolidated circular is formally repealed ⇒ precision trivially 1.0; "
        "within-group survivor is not in RBI's flat appendix (characterized, not scored).",
    }


def disagreements(true: dict[str, str], engine: dict[str, Any]) -> list[dict[str, Any]]:
    """Per engine group: the MD(s) its docs map to. A pure group agrees; a group spanning MDs,
    or an MD split across groups, is a characterized disagreement (some are cleaner splits)."""
    rows: list[dict[str, Any]] = []
    for g in engine["groups"]:
        mds = Counter(true[d] for d in g["doc_ids"] if d in true)
        if not mds:
            continue
        dominant, dom_n = mds.most_common(1)[0]
        purity = dom_n / sum(mds.values())
        rows.append(
            {
                "group_id": g["group_id"],
                "theme": g["theme"],
                "size": len(g["doc_ids"]),
                "md_distribution": dict(mds),
                "dominant_md": dominant,
                "purity": round(purity, 2),
                "kind": "pure" if purity == 1.0 else "mixed",
            }
        )
    return sorted(rows, key=lambda r: -r["size"])


def write_scores(root: Path, out: Path) -> dict[str, Any]:
    true = _doc_to_md()
    engine = json.loads((out / "engine_proposals.json").read_text())
    baseline = json.loads((out / "baseline_proposals.json").read_text())

    eng_group = score_grouping(true, engine)
    base_group = score_grouping(true, baseline)
    delta = {
        "f1": round(eng_group["pairwise"]["f1"] - base_group["pairwise"]["f1"], 3),
        "ari": round(eng_group["adjusted_rand_index"] - base_group["adjusted_rand_index"], 3),
    }
    # md splitting: how many engine groups each true MD is spread across
    doc_group = _doc_to_group(engine)
    md_groups: dict[str, set[str]] = {}
    for d, md in true.items():
        if d in doc_group:
            md_groups.setdefault(md, set()).add(doc_group[d])
    md_spread = {md: len(gs) for md, gs in sorted(md_groups.items())}

    scores = {
        "_meta": "B6-T5 structural scoring. Answer key unsealed here only (scorer). Metrics: "
        "pairwise P/R/F1 + Adjusted Rand Index of the proposed grouping vs RBI's circular→MD "
        "assignment; operation-mix; baseline delta. RBI's policy choices are never scored.",
        "corpus": {"scored_circulars": len(true), "true_mds": len(set(true.values()))},
        "engine": {
            "grouping": eng_group,
            "operation_mix": operation_mix(engine),
            "survival_repeal": survival_repeal(true, engine),
        },
        "baseline": {"grouping": base_group},
        "engine_minus_baseline": delta,
        "md_spread_engine": md_spread,
        "disagreements": disagreements(true, engine),
    }
    out.mkdir(parents=True, exist_ok=True)
    (out / "scores.json").write_text(json.dumps(scores, indent=2, sort_keys=True) + "\n")
    return scores
