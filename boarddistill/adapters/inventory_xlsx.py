"""T8 — deterministic inventory-xlsx adapter.

Reads the "All Board Duties" sheet of the combined inventory and emits **draft**
DutySpecs. Every emitted claim is ``unverified`` and every spec is non-finalizable — the
adapter maps local, deterministic columns; it never asserts a verified legal claim. The
column mappings are fuzzy hints and are a checkpoint (§14.1): confirm before trusting.

Local + deterministic: openpyxl only, no network, no LLM. Outputs are drafts, not findings.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

import openpyxl

from distillcore.models.base import SnapshotDates
from profiles.lex_balanus.models import DutySpec

_SHEET = "All Board Duties"
_HEADER_ROW = 3

DRAFT_BANNER = (
    "DRAFT — imported from the inventory xlsx by adapters/inventory_xlsx.py. "
    "Every claim is UNVERIFIED and no spec is finalizable. Column mappings are fuzzy "
    "hints; mappings CONFIRMED by M. Hsu, 2026-07-02 (REVIEW_CHECKLIST Item 3). "
    "Claims remain UNVERIFIED until B1 citation verification."
)

_DEFAULT_SNAPSHOT = SnapshotDates(
    inventory_as_of=date(2026, 6, 5),
    consolidation_as_of=date(2026, 6, 30),
    current_as_of=date(2026, 7, 1),
)


def _s(value: Any) -> str:
    return "" if value is None else str(value).strip()


def _legal_force(raw: str) -> str:
    s = raw.lower()
    if "examination manual" in s:
        return "manual"
    if "enforceable guideline" in s:
        return "enforceable_guideline"
    if "statute" in s:
        return "statute"
    if "regulation" in s:
        return "regulation"
    return "guidance"


def _cadence(raw: str) -> str:
    s = raw.lower()
    if "annual" in s:
        return "annual"
    if "quarterly" in s:
        return "quarterly"
    if "event-driven" in s or "event driven" in s:
        return "event_driven"
    if "periodic" in s or "ongoing" in s:
        return "continuous"
    return "none_specified"


def _currency(raw: str) -> str:
    s = raw.lower()
    if "rescinded" in s:
        return "rescinded_formal"
    if "superseded" in s:
        return "superseded"
    if "proposed" in s or "proposal" in s:
        return "stale_unverified"
    return "active"


def _entity(raw: str) -> str:
    s = raw.lower()
    if "both" in s or "&" in s or "and bhc" in s:
        return "both"
    if "idi" in s:
        return "IDI"
    if "bhc" in s or "issuer" in s:
        return "BHC"
    return "both"


def _confidence(raw: str) -> float:
    s = raw.lower()
    if s.startswith("high"):
        return 0.9
    if s.startswith("medium"):
        return 0.6
    if s.startswith("low"):
        return 0.3
    return 0.5


def _consequence(raw: str) -> str:
    s = raw.lower()
    if "enforcement" in s:
        return "enforcement_action"
    if "disclosure" in s:
        return "public_disclosure"
    if "certif" in s:
        return "certification_required"
    return "supervisory_finding"


def _layer_prefix(raw: str) -> str:
    s = raw.lower()
    if s.startswith("binding"):
        return "b:"
    if s.startswith("personal liability"):
        return "p:"
    return "s:"


@dataclass(frozen=True)
class ImportResult:
    banner: str
    duties: list[DutySpec]


def import_inventory(
    xlsx_path: Path,
    snapshot: SnapshotDates | None = None,
) -> ImportResult:
    snap = snapshot or _DEFAULT_SNAPSHOT
    workbook = openpyxl.load_workbook(xlsx_path, read_only=True, data_only=True)
    sheet = workbook[_SHEET]

    header_row = next(sheet.iter_rows(min_row=_HEADER_ROW, max_row=_HEADER_ROW, values_only=True))
    header = [_s(c) for c in header_row]
    col = {name: idx for idx, name in enumerate(header)}

    def cell(row: tuple[Any, ...], name: str) -> str:
        idx = col.get(name)
        return _s(row[idx]) if idx is not None and idx < len(row) else ""

    duties: list[DutySpec] = []
    for row in sheet.iter_rows(min_row=_HEADER_ROW + 1, values_only=True):
        duty_id_raw = cell(row, "ID")
        if not duty_id_raw:
            continue
        duty_id = _layer_prefix(cell(row, "Layer")) + duty_id_raw
        legal_force = _legal_force(cell(row, "Legal force"))
        nature = cell(row, "Board duty (nature)") or duty_id
        citation = cell(row, "Citation") or cell(row, "Source") or "n/a"
        confidence = _confidence(cell(row, "Confidence"))

        duties.append(
            DutySpec.model_validate(
                {
                    "duty_id": duty_id,
                    "label": nature[:120],
                    "layer": "as_built",
                    "cluster": cell(row, "Cluster") or None,
                    "snapshot_dates": snap.model_dump(mode="json"),
                    "board_level": cell(row, "Board level") or "full_board",
                    "director_class": cell(row, "Director-type distinction") or "any",
                    "entity": _entity(cell(row, "Entity")),
                    "verb_standard": "none_specified",
                    "object": nature,
                    "cadence": _cadence(cell(row, "Cadence")),
                    "trigger": None,
                    "legal_force": legal_force,
                    "consequence": _consequence(cell(row, "Supervisory consequence")),
                    "instrument_id": citation,
                    "currency_status": _currency(cell(row, "Status (currency)")),
                    "source_citations": [citation] if citation != "n/a" else [],
                    "claims": [
                        {
                            "id": f"claim-{duty_id}",
                            "claim": nature,
                            "source_span_ids": [f"cite-{duty_id}"],
                            "support_type": "paraphrased",
                            "authority_type": legal_force,
                            "as_of_valid": False,
                            "confidence": confidence,
                            "verifier_status": "unverified",
                        }
                    ],
                    "confidence": confidence,
                }
            )
        )
    workbook.close()
    return ImportResult(banner=DRAFT_BANNER, duties=duties)
