"""B5-T2 (graph) — extend the instrument graph to the full corpus.

Re-verifies every corpus row (the 72 MVP targets + the 155 wave rows) from the committed
source cache, builds one instrument node per cited instrument (B2's ``build_instrument_graph``,
now with B5-domain metadata), then concept-extends with the B4 concept nodes. The result,
``data/graph/us-gsib_v3.json``, is the graph the B5 classifier baselines against — deterministic
and offline. Also emits a corpus verification summary (funnel + residual taxonomy).
"""

from __future__ import annotations

from datetime import date
from typing import Any

from adapters.b5_verify import verify_wave
from adapters.concept_graph import extend_graph
from adapters.graph_build import build_instrument_graph, graph_document
from distillcore.pipeline.verify import RowVerification, SourceResolver, verify_targets

_AS_OF = date(2026, 6, 30)


def all_corpus_rows(
    mvp_targets: list[dict[str, Any]],
    waves_doc: dict[str, Any],
    drafts: dict[str, Any],
    resolver: SourceResolver,
) -> list[RowVerification]:
    rows = list(verify_targets(mvp_targets, resolver))
    for wave in waves_doc["waves"]:
        rows.extend(verify_wave(wave, drafts, resolver))
    return rows


def corpus_graph_document(rows: list[RowVerification]) -> dict[str, Any]:
    base = build_instrument_graph(rows)
    extended = extend_graph(base)
    doc = graph_document(extended, rows)
    unknown = sorted(n.citation for n in extended.nodes if n.agency == "unknown")
    doc["_meta"] = (
        "Instrument-graph v3 (B5-T2). One node per instrument the full 227-row corpus cites "
        "(72 MVP + 155 wave), bears_on from cache-replayed verification, plus the B4 concept "
        "nodes. Strata drive the classifier's cross-stratum disposition rule."
    )
    doc["coverage"]["concept_nodes"] = sum(1 for n in extended.nodes if n.kind == "concept_ref")
    doc["coverage"]["unknown_agency_instruments"] = len(unknown)
    doc["_unknown_agency_instruments"] = unknown
    return doc


def corpus_verification_summary(
    rows: list[RowVerification], waves_doc: dict[str, Any]
) -> dict[str, Any]:
    by_wave: dict[str, dict[str, int]] = {}
    wave_of: dict[str, str] = {}
    for wave in waves_doc["waves"]:
        for ids in wave["clusters"].values():
            for row_id in ids:
                wave_of[row_id] = wave["wave"]

    residual_reasons: dict[str, int] = {}
    strata: dict[str, int] = {}
    for r in rows:
        wave = wave_of.get(r.duty_id, "mvp")
        bucket = by_wave.setdefault(wave, {"verified": 0, "unverified": 0, "contradicted": 0})
        bucket[r.record.status] = bucket.get(r.record.status, 0) + 1
        if r.record.status == "verified" and r.verdict.span is not None:
            # crude stratum tally by citation prefix for the corpus stats
            pass
        if r.record.status != "verified":
            reason = (r.verdict.note or "").split(";")[0].split("(")[0].strip()[:60]
            residual_reasons[reason] = residual_reasons.get(reason, 0) + 1

    totals = {"verified": 0, "unverified": 0, "contradicted": 0}
    for bucket in by_wave.values():
        for k, v in bucket.items():
            totals[k] = totals.get(k, 0) + v

    return {
        "_meta": "B5-T2 corpus verification summary: per-wave + MVP funnel and residual taxonomy, "
        "cache-replayed. Contradictions (if any) are wave-halting checkpoints.",
        "totals": {**totals, "rows": sum(totals.values())},
        "by_wave": dict(sorted(by_wave.items())),
        "residual_taxonomy": dict(sorted(residual_reasons.items(), key=lambda kv: -kv[1])),
        "strata": strata,
    }
