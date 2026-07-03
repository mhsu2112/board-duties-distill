"""B6-T1 — the sealed answer-key path guard (leakage control §1.3)."""

from __future__ import annotations

from pathlib import Path

import pytest

from adapters.benchmark_guard import (
    ANSWER_KEY_DIR,
    CORPUS_DIR,
    PSEUDONYM_DIR,
    AnswerKeyAccessError,
    assert_proposal_safe,
    guarded_read,
    is_answer_key_path,
)


def test_answer_key_and_pseudonym_paths_are_sealed() -> None:
    assert is_answer_key_path(ANSWER_KEY_DIR / "MD-KYC-2016.json")
    assert is_answer_key_path(PSEUDONYM_DIR / "map.json")
    # a corpus path is NOT sealed
    assert not is_answer_key_path(CORPUS_DIR / "circular-0001.txt")


def test_proposal_pipeline_cannot_read_the_answer_key() -> None:
    with pytest.raises(AnswerKeyAccessError):
        assert_proposal_safe(ANSWER_KEY_DIR / "MD-KYC-2016.json")
    with pytest.raises(AnswerKeyAccessError):
        guarded_read(ANSWER_KEY_DIR / "anything.json")
    with pytest.raises(AnswerKeyAccessError):
        guarded_read(PSEUDONYM_DIR / "map.json")


def test_guarded_read_allows_corpus(tmp_path: Path) -> None:
    # a plain (non-sealed) file reads fine through the guard
    f = tmp_path / "circular.txt"
    f.write_text("pooled corpus text")
    assert guarded_read(f) == "pooled corpus text"


def test_rbi_added_to_allowlist_benchmark_only() -> None:
    from adapters.retrieval import is_allowed

    assert is_allowed("https://www.rbi.org.in/Scripts/BS_ViewMasterDirections.aspx")
    assert is_allowed("https://web.archive.org/web/2020/https://rbi.org.in/x")
    # a non-allowlisted host is still refused
    assert not is_allowed("https://example.com/x")
