"""B3-T2 — LLM distillation of the 50 verified as-built duties against their pinned source
excerpts.

The pinned quote for each verified row is the anchor domain: B2 already resolved it to the
cache, so any distilled anchor that is a verbatim substring of that quote resolves to the
cache by construction (the B3-T6 zero-hallucination invariant). The LLM proposes; nothing is
overwritten and nothing is finalized — every output lands as reviewable draft.

Two rules ride in ``profiles/lex_balanus/prompts/distill.md`` (+ the shared preamble):
anchor every asserted field, and prefer ``unresolved`` over a guess. Two checks run in code
after the LLM: (1) anchor verification — a non-empty evidence quote must be a substring of the
excerpt, else it is a hallucinated citation (checkpoint 1); (2) a verb-vs-retag cross-check —
an active board verb on a duty B2 retagged away from the board is flagged, never overwritten
(checkpoint discipline).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from distillcore.llm import LlmHarness, load_template, render
from distillcore.models.base import StrictModel
from profiles.lex_balanus.enums import Cadence, VerbStandard

# --- LLM I/O schema --------------------------------------------------------------------


class DistilledDefinition(StrictModel):
    term: str
    quote: str


class DistilledElement(StrictModel):
    text: str
    quote: str


class DistilledDuty(StrictModel):
    """What the LLM returns for one duty. Enum fields constrain the output; ``*_evidence`` /
    ``quote`` fields carry the verbatim anchor (empty ⇒ unresolved)."""

    duty_id: str
    verb_standard: VerbStandard
    verb_evidence: str = ""
    object: str
    object_evidence: str = ""
    cadence: Cadence
    cadence_evidence: str = ""
    definitions_used: list[DistilledDefinition] = []  # noqa: RUF012 (pydantic field default)
    elements: list[DistilledElement] = []  # noqa: RUF012
    unresolved_fields: list[str] = []  # noqa: RUF012
    notes: str = ""


# Active board-performance verbs. If B2 retagged a duty's actor away from the board, one of
# these re-asserts board performance and contradicts the retag (flag, never overwrite).
_ACTIVE_BOARD_VERBS: frozenset[VerbStandard] = frozenset(
    {VerbStandard.APPROVE, VerbStandard.CERTIFY, VerbStandard.REVIEW_AND_CHALLENGE}
)


# --- anchor verification ---------------------------------------------------------------


def _despace(s: str) -> str:
    """Drop all whitespace. Anchoring is whitespace-insensitive so a quote still counts as
    resolved when the *content* is present but the cached excerpt carries a spacing artifact
    from XML text extraction (e.g. ``"C apital plan cycle"``). Content must match exactly;
    only spacing is ignored, so this never turns a fabrication into a match."""
    return re.sub(r"\s+", "", s)


def anchor_failures(d: DistilledDuty, excerpt: str) -> list[str]:
    """Every non-empty evidence quote must be present in the excerpt (whitespace-insensitive).
    A miss is a hallucinated citation (checkpoint 1) — the row is a bug *and* a gate failure."""
    fails: list[str] = []
    excerpt_ws = _despace(excerpt)

    def _check(name: str, quote: str) -> None:
        if quote and _despace(quote) not in excerpt_ws:
            fails.append(f"{name}: {quote[:50]!r} not in excerpt")

    _check("verb_evidence", d.verb_evidence)
    _check("object_evidence", d.object_evidence)
    _check("cadence_evidence", d.cadence_evidence)
    for i, df in enumerate(d.definitions_used):
        _check(f"definitions_used[{i}].quote", df.quote)
    for i, el in enumerate(d.elements):
        _check(f"elements[{i}].quote", el.quote)
    return fails


# --- verb-vs-retag cross-check ---------------------------------------------------------


def verb_retag_conflict(d: DistilledDuty, retag: dict[str, Any]) -> dict[str, Any] | None:
    """Flag (do not resolve) an active board verb on a duty B2 retagged away from the board."""
    if retag.get("parameter") != "actor":
        return None
    if d.verb_standard not in _ACTIVE_BOARD_VERBS:
        return None
    return {
        "duty_id": d.duty_id,
        "distilled_verb_standard": d.verb_standard.value,
        "retag_from_actor": retag.get("from_actor"),
        "retag_to_actor": retag.get("to_actor"),
        "reason": (
            f"distilled verb_standard '{d.verb_standard.value}' asserts board performance, "
            f"but B2 retagged the actor to '{retag.get('to_actor')}'. Flagged, not "
            "overwritten (TODO(human): reconcile verb vs. actor)."
        ),
    }


# --- driver ----------------------------------------------------------------------------


@dataclass(frozen=True)
class DistillTarget:
    duty_id: str
    draft: dict[str, Any]
    excerpt: str  # the verified pinned quote (anchor domain)
    citation: str


@dataclass
class DistilledRow:
    duty_id: str
    distilled: DistilledDuty
    anchor_ok: bool
    anchor_failures: list[str]
    retag_conflict: dict[str, Any] | None


def build_targets(verification: dict[str, Any], drafts: dict[str, Any]) -> list[DistillTarget]:
    """The 50 verified rows, each paired with its draft spec and pinned quote."""
    records = {r["claim_id"]: r for r in verification["records"]}
    spans = {s["id"]: s for s in verification["spans"]}
    targets: list[DistillTarget] = []
    for row in verification["rows"]:
        if row["status"] != "verified":
            continue
        duty_id = row["duty_id"]
        rec = records.get(f"claim-{duty_id}")
        span = spans.get(rec["checked_span_ids"][0]) if rec and rec["checked_span_ids"] else None
        if span is None or duty_id not in drafts:
            raise ValueError(f"verified row {duty_id} lacks a span or a draft spec")
        targets.append(
            DistillTarget(
                duty_id=duty_id,
                draft=drafts[duty_id],
                excerpt=span["quote"],
                citation=span["citation"],
            )
        )
    return sorted(targets, key=lambda t: t.duty_id)


def _prompt_for(target: DistillTarget) -> str:
    d = target.draft
    return render(
        load_template("distill"),
        {
            "duty_id": target.duty_id,
            "label": str(d.get("label", "")),
            "cluster": str(d.get("cluster") or ""),
            "instrument": str(d.get("instrument_id") or target.citation),
            "draft_verb": str(d.get("verb_standard", "")),
            "draft_object": str(d.get("object", "")),
            "draft_cadence": str(d.get("cadence", "")),
            "verb_options": ", ".join(m.value for m in VerbStandard),
            "cadence_options": ", ".join(m.value for m in Cadence),
            "source_excerpt": target.excerpt,
        },
    )


def distill_target(
    harness: LlmHarness, target: DistillTarget, retags: dict[str, Any]
) -> DistilledRow:
    distilled = harness.complete(_prompt_for(target), DistilledDuty)
    fails = anchor_failures(distilled, target.excerpt)
    retag = retags.get(target.duty_id)
    conflict = verb_retag_conflict(distilled, retag) if retag else None
    return DistilledRow(
        duty_id=target.duty_id,
        distilled=distilled,
        anchor_ok=not fails,
        anchor_failures=fails,
        retag_conflict=conflict,
    )


def distill_all(
    harness: LlmHarness,
    verification: dict[str, Any],
    drafts: dict[str, Any],
    retags: dict[str, Any],
) -> list[DistilledRow]:
    return [
        distill_target(harness, t, retags) for t in build_targets(verification, drafts)
    ]


# --- reports ---------------------------------------------------------------------------


def _object_unresolved(r: DistilledRow) -> bool:
    """The excerpt did not even support the duty's object — a stronger signal than a missing
    verb: the pinned span may not support this duty at all (a source-mismatch for review)."""
    return not r.distilled.object.strip() or "object" in r.distilled.unresolved_fields


def distilled_document(rows: list[DistilledRow]) -> dict[str, Any]:
    conflicts = [r.retag_conflict for r in rows if r.retag_conflict]
    anchor_fail_rows = [r.duty_id for r in rows if not r.anchor_ok]
    mismatch_rows = [r.duty_id for r in rows if _object_unresolved(r)]
    return {
        "_meta": "B3-T2 as-built distillation. LLM proposals refined against each verified "
        "pinned excerpt; every asserted field anchored to a substring of that excerpt. "
        "Nothing overwritten or finalized — all reviewable draft.",
        "counts": {
            "distilled": len(rows),
            "anchor_clean": sum(1 for r in rows if r.anchor_ok),
            "anchor_failures": len(anchor_fail_rows),
            "verb_retag_conflicts": len(conflicts),
            "source_mismatch_rows": len(mismatch_rows),
        },
        "anchor_failure_rows": sorted(anchor_fail_rows),
        "source_mismatch_rows": sorted(mismatch_rows),
        "verb_retag_conflicts": conflicts,
        "rows": [
            {
                "duty_id": r.duty_id,
                "anchor_ok": r.anchor_ok,
                "anchor_failures": r.anchor_failures,
                "retag_conflict": r.retag_conflict,
                "distilled": r.distilled.model_dump(mode="json"),
            }
            for r in rows
        ],
    }


def _changed(before: str, after: str) -> str:
    return f"`{before}` → `{after}`" if before != after else f"`{after}` (unchanged)"


def diff_report(rows: list[DistilledRow], drafts: dict[str, Any]) -> str:
    lines = [
        "# B3-T2 — distilled as-built vs. draft",
        "",
        "LLM-refined `verb_standard` / `object` / `cadence` against each verified pinned "
        "excerpt. Proposals only — nothing overwritten. `⚠` marks an anchor failure or a "
        "verb-vs-retag conflict (checkpoint).",
        "",
        "| duty_id | verb_standard | cadence | object (draft → distilled) | flags |",
        "| --- | --- | --- | --- | --- |",
    ]
    for r in rows:
        d = drafts[r.duty_id]
        dd = r.distilled
        flags = []
        if not r.anchor_ok:
            flags.append("⚠ anchor")
        if r.retag_conflict:
            flags.append("⚠ verb-vs-retag")
        obj = _changed(str(d.get("object", ""))[:60], dd.object[:60])
        lines.append(
            f"| {r.duty_id} "
            f"| {_changed(str(d.get('verb_standard', '')), dd.verb_standard.value)} "
            f"| {_changed(str(d.get('cadence', '')), dd.cadence.value)} "
            f"| {obj} "
            f"| {' '.join(flags) or '—'} |"
        )
    return "\n".join(lines) + "\n"
