"""T8 — test #11: import-inventory emits ~230 draft DutySpecs; every claim unverified;
no spec is finalizable (drafts can never silently finalize)."""

from __future__ import annotations

from pathlib import Path

import pytest

from adapters.inventory_xlsx import DRAFT_BANNER, import_inventory
from distillcore.pipeline.invariants import can_finalize
from profiles.lex_balanus.models import BankingFinding

_XLSX = (
    Path(__file__).resolve().parents[2]
    / "Synthesis"
    / "gsib-board_duties-combined_inventory.xlsx"
)

pytestmark = pytest.mark.skipif(not _XLSX.exists(), reason="inventory xlsx not present")


def _draft_finding(duty_id: str) -> BankingFinding:
    return BankingFinding.model_validate(
        {
            "id": f"f-{duty_id}",
            "provision": duty_id,
            "as_built_ref": duty_id,
            "operation_ids": [],
            "effect_class": "unresolved",
            "rationale": "imported draft",
            "confidence": 0.5,
        }
    )


def test_import_emits_many_drafts() -> None:
    result = import_inventory(_XLSX)
    assert result.banner == DRAFT_BANNER
    assert 200 <= len(result.duties) <= 260  # ~230 rows in the sheet


def test_every_emitted_claim_is_unverified() -> None:
    result = import_inventory(_XLSX)
    for duty in result.duties:
        assert duty.claims, f"{duty.duty_id} has no claims"
        for claim in duty.claims:
            assert claim.verifier_status == "unverified"


def test_no_emitted_spec_is_finalizable() -> None:
    result = import_inventory(_XLSX)
    for duty in result.duties:
        # a draft finding over this spec's (unverified) claims can never reach final
        ok, blockers = can_finalize(_draft_finding(duty.duty_id), duty.claims)
        assert not ok
        assert blockers


def test_layer_prefix_and_force_hints() -> None:
    result = import_inventory(_XLSX)
    ids = {d.duty_id for d in result.duties}
    # binding and supervisory layers get distinct prefixes
    assert any(i.startswith("b:") for i in ids)
    assert any(i.startswith("s:") for i in ids)
    # legal_force is always a valid enum value (never free text)
    forces = {str(d.legal_force) for d in result.duties}
    assert forces <= {"statute", "regulation", "enforceable_guideline", "guidance", "manual"}
