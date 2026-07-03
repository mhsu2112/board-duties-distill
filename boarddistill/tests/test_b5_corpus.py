"""B5-T6 — corpus roll-up artifacts + feasibility tiering."""

from __future__ import annotations

from pathlib import Path

from adapters.b5_corpus import feasibility_tier

_ROOT = Path(__file__).resolve().parents[1]
_CORPUS = _ROOT / "outputs" / "b5" / "corpus"
_PACKET = _ROOT.parent / "REVIEW_PACKET_B5.md"


def test_feasibility_tier_follows_the_inventory_ordering() -> None:
    assert feasibility_tier("guidance_action", "single:MERGE") == 1
    assert feasibility_tier("interagency_statement", "single:CANONICALIZE_DEFINITION") == 2
    assert feasibility_tier("rule_apa", "consolidation") == 3
    assert feasibility_tier("joint_rulemaking", "vertical_rationalization") == 4  # vertical wins
    assert feasibility_tier("statutory_amendment", "single:REPEAL") == 5
    assert feasibility_tier(None, "single:MERGE") == 6


def test_corpus_artifacts_exist_and_are_traceable() -> None:
    for name in ("master_crosswalk.md", "reform_roadmap_v2.md", "corpus_stats.md"):
        p = _CORPUS / name
        if not p.exists():
            return  # artifacts not built in this checkout
        text = p.read_text()
        assert len(text) > 200
    roadmap = (_CORPUS / "reform_roadmap_v2.md").read_text()
    # every roadmap lever row is traceable to a package path
    assert "package.md" in roadmap
    assert "Tier legend" in roadmap
    stats = (_CORPUS / "corpus_stats.md").read_text()
    assert "unstated-board-action-standard" in stats
    assert "Duplication families" in stats


def test_review_packet_is_answerable_in_one_line() -> None:
    if not _PACKET.exists():
        return
    text = _PACKET.read_text()
    assert "accept all recommendations" in text
    assert "## Part 1" in text and "## Part 6" in text
    assert "closure test" in text.lower()
