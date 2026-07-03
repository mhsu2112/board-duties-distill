"""B6-T3 — the calculus engine over the pooled, pseudonymized RBI corpus.

Two-stage, span-anchored, under harness rules (temp-0 via cache, budget guard). The prompt NEVER
names Master Directions, the RRA, or the consolidation program (§1.3a); the corpus is
pseudonymized (§1.3b); every LLM output is leakage-scanned (§1.3c) and any hit is quarantined.

Stage 1 (grouping): from a compact index (doc_id · subject · addressee · cross-refs) the engine
proposes consolidation groups — which circulars belong to one consolidated instrument.
Stage 2 (operations): per group, over the circular bodies, the engine proposes calculus operations
(MERGE / REPEAL / CANONICALIZE_DEFINITION / RESOLVE_CROSS_REFERENCE / RELATE_OBLIGATION /
ELEVATE_GENERAL_RULE) with a verbatim span from a circular as evidence. Unanchored operations are
dropped (zero unanchored claims, DoD).
"""

from __future__ import annotations

import re
from typing import Any, Literal

from adapters.rbi_adapter import has_leaked_identifier
from distillcore.llm import LlmHarness
from distillcore.models.base import StrictModel

# Terms that would reveal the held-out consolidation program if they appeared in an LLM output
# (in addition to the pseudonymizer's RBI-identifier scan). A hit ⇒ quarantine (checkpoint 3.2).
_LEAK_TERMS = re.compile(
    r"\b(master\s+direction|regulations?\s+review\s+authority|\brra\b|reserve\s+bank\s+of\s+india|"
    r"rbi/\d)",
    re.I,
)

_ENGINE_OPS = (
    "MERGE",
    "REPEAL",
    "CANONICALIZE_DEFINITION",
    "RESOLVE_CROSS_REFERENCE",
    "RELATE_OBLIGATION",
    "ELEVATE_GENERAL_RULE",
)


def leakage_hit(text: str) -> bool:
    return bool(_LEAK_TERMS.search(text)) or has_leaked_identifier(text)


# --- schemas ---------------------------------------------------------------------------


class ProposedGroup(StrictModel):
    group_id: str
    theme: str
    doc_ids: list[str] = []  # noqa: RUF012


class GroupingProposal(StrictModel):
    groups: list[ProposedGroup] = []  # noqa: RUF012


class EngineOp(StrictModel):
    primitive: Literal[
        "MERGE",
        "REPEAL",
        "CANONICALIZE_DEFINITION",
        "RESOLVE_CROSS_REFERENCE",
        "RELATE_OBLIGATION",
        "ELEVATE_GENERAL_RULE",
    ]
    doc_ids: list[str] = []  # noqa: RUF012
    evidence_quote: str
    rationale: str = ""


class GroupOps(StrictModel):
    operations: list[EngineOp] = []  # noqa: RUF012


# --- prompts (benchmark-neutral; no MD/RRA references) ---------------------------------


def _index_block(instruments: list[dict[str, Any]]) -> str:
    lines = []
    for s in instruments:
        xref = f" cites:{','.join(s['cross_refs'])}" if s["cross_refs"] else ""
        lines.append(f"{s['doc_id']} · {s['subject'][:90]} · [{s['addressee'][:40]}]{xref}")
    return "\n".join(lines)


def grouping_prompt(instruments: list[dict[str, Any]]) -> str:
    return (
        "You are a regulatory-structure analyst. Below is an index of individual regulatory "
        "circulars, each with a stable id, its subject, its addressee, and any circulars it "
        "cites. Propose how these circulars should be organized into CONSOLIDATED INSTRUMENTS — "
        "each group is the set of circulars that cover one coherent subject and would sensibly be "
        "combined into a single consolidated instrument. Assign EVERY id to exactly one group. "
        "Group by subject-matter and addressee coherence and by citation structure; do not invent "
        "ids. Return JSON only.\n\n"
        "Do NOT reference any specific real-world regulation, regulator, consolidation program, or "
        "'master direction' — reason only from the subjects and structure shown.\n\n"
        "## Circular index\n" + _index_block(instruments)
    )


