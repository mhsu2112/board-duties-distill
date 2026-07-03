"""B5-T3 — per-wave diagnostics + classification.

Runs the proven LLM diagnostic pass (``diagnose_cluster``) over each wave cluster's distilled
corpus — the same four kinds (duplicate_duty→restatement, rule_guidance_restatement,
undefined_term, actor_ambiguity), each span-anchored — and adds deterministic ``mirror_pair``
diagnostics for cross-entity BHC↔IDI parallels (``b:XXX-NN`` ↔ ``s:XXX-NN``, same cluster).
Every diagnostic is 0-op, so the mechanical classifier resolves it to ``unresolved`` (never
guessed) with a ``needs_review`` default. Consolidation findings (with real effect classes)
come from the B5-T4 lever decomposition, not here.

Finding ids are wave-prefixed so the corpus roll-up can merge every wave without collision.
"""

from __future__ import annotations

from typing import Any

from adapters.diagnose import (
    MIRROR_PAIR,
    _cluster_duties,
    diagnose_cluster,
    diagnostic_anchor_ok,
    diagnostic_finding,
    duplication_family,
    official_kind,
)
from distillcore.llm import LlmHarness
from profiles.lex_balanus.models import BankingFinding


def wave_cluster_of(wave_doc: dict[str, Any]) -> dict[str, str]:
    return {rid: cluster for cluster, ids in wave_doc["clusters"].items() for rid in ids}


def wave_excerpts(verif: dict[str, Any]) -> dict[str, str]:
    records = {r["claim_id"]: r for r in verif["records"]}
    spans = {s["id"]: s for s in verif["spans"]}
    out: dict[str, str] = {}
    for row in verif["rows"]:
        if row["status"] != "verified":
            continue
        rec = records.get(f"claim-{row['duty_id']}")
        if rec and rec["checked_span_ids"]:
            span = spans.get(rec["checked_span_ids"][0])
            if span:
                out[row["duty_id"]] = span["quote"]
    return out


def mirror_pairs(
    distilled_doc: dict[str, Any], cluster_of: dict[str, str]
) -> list[tuple[str, str]]:
    """Cross-entity BHC↔IDI pairs: same stem after the ``b:``/``s:`` prefix, same cluster,
    both distilled. Deterministic, sorted by stem."""
    stems: dict[str, dict[str, str]] = {}
    for row in distilled_doc["rows"]:
        did = row["duty_id"]
        if ":" not in did:
            continue
        prefix, stem = did.split(":", 1)
        stems.setdefault(stem, {})[prefix] = did
    pairs: list[tuple[str, str]] = []
    for stem in sorted(stems):
        by_prefix = stems[stem]
        if "b" in by_prefix and "s" in by_prefix:
            a, b = by_prefix["b"], by_prefix["s"]
            if cluster_of.get(a) == cluster_of.get(b):
                pairs.append((a, b))
    return pairs


def _mirror_finding(wave: str, index: int, a: str, b: str) -> BankingFinding:
    return BankingFinding.model_validate(
        {
            "id": f"{wave}-dx-mp-{index}",
            "provision": f"{MIRROR_PAIR} :: {a}, {b}",
            "as_built_ref": a,
            "intended_ref": None,
            "operation_ids": [],
            "effect_class": "unresolved",
            "rationale": f"Cross-entity BHC↔IDI mirror pair: {a} ↔ {b}. Parallel obligation at "
            "two levels (RELATE_OBLIGATION / DEEM_SATISFIED-shaped); reform lever is "
            "vertical rationalization / reliance, not MERGE.",
            "baseline": None,
            "normative_kind": [],
            "disposition_state": "needs_review",
            "confidence": 0.5,
            "status": "draft",
        }
    )


def run_wave_diagnose(
    harness: LlmHarness,
    wave: str,
    wave_doc: dict[str, Any],
    distilled_doc: dict[str, Any],
    excerpts: dict[str, str],
) -> dict[str, Any]:
    cluster_of = wave_cluster_of(wave_doc)
    dd = {**distilled_doc, "_cluster_of": cluster_of}

    findings: list[BankingFinding] = []
    finding_cluster: dict[str, str] = {}
    finding_kind: dict[str, str] = {}
    anchor_failures: list[str] = []

    for cluster in sorted(wave_doc["clusters"]):
        duties = _cluster_duties(dd, cluster, excerpts)
        if not duties:
            continue
        ds, corpus = diagnose_cluster(harness, cluster, duties)
        for i, d in enumerate(ds.diagnostics):
            if not diagnostic_anchor_ok(d, corpus):
                # An unanchored diagnostic is the LLM over-reaching past the excerpt — a claim we
                # cannot ground. Drop it from the findings (zero unanchorable claims, B5-T3 DoD)
                # and record it as a checkpoint (the model asserted text not in the source).
                anchor_failures.append(f"{cluster}:{d.kind}:{d.evidence_quote[:60]!r}")
                continue
            df = diagnostic_finding(cluster, i, d, True)
            df = df.model_copy(update={"id": f"{wave}-{df.id}"})
            findings.append(df)
            finding_cluster[df.id] = cluster
            finding_kind[df.id] = official_kind(d.kind)

    for i, (a, b) in enumerate(mirror_pairs(distilled_doc, cluster_of)):
        mp = _mirror_finding(wave, i, a, b)
        findings.append(mp)
        finding_cluster[mp.id] = cluster_of.get(a, "")
        finding_kind[mp.id] = MIRROR_PAIR

    return diagnose_document(wave, findings, finding_cluster, finding_kind, anchor_failures)


def diagnose_document(
    wave: str,
    findings: list[BankingFinding],
    finding_cluster: dict[str, str],
    finding_kind: dict[str, str],
    anchor_failures: list[str],
) -> dict[str, Any]:
    mirror = sorted(fid for fid, k in finding_kind.items() if duplication_family(k) == MIRROR_PAIR)
    restate = sorted(
        fid for fid, k in finding_kind.items() if duplication_family(k) == "restatement"
    )
    effect_hist: dict[str, int] = {}
    for f in findings:
        effect_hist[f.effect_class] = effect_hist.get(f.effect_class, 0) + 1
    return {
        "_meta": f"B5-T3 diagnostics for wave {wave}. LLM diagnostics per cluster (span-anchored) "
        "+ deterministic cross-entity mirror pairs; every diagnostic 0-op ⇒ unresolved effect, "
        "needs_review default. Consolidation findings come from the B5-T4 lever decomposition.",
        "wave": wave,
        "counts": {
            "diagnostic_findings": len(findings),
            "anchor_failures": len(anchor_failures),
            "in_review": sum(1 for f in findings if f.disposition_state == "needs_review"),
            "effect_classes": dict(sorted(effect_hist.items())),
        },
        "anchor_failures": anchor_failures,
        "duplication_families": {
            "mirror_pair": {"count": len(mirror), "finding_ids": mirror},
            "restatement": {"count": len(restate), "finding_ids": restate},
        },
        "finding_cluster": finding_cluster,
        "finding_kind": finding_kind,
        "findings": [f.model_dump(mode="json") for f in findings],
    }
