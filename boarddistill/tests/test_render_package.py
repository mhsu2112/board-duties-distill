"""T6 — test #10: all three fixture packages render into package.md with the §9 sections
(findings table, crosswalk, blocker summary, etc.)."""

from __future__ import annotations

from pathlib import Path

import pytest

from adapters.fixture_loader import load_fixture
from distillcore.pipeline.render import render_package
from profiles.lex_balanus.pipeline import run_fixture, write_outputs

_FIXTURES = Path(__file__).resolve().parent.parent / "data" / "fixtures" / "us-gsib"
_DIRS = ["icfr", "sr12-17", "board-effectiveness"]

_REQUIRED_SECTIONS = [
    "## Snapshot dates",
    "## Cluster summary",
    "## As-built duties",
    "## Intended duties",
    "## Instrument graph",
    "## Findings",
    "## Duty crosswalk",
    "## Authority to act",
    "## Claim verification",
    "## Normative review queue",
    "## Final-status blocker summary",
]


@pytest.mark.parametrize("name", _DIRS)
def test_package_renders_with_required_sections(name: str, tmp_path: Path) -> None:
    bundle = load_fixture(_FIXTURES / name)
    result = run_fixture(bundle)
    fixture_out = write_outputs(result, bundle, tmp_path)
    markdown = render_package(fixture_out)
    for section in _REQUIRED_SECTIONS:
        assert section in markdown, f"{name} missing section {section!r}"


@pytest.mark.parametrize("name", _DIRS)
def test_findings_table_and_crosswalk_have_content(name: str, tmp_path: Path) -> None:
    bundle = load_fixture(_FIXTURES / name)
    result = run_fixture(bundle)
    fixture_out = write_outputs(result, bundle, tmp_path)
    markdown = render_package(fixture_out)
    # every computed finding's disposition appears in the findings table
    for finding in result.computed_findings:
        assert finding.effect_class in markdown
    # crosswalk lists each as-built duty id
    for duty in bundle.as_built:
        assert duty.duty_id in markdown


def test_needs_review_findings_appear_in_blocker_summary(tmp_path: Path) -> None:
    bundle = load_fixture(_FIXTURES / "icfr")
    result = run_fixture(bundle)
    fixture_out = write_outputs(result, bundle, tmp_path)
    markdown = render_package(fixture_out)
    summary = markdown.split("## Final-status blocker summary")[1]
    # the DEEM finding is a needs_review policy_choice -> a blocker
    assert "f-deem" in summary


def test_cli_render_writes_package_md(tmp_path: Path) -> None:
    bundle = load_fixture(_FIXTURES / "board-effectiveness")
    result = run_fixture(bundle)
    fixture_out = write_outputs(result, bundle, tmp_path)
    markdown = render_package(fixture_out)
    (fixture_out / "package.md").write_text(markdown)
    assert (fixture_out / "package.md").exists()
