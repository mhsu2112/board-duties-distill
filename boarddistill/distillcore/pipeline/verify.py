"""Verify stage (slice one, deterministic).

A claim is ``verified`` iff every span it cites resolves to a known source; otherwise
``contradicted``. This checks *citation presence*, not that the cited law says what the
claim asserts — that requires retrieval and lands behind this same interface (README
roadmap step 2). No network, no LLM.
"""

from __future__ import annotations

import json
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from ..models.base import SourceSpan, VerifierRecord, VerifierStatus
from ..models.review import RESOLVED_DISPOSITIONS
from .protocols import DutyLike


def verify_claims(
    duties: Sequence[DutyLike],
    sources: Sequence[Any],
) -> tuple[list[VerifierRecord], dict[str, VerifierStatus]]:
    """Return one VerifierRecord per claim and a claim_id -> status map."""
    source_ids = {s.id for s in sources}
    records: list[VerifierRecord] = []
    statuses: dict[str, VerifierStatus] = {}
    seen: set[str] = set()
    for duty in duties:
        for claim in duty.claims:
            if claim.id in seen:
                continue
            seen.add(claim.id)
            spans = list(claim.source_span_ids)
            resolved = bool(spans) and all(sid in source_ids for sid in spans)
            status: VerifierStatus = "verified" if resolved else "contradicted"
            records.append(
                VerifierRecord(
                    id=f"v-{claim.id}",
                    claim_id=claim.id,
                    status=status,
                    method="span_present",
                    checked_span_ids=spans,
                    note=None if resolved else "one or more cited spans not present in sources",
                )
            )
            statuses[claim.id] = status
    return records, statuses


def _finding_blockers(finding: dict[str, Any], claim_status: dict[str, str]) -> list[str]:
    blockers: list[str] = []
    if finding.get("normative_kind") and finding["disposition_state"] not in RESOLVED_DISPOSITIONS:
        blockers.append(f"open normative item ({finding['disposition_state']})")
    if finding["effect_class"] == "unresolved":
        blockers.append("unresolved effect class")
    for rec_id in finding.get("verifier_records", []):
        claim_id = rec_id.removeprefix("v-")
        status = claim_status.get(claim_id, "unverified")
        if status != "verified":
            blockers.append(f"claim {claim_id}: {status}")
    return blockers


def finalization_blocker_lines(
    findings: Sequence[dict[str, Any]],
    claim_status: dict[str, str],
) -> list[str]:
    """Human-readable blocker summary (§9 final section). Shared by render and verify."""
    lines = [
        f"- **{f['id']}** blocked: " + "; ".join(blk)
        for f in findings
        if (blk := _finding_blockers(f, claim_status))
    ]
    return lines or ["All findings are eligible for `final` (no blockers)."]


@dataclass(frozen=True)
class ReverifyResult:
    records: list[dict[str, Any]]
    claim_status: dict[str, str]
    blocker_lines: list[str]
    final_eligible: list[str]


def reverify_dir(outdir: Path) -> ReverifyResult:
    """Recompute verifier statuses and the final-status blocker summary from the written
    JSON in ``outdir`` (profile-independent — operates on the JSON shapes)."""
    duties = (
        json.loads((outdir / "as_built.json").read_text())["duties"]
        + json.loads((outdir / "intended.json").read_text())["duties"]
    )
    source_ids = {s["id"] for s in json.loads((outdir / "sources.json").read_text())["sources"]}
    findings = json.loads((outdir / "findings.json").read_text())["findings"]

    records: list[dict[str, Any]] = []
    claim_status: dict[str, str] = {}
    seen: set[str] = set()
    for duty in duties:
        for claim in duty.get("claims", []):
            if claim["id"] in seen:
                continue
            seen.add(claim["id"])
            spans = claim.get("source_span_ids", [])
            resolved = bool(spans) and all(sid in source_ids for sid in spans)
            status = "verified" if resolved else "contradicted"
            records.append(
                {
                    "id": f"v-{claim['id']}",
                    "claim_id": claim["id"],
                    "status": status,
                    "method": "span_present",
                    "checked_span_ids": spans,
                    "note": None if resolved else "one or more cited spans not present in sources",
                }
            )
            claim_status[claim["id"]] = status

    blocker_lines = finalization_blocker_lines(findings, claim_status)
    eligible = [f["id"] for f in findings if not _finding_blockers(f, claim_status)]
    return ReverifyResult(records, claim_status, blocker_lines, eligible)


# --- B1 live verification (retrieval-backed; resolver is injected, so core stays offline)


@dataclass(frozen=True)
class CitationVerdict:
    """A resolver's verdict on one citation: status, evidence span, and currency."""

    status: VerifierStatus
    note: str
    as_of_valid: bool
    support_signal: str  # "strong" | "weak" | "none" | "n/a"
    span: SourceSpan | None


class SourceResolver(Protocol):
    """Resolves a citation to primary-source evidence. The live (network) implementation
    lives in an adapter; the core only depends on this protocol."""

    def verify(self, citation: str, *, expected_actor: str) -> CitationVerdict: ...


@dataclass(frozen=True)
class RowVerification:
    duty_id: str
    cluster: str | None
    citation: str
    record: VerifierRecord
    verdict: CitationVerdict


def verify_targets(
    targets: Sequence[dict[str, Any]],
    resolver: SourceResolver,
) -> list[RowVerification]:
    """Verify each target duty's primary claim against ``resolver``. One VerifierRecord per
    duty; every row gets a status (never skipped). Deterministic given a fixed cache."""
    out: list[RowVerification] = []
    for duty in sorted(targets, key=lambda d: str(d["duty_id"])):
        citation = str(duty.get("instrument_id") or "")
        claims = duty.get("claims") or []
        claim_id = claims[0]["id"] if claims else f"claim-{duty['duty_id']}"
        verdict = resolver.verify(citation, expected_actor=str(duty.get("board_level") or ""))
        record = VerifierRecord(
            id=f"v-{claim_id}",
            claim_id=claim_id,
            status=verdict.status,
            method="live_retrieval",
            checked_span_ids=[verdict.span.id] if verdict.span is not None else [],
            note=verdict.note,
        )
        out.append(
            RowVerification(
                duty_id=str(duty["duty_id"]),
                cluster=duty.get("cluster"),
                citation=citation,
                record=record,
                verdict=verdict,
            )
        )
    return out
