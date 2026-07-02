"""Verify stage (slice one, deterministic).

A claim is ``verified`` iff every span it cites resolves to a known source; otherwise
``contradicted``. This checks *citation presence*, not that the cited law says what the
claim asserts — that requires retrieval and lands behind this same interface (README
roadmap step 2). No network, no LLM.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from ..models.base import VerifierRecord, VerifierStatus
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