def operations_prompt(theme: str, docs: list[dict[str, Any]]) -> str:
    block = "\n\n".join(
        f"{d['doc_id']} · {d['subject'][:90]}\n<<<\n{d['body'][:1200]}\n>>>" for d in docs
    )
    return (
        "You are a regulatory-consolidation calculus. Given a group of circulars on one subject, "
        "propose the structural OPERATIONS that would consolidate them into a single instrument. "
        "Use ONLY these operation primitives:\n"
        "- MERGE: fold multiple circulars stating one obligation into one.\n"
        "- REPEAL: a circular that is superseded/withdrawn by a later one in the group.\n"
        "- CANONICALIZE_DEFINITION: a single definition replacing divergent ones.\n"
        "- RESOLVE_CROSS_REFERENCE: replace a circular's cross-reference with the "
        "consolidated text.\n"
        "- RELATE_OBLIGATION: two circulars stating parallel obligations kept distinct.\n"
        "- ELEVATE_GENERAL_RULE: a recurring instruction lifted into a general part.\n\n"
        "For each operation give `doc_ids` (the circulars it acts on) and an `evidence_quote` that "
        "is a VERBATIM substring copied from one of the circular bodies below. Do not invent text; "
        "an operation without a verbatim quote is an error. Do NOT name any real regulator, "
        "regulation, or consolidation program. Return JSON only.\n\n"
        f"## Group subject: {theme}\n\n## Circulars\n{block}"
    )


def baseline_prompt(instruments: list[dict[str, Any]]) -> str:
    """The §1.4 plain-LLM baseline: one prompt, no calculus scaffold, no operations, no
    span-anchoring — just 'propose how to consolidate these instruments.' Same index, same model,
    same leakage rules. Its grouping is scored identically to the engine's; the benchmark claim is
    the delta the scaffold adds."""
    return (
        "Below is a list of regulatory circulars, each with an id, subject, addressee, and the "
        "circulars it cites. Propose how to consolidate these instruments: group together the "
        "circulars that should be combined into a single consolidated instrument, "
        "assigning every "
        "id to exactly one group. Return JSON only. Do not name any real regulation "
        "or regulator.\n\n"
        "## Circulars\n" + _index_block(instruments)
    )


# --- driver ----------------------------------------------------------------------------


def _despace(s: str) -> str:
    return re.sub(r"\s+", "", s)


def _partition(
    grouping: GroupingProposal, all_ids: set[str]
) -> list[ProposedGroup]:
    """Turn a raw grouping into a clean partition: dedup within/across groups, singletons for any
    unassigned id (never silently dropped)."""
    assigned: set[str] = set()
    groups: list[ProposedGroup] = []
    for g in grouping.groups:
        ids = list(dict.fromkeys(d for d in g.doc_ids if d in all_ids and d not in assigned))
        if not ids:
            continue
        assigned.update(ids)
        groups.append(ProposedGroup(group_id=g.group_id, theme=g.theme, doc_ids=ids))
    for missing in sorted(all_ids - assigned):
        groups.append(
            ProposedGroup(group_id=f"solo-{missing}", theme="(unassigned)", doc_ids=[missing])
        )
    return groups


