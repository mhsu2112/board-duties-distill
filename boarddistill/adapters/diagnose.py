"""B3-T4 — diagnose + classify.

Two finding sources, both classified by the **mechanical** classifier (``classify_finding`` /
``compute_disposition``) after any LLM proposal — the LLM never sets an effect class:

1. **Consolidation findings** — one per B0 decomposition (from the B3-T3 intended layer).
   ``effect_class`` and baseline come from ``classify_finding`` (baseline_for diffs + the
   per-se force-conversion rule + no-baseline ⇒ unresolved). Normative kinds are carried
   from B0 (proposals, not resolved). Disposition defaults per ``compute_disposition``.

2. **LLM diagnostics** — per MVP cluster, over the distilled as-built corpus: duplicate duty,
   rule-guidance restatement, undefined term, actor ambiguity. Each carries a span-anchored
   evidence quote (verified against the cluster's excerpts) and a *proposed* normative kind;
   effect is still classified in code (0-op diagnostics resolve to ``unresolved``).

Divergence vs. the hand-labelled duplicates (the B0 RELATE_OBLIGATION / DEEM_SATISFIED
operand pairs) is recorded both directions — LLM-only and B0-only pairs are each findings.
Nothing is finalized.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date
from typing import Any

from adapters.intended import operation_refs, scaffold_operations
from distillcore.llm import LlmHarness, load_template, render
from distillcore.models.base import StrictModel
from distillcore.pipeline.classify import (
    FORCE_MOVING_PRIMITIVES,
    classify_finding,
    compute_disposition,
    is_force_conversion,
)
from profiles.lex_balanus.enums import NormativeKind
from profiles.lex_balanus.models import (
    BankingFinding,
    BankingOperation,
    DutySpec,
    InstrumentGraph,
)

AS_OF = date(2026, 6, 30)

MVP_CLUSTERS = (
    "Risk-governance framework / strategy",
    "Audit committee & independence",
    "Capital planning & stress testing",
)

_NORMATIVE_VALUES = frozenset(m.value for m in NormativeKind)

# --- diagnostic-kind vocabulary (B4-T3) ------------------------------------------------
#
# The B3 duplicate diagnostic splits into two first-class, non-overlapping families
# (REVIEW_PACKET_B3 Part 4, accepted):
#   * ``mirror_pair`` — cross-layer / cross-entity parallel obligations (BHC↔IDI, rule↔
#     guideline), RELATE_OBLIGATION / DEEM_SATISFIED-shaped. These are B0's hand-labelled
#     mirror pairs; the reform lever is DEEM_SATISFIED / reliance.
#   * ``restatement`` — the same text repeated across rows, MERGE / RESOLVE_CROSS_REFERENCE-
#     shaped. These are the LLM's within-cluster duplicates (``duplicate_duty``, re-keyed) plus
#     the rule↔guidance restatements (``rule_guidance_restatement``).
MIRROR_PAIR = "mirror_pair"
RESTATEMENT = "restatement"
RULE_GUIDANCE_RESTATEMENT = "rule_guidance_restatement"
UNDEFINED_TERM = "undefined_term"
ACTOR_AMBIGUITY = "actor_ambiguity"

OFFICIAL_DIAGNOSTIC_KINDS: frozenset[str] = frozenset(
    {MIRROR_PAIR, RESTATEMENT, RULE_GUIDANCE_RESTATEMENT, UNDEFINED_TERM, ACTOR_AMBIGUITY}
)

# The LLM's ``duplicate_duty`` is re-keyed to ``restatement`` (its within-cluster duplicates
# are same-text repetitions, distinct from B0's parallel-obligation mirror pairs).
_KIND_REMAP: dict[str, str] = {"duplicate_duty": RESTATEMENT}


def official_kind(kind: str) -> str:
    """Map a raw (possibly LLM-emitted) diagnostic kind to its official B4 kind."""
    return _KIND_REMAP.get(kind, kind)


def duplication_family(kind: str) -> str | None:
    """The duplication family a kind belongs to (``mirror_pair`` / ``restatement``), else None."""
    canon = official_kind(kind)
    if canon == MIRROR_PAIR:
        return MIRROR_PAIR
    if canon in {RESTATEMENT, RULE_GUIDANCE_RESTATEMENT}:
        return RESTATEMENT
    return None


# --- loaders ---------------------------------------------------------------------------


def as_built_map(drafts: dict[str, Any]) -> dict[str, DutySpec]:
    return {duty_id: DutySpec.model_validate(d) for duty_id, d in drafts.items()}


def intended_map(intended_doc: dict[str, Any]) -> dict[str, DutySpec]:
    return {
        d["intended_spec"]["duty_id"]: DutySpec.model_validate(d["intended_spec"])
        for d in intended_doc["decompositions"]
    }


def load_graph(graph_doc: dict[str, Any]) -> InstrumentGraph:
    return InstrumentGraph.model_validate(graph_doc["graph"])


# --- consolidation findings ------------------------------------------------------------


@dataclass
class _FindingStub:
    """Minimal FindingLike for the classifier (reads refs/ops/normative_kind only)."""

    id: str
    as_built_ref: str | None
    intended_ref: str | None
    operation_ids: list[str]
    normative_kind: list[Any]
    force_conversion_declared: bool = False


def _decomp_normative_kinds(dec: dict[str, Any]) -> list[str]:
    kinds: list[str] = []
    for op in dec.get("operations", []):
        for k in op.get("normative_kind", []) or []:
            if k in _NORMATIVE_VALUES and k not in kinds:
                kinds.append(k)
    return kinds


def _first_resolved(ops: list[BankingOperation], as_built: dict[str, DutySpec]) -> str | None:
    # Consider operands and the DEEM refs — a DEEM finding's as-built target is the duty
    # being deemed satisfied (its satisfied_ref), not an operand it lacks.
    for op in ops:
        for ref in operation_refs(op):
            if ref in as_built:
                return ref
    return None


def _force_conversion(
    ops: list[BankingOperation], as_built: dict[str, DutySpec], output_force: Any
) -> bool:
    if output_force is None:
        return False
    for op in ops:
        if str(op.primitive) not in FORCE_MOVING_PRIMITIVES:
            continue
        forces = [as_built[o].legal_force for o in op.operands if o in as_built]
        if is_force_conversion(forces, output_force):
            return True
    return False


def consolidation_finding(
    dec: dict[str, Any],
    ops: list[BankingOperation],
    as_built: dict[str, DutySpec],
    intended: dict[str, DutySpec],
    graph: InstrumentGraph,
) -> BankingFinding:
    intended_ref = f"i:{dec['id']}"
    nk = _decomp_normative_kinds(dec)
    stub = _FindingStub(
        id=f"f-{dec['id']}",
        as_built_ref=_first_resolved(ops, as_built),
        intended_ref=intended_ref if intended_ref in intended else None,
        operation_ids=[op.id for op in ops],
        normative_kind=nk,
    )
    effect, baseline = classify_finding(stub, ops, as_built, intended, graph, AS_OF)

    output_force = intended[intended_ref].legal_force if intended_ref in intended else None
    fc = _force_conversion(ops, as_built, output_force)
    forces = {as_built[o].legal_force for op in ops for o in op.operands if o in as_built}
    cross_stratum = len(forces) > 1
    deem_floor = any(
        str(op.primitive) == "DEEM_SATISFIED"
        and op.satisfied_ref in as_built
        and str(as_built[op.satisfied_ref].legal_force) == "statute"
        for op in ops
    )
    disposition = compute_disposition(
        effect=effect,
        primitives=[str(op.primitive) for op in ops],
        normative_kind=nk,
        cross_stratum=cross_stratum,
        force_conversion=fc,
        deem_against_floor=deem_floor,
    )
    return BankingFinding.model_validate(
        {
            "id": stub.id,
            "provision": str(dec.get("lever", "")),
            "as_built_ref": stub.as_built_ref,
            "intended_ref": stub.intended_ref,
            "operation_ids": stub.operation_ids,
            "effect_class": effect,
            "rationale": f"Consolidation lever {dec['id']} ({dec.get('cluster', '')}).",
            "baseline": baseline.model_dump(mode="json") if baseline is not None else None,
            "normative_kind": nk,
            "disposition_state": disposition,
            "force_conversion_declared": fc,
            "confidence": 0.5,
            "status": "draft",
        }
    )


# --- LLM diagnostics -------------------------------------------------------------------


class Diagnostic(StrictModel):
    kind: str  # duplicate_duty | rule_guidance_restatement | undefined_term | actor_ambiguity
    target_ids: list[str]
    evidence_quote: str
    normative_kind: list[NormativeKind] = []  # noqa: RUF012 (proposal, not resolved)
    rationale: str


class DiagnosticSet(StrictModel):
    cluster: str
    diagnostics: list[Diagnostic] = []  # noqa: RUF012


def _despace(s: str) -> str:
    return re.sub(r"\s+", "", s)


def diagnostic_anchor_ok(d: Diagnostic, corpus: str) -> bool:
    return bool(d.evidence_quote) and _despace(d.evidence_quote) in _despace(corpus)


def _cluster_duties(
    distilled_doc: dict[str, Any], cluster: str, excerpts: dict[str, str]
) -> list[dict[str, Any]]:
    out = []
    for row in distilled_doc["rows"]:
        did = row["duty_id"]
        if excerpts.get(did, "") and _duty_cluster(did, distilled_doc) == cluster:
            dd = row["distilled"]
            out.append(
                {
                    "duty_id": did,
                    "verb": dd["verb_standard"],
                    "object": dd["object"],
                    "excerpt": excerpts[did],
                }
            )
    return out


def _duty_cluster(duty_id: str, distilled_doc: dict[str, Any]) -> str:
    return str(distilled_doc.get("_cluster_of", {}).get(duty_id, ""))


def diagnose_cluster(
    harness: LlmHarness, cluster: str, duties: list[dict[str, Any]]
) -> tuple[DiagnosticSet, str]:
    corpus = "\n\n".join(
        f"{d['duty_id']} · {d['verb']} · {d['object']}\n{d['excerpt']}" for d in duties
    )
    duties_block = "\n\n".join(
        f"{d['duty_id']} · {d['verb']} · {d['object']}\n<<<\n{d['excerpt']}\n>>>" for d in duties
    )
    prompt = render(
        load_template("diagnose"),
        {
            "cluster": cluster,
            "normative_kinds": ", ".join(m.value for m in NormativeKind),
            "duties": duties_block,
        },
    )
    return harness.complete(prompt, DiagnosticSet), corpus


def diagnostic_finding(cluster: str, index: int, d: Diagnostic, anchor_ok: bool) -> BankingFinding:
    nk = [k.value for k in d.normative_kind]
    kind = official_kind(d.kind)  # duplicate_duty -> restatement (B4-T3)
    # 0-operation diagnostic: no baseline diff to run ⇒ unresolved (never guessed).
    return BankingFinding.model_validate(
        {
            "id": f"dx-{cluster[:3].lower()}-{index}",
            "provision": f"{kind} :: {', '.join(d.target_ids)}",
            "as_built_ref": d.target_ids[0] if d.target_ids else None,
            "intended_ref": None,
            "operation_ids": [],
            "effect_class": "unresolved",
            "rationale": d.rationale,
            "baseline": None,
            "normative_kind": nk,
            # normative diagnostics start in review; disposition is not resolved here.
            "disposition_state": "needs_review",
            "confidence": 0.5,
            "status": "draft",
        }
    )


# --- duplicate divergence --------------------------------------------------------------


def b0_duplicate_pairs(
    decompositions: list[dict[str, Any]], inventory: set[str]
) -> set[frozenset[str]]:
    """Hand-labelled duplicate pairs = RELATE_OBLIGATION operand pairs + DEEM_SATISFIED
    satisfied/satisfying pairs, restricted to resolved inventory IDs."""
    pairs: set[frozenset[str]] = set()
    for dec in decompositions:
        for op in dec.get("operations", []):
            if op.get("primitive") == "RELATE_OBLIGATION":
                ids = [o for o in op.get("operands", []) if o in inventory]
                for i in range(len(ids)):
                    for j in range(i + 1, len(ids)):
                        pairs.add(frozenset({ids[i], ids[j]}))
            if op.get("primitive") == "DEEM_SATISFIED":
                a, b = op.get("satisfied_ref"), op.get("satisfying_ref")
                if a in inventory and b in inventory:
                    pairs.add(frozenset({a, b}))
    return pairs


def llm_duplicate_pairs(diag_sets: list[DiagnosticSet]) -> set[frozenset[str]]:
    pairs: set[frozenset[str]] = set()
    for ds in diag_sets:
        for d in ds.diagnostics:
            if d.kind == "duplicate_duty" and len(d.target_ids) >= 2:
                ids = sorted(set(d.target_ids))
                for i in range(len(ids)):
                    for j in range(i + 1, len(ids)):
                        pairs.add(frozenset({ids[i], ids[j]}))
    return pairs


def duplicate_divergence(
    decompositions: list[dict[str, Any]], diag_sets: list[DiagnosticSet], inventory: set[str]
) -> dict[str, Any]:
    b0 = b0_duplicate_pairs(decompositions, inventory)
    llm = llm_duplicate_pairs(diag_sets)
    return {
        "b0_only": sorted(sorted(p) for p in (b0 - llm)),
        "llm_only": sorted(sorted(p) for p in (llm - b0)),
        "agreed": sorted(sorted(p) for p in (b0 & llm)),
        "counts": {"b0_only": len(b0 - llm), "llm_only": len(llm - b0), "agreed": len(b0 & llm)},
    }


# --- mirror-pair diagnostics (B4-T3) ---------------------------------------------------


def mirror_pair_findings(
    divergence: dict[str, Any], cluster_of: dict[str, str]
) -> list[BankingFinding]:
    """Materialize the B0 cross-layer/cross-entity mirror pairs (the ``b0_only`` divergence)
    as first-class ``mirror_pair`` diagnostics. 0-op ⇒ unresolved (never guessed)."""
    findings: list[BankingFinding] = []
    for i, pair in enumerate(divergence.get("b0_only", [])):
        a, b = pair[0], pair[1]
        findings.append(
            BankingFinding.model_validate(
                {
                    "id": f"dx-mp-{i}",
                    "provision": f"{MIRROR_PAIR} :: {a}, {b}",
                    "as_built_ref": a,
                    "intended_ref": None,
                    "operation_ids": [],
                    "effect_class": "unresolved",
                    "rationale": f"B0 cross-layer/cross-entity mirror pair "
                    f"(RELATE_OBLIGATION / DEEM_SATISFIED-shaped): {a} ↔ {b}. Reform lever: "
                    "DEEM_SATISFIED / reliance, not MERGE.",
                    "baseline": None,
                    "normative_kind": [],
                    "disposition_state": "needs_review",
                    "confidence": 0.5,
                    "status": "draft",
                }
            )
        )
    return findings


# --- driver ----------------------------------------------------------------------------


@dataclass
class DiagnoseResult:
    consolidation_findings: list[BankingFinding] = field(default_factory=list)
    diagnostic_findings: list[BankingFinding] = field(default_factory=list)
    diagnostic_sets: list[DiagnosticSet] = field(default_factory=list)
    anchor_failures: list[str] = field(default_factory=list)
    divergence: dict[str, Any] = field(default_factory=dict)
    finding_cluster: dict[str, str] = field(default_factory=dict)  # finding_id -> cluster
    finding_kind: dict[str, str] = field(default_factory=dict)  # diagnostic finding_id -> kind


def run_diagnose(
    harness: LlmHarness,
    decompositions: list[dict[str, Any]],
    drafts: dict[str, Any],
    intended_doc: dict[str, Any],
    graph_doc: dict[str, Any],
    distilled_doc: dict[str, Any],
    excerpts: dict[str, str],
    cluster_of: dict[str, str],
) -> DiagnoseResult:
    ab = as_built_map(drafts)
    intended = intended_map(intended_doc)
    graph = load_graph(graph_doc)
    result = DiagnoseResult()

    for dec in decompositions:
        if not dec.get("operations"):
            continue
        ops = scaffold_operations(dec)
        cf = consolidation_finding(dec, ops, ab, intended, graph)
        result.consolidation_findings.append(cf)
        result.finding_cluster[cf.id] = str(dec.get("cluster", ""))

    distilled_doc = {**distilled_doc, "_cluster_of": cluster_of}
    for cluster in MVP_CLUSTERS:
        duties = _cluster_duties(distilled_doc, cluster, excerpts)
        if not duties:
            continue
        ds, corpus = diagnose_cluster(harness, cluster, duties)
        result.diagnostic_sets.append(ds)
        for i, d in enumerate(ds.diagnostics):
            ok = diagnostic_anchor_ok(d, corpus)
            if not ok:
                result.anchor_failures.append(f"{cluster}:{d.kind}:{d.evidence_quote[:40]!r}")
            df = diagnostic_finding(cluster, i, d, ok)
            result.diagnostic_findings.append(df)
            result.finding_cluster[df.id] = cluster
            result.finding_kind[df.id] = official_kind(d.kind)

    result.divergence = duplicate_divergence(decompositions, result.diagnostic_sets, set(drafts))

    # B4-T3: the B0 mirror pairs become first-class mirror_pair diagnostics.
    for mp in mirror_pair_findings(result.divergence, cluster_of):
        result.diagnostic_findings.append(mp)
        first_target = mp.as_built_ref or ""
        result.finding_cluster[mp.id] = cluster_of.get(first_target, "")
        result.finding_kind[mp.id] = MIRROR_PAIR

    return result


def diagnose_document(result: DiagnoseResult) -> dict[str, Any]:
    findings = result.consolidation_findings + result.diagnostic_findings
    return {
        "_meta": "B3-T4 diagnose + classify. Consolidation findings (one per B0 lever) and "
        "LLM diagnostics per MVP cluster; every effect class computed by the mechanical "
        "classifier after the LLM, never by the LLM. Normative kinds are proposals; nothing "
        "finalized.",
        "counts": {
            "consolidation_findings": len(result.consolidation_findings),
            "diagnostic_findings": len(result.diagnostic_findings),
            "anchor_failures": len(result.anchor_failures),
            "effect_classes": _effect_hist(findings),
            "in_review": sum(1 for f in findings if f.disposition_state == "needs_review"),
        },
        "anchor_failures": result.anchor_failures,
        "duplicate_divergence": result.divergence,
        "duplication_families": _duplication_families(result),
        "finding_cluster": result.finding_cluster,
        "finding_kind": result.finding_kind,
        "findings": [f.model_dump(mode="json") for f in findings],
    }


def _duplication_families(result: DiagnoseResult) -> dict[str, Any]:
    """The two official duplication families (B4-T3), each as a list of finding ids."""
    fk = result.finding_kind
    mirror = sorted(fid for fid, k in fk.items() if duplication_family(k) == MIRROR_PAIR)
    restate = sorted(fid for fid, k in fk.items() if duplication_family(k) == RESTATEMENT)
    return {
        "mirror_pair": {"count": len(mirror), "finding_ids": mirror},
        "restatement": {"count": len(restate), "finding_ids": restate},
    }


def _effect_hist(findings: list[BankingFinding]) -> dict[str, int]:
    hist: dict[str, int] = {}
    for f in findings:
        hist[f.effect_class] = hist.get(f.effect_class, 0) + 1
    return dict(sorted(hist.items()))
