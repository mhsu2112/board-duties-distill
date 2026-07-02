"""T7 — disposition state machine, finalization gates, and re-verify end-to-end."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from adapters.fixture_loader import load_fixture
from distillcore.models.base import LegalClaim
from distillcore.models.review import transition
from distillcore.pipeline.invariants import finalize
from distillcore.pipeline.verify import reverify_dir
from profiles.lex_balanus.models import BankingFinding
from profiles.lex_balanus.pipeline import run_fixture, write_outputs

_FIXTURES = Path(__file__).resolve().parent.parent / "data" / "fixtures" / "us-gsib"


def _finding(**over: Any) -> BankingFinding:
    base: dict[str, Any] = {
        "id": "f",
        "provision": "P",
        "operation_ids": [],
        "effect_class": "clarify",
        "rationale": "r",
        "confidence": 0.8,
    }
    base.update(over)
    return BankingFinding.model_validate(base)


def _claim(cid: str, spans: list[str], status: str = "verified") -> LegalClaim:
    return LegalClaim.model_validate(
        {
            "id": cid,
            "claim": "c",
            "source_span_ids": spans,
            "support_type": "quoted",
            "authority_type": "regulation",
            "as_of_valid": True,
            "confidence": 0.9,
            "verifier_status": status,
        }
    )


def test_disposition_transition_legal_and_illegal() -> None:
    f = _finding(disposition_state="needs_review")
    moved = transition(f, "reviewer_accepted")
    assert moved.disposition_state == "reviewer_accepted"
    with pytest.raises(ValueError):
        transition(moved, "needs_review")  # reviewer verdicts are terminal
    with pytest.raises(ValueError):
        transition(_finding(disposition_state="auto_ok"), "reviewer_accepted")


def test_finalize_promotes_only_eligible_findings() -> None:
    clean = _finding(effect_class="clarify", normative_kind=[], disposition_state="auto_ok")
    promoted = finalize(clean, [_claim("c1", ["s1"], status="verified")])
    assert promoted.status == "final"

    normative = _finding(
        effect_class="change",
        normative_kind=["policy_choice"],
        disposition_state="needs_review",
    )
    blocked = finalize(normative, [_claim("c1", ["s1"], status="verified")])
    assert blocked.status == "draft"

    unverified = finalize(clean, [_claim("c2", ["s1"], status="unverified")])
    assert unverified.status == "draft"


def test_reverify_dir_recomputes_and_summarizes(tmp_path: Path) -> None:
    bundle = load_fixture(_FIXTURES / "icfr")
    result = run_fixture(bundle)
    out = write_outputs(result, bundle, tmp_path)

    rv = reverify_dir(out)
    assert rv.claim_status
    assert all(status == "verified" for status in rv.claim_status.values())
    # auto_ok clarify findings are final-eligible; needs_review policy findings are not
    assert "f-factor" in rv.final_eligible
    assert "f-relate" in rv.final_eligible
    assert "f-deem" not in rv.final_eligible
    assert "f-cadence" not in rv.final_eligible
    # the DEEM finding shows up as a blocker
    assert any("f-deem" in line for line in rv.blocker_lines)


def test_reverify_flags_missing_span_as_contradicted(tmp_path: Path) -> None:
    import json

    bundle = load_fixture(_FIXTURES / "board-effectiveness")
    result = run_fixture(bundle)
    out = write_outputs(result, bundle, tmp_path)
    # corrupt a claim to cite a span that is not in sources.json
    ab_path = out / "as_built.json"
    doc = json.loads(ab_path.read_text())
    doc["duties"][0]["claims"][0]["source_span_ids"] = ["does-not-exist"]
    ab_path.write_text(json.dumps(doc))

    rv = reverify_dir(out)
    assert any(status == "contradicted" for status in rv.claim_status.values())