def run_baseline(harness: LlmHarness, instruments: list[dict[str, Any]]) -> dict[str, Any]:
    all_ids = {s["doc_id"] for s in instruments}
    grouping = harness.complete(baseline_prompt(instruments), GroupingProposal)
    groups = _partition(grouping, all_ids)
    leaky = [g.group_id for g in groups if leakage_hit(g.theme)]
    return {
        "_meta": "B6-T4 plain-LLM baseline: one grouping prompt, no calculus scaffold, no "
        "operations. Same corpus/model/leakage rules; scored identically to the engine (§1.4).",
        "counts": {
            "instruments": len(instruments),
            "groups": len(groups),
            "multi_doc_groups": sum(1 for g in groups if len(g.doc_ids) > 1),
            "leaky_themes": len(leaky),
            "budget": harness.budget.summary(),
        },
        "groups": [
            {"group_id": g.group_id, "theme": g.theme, "doc_ids": g.doc_ids} for g in groups
        ],
    }


def run_engine(
    harness: LlmHarness, instruments: list[dict[str, Any]], max_group_docs: int = 40
) -> dict[str, Any]:
    by_id = {s["doc_id"]: s for s in instruments}
    all_ids = set(by_id)

    grouping = harness.complete(grouping_prompt(instruments), GroupingProposal)
    quarantined: list[dict[str, str]] = []

    # coverage: assign any unassigned id to its own singleton group (the engine's grouping is a
    # partition; a missed id is a singleton, not silently dropped).
    assigned: set[str] = set()
    groups: list[ProposedGroup] = []
    for g in grouping.groups:
        # dedup within the group (dict.fromkeys) as well as across groups (assigned)
        ids = list(dict.fromkeys(d for d in g.doc_ids if d in all_ids and d not in assigned))
        if not ids:
            continue
        assigned.update(ids)
        groups.append(ProposedGroup(group_id=g.group_id, theme=g.theme, doc_ids=ids))
    for missing in sorted(all_ids - assigned):
        groups.append(
            ProposedGroup(group_id=f"solo-{missing}", theme="(unassigned)", doc_ids=[missing])
        )

    group_records: list[dict[str, Any]] = []
    for g in groups:
        docs = [by_id[d] for d in g.doc_ids]
        ops_out: list[dict[str, Any]] = []
        # only ask for operations on multi-doc groups (a singleton has nothing to consolidate)
        if len(docs) > 1:
            corpus = "\n".join(d["body"] for d in docs)
            corpus_ws = _despace(corpus)
            for batch_start in range(0, len(docs), max_group_docs):
                batch = docs[batch_start : batch_start + max_group_docs]
                result = harness.complete(operations_prompt(g.theme, batch), GroupOps)
                for op in result.operations:
                    text = op.evidence_quote + " " + op.rationale
                    if leakage_hit(text):
                        quarantined.append({"group": g.group_id, "quote": op.evidence_quote[:80]})
                        continue
                    anchored = bool(op.evidence_quote) and _despace(op.evidence_quote) in corpus_ws
                    if not anchored:
                        continue  # zero unanchored claims (DoD): drop
                    ops_out.append(
                        {
                            "primitive": op.primitive,
                            "doc_ids": [d for d in op.doc_ids if d in all_ids],
                            "evidence_quote": op.evidence_quote[:300],
                            "rationale": op.rationale[:200],
                        }
                    )
        group_records.append(
            {"group_id": g.group_id, "theme": g.theme, "doc_ids": g.doc_ids, "operations": ops_out}
        )

    op_mix: dict[str, int] = {}
    for gr in group_records:
        for op in gr["operations"]:
            op_mix[op["primitive"]] = op_mix.get(op["primitive"], 0) + 1

    return {
        "_meta": "B6-T3 engine proposals over the pooled pseudonymized corpus. Prompt never names "
        "Master Directions / RRA; every operation span-anchored; leakage-scanned outputs.",
        "counts": {
            "instruments": len(instruments),
            "groups": len(group_records),
            "multi_doc_groups": sum(1 for g in group_records if len(g["doc_ids"]) > 1),
            "operations": sum(len(g["operations"]) for g in group_records),
            "operation_mix": dict(sorted(op_mix.items())),
            "quarantined_leakage": len(quarantined),
            "budget": harness.budget.summary(),
        },
        "quarantined": quarantined,
        "groups": group_records,
    }
