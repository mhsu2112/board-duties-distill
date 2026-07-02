"""B1-T5 — cache-replay regression: realification is idempotent from the committed cache,
and the committed fixtures rest on verbatim (non-paraphrase) primary-source text."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from adapters.realify import realify_fixture
from adapters.resolvers import build_resolver
from adapters.retrieval import Fetcher, offline_client

_FIXTURES = Path(__file__).resolve().parents[1] / "data" / "fixtures" / "us-gsib"
_CACHE = Path(__file__).resolve().parents[1] / "data" / "sources"
_DIRS = ["icfr", "sr12-17", "board-effectiveness", "_calculus"]


@pytest.mark.parametrize("name", _DIRS)
def test_committed_fixture_spans_are_verbatim(name: str) -> None:
    doc = json.loads((_FIXTURES / name / "sources.json").read_text())
    for src in doc["sources"]:
        quote = src["quote"]
        # no [FIXTURE] paraphrases survive; reform-lever spans stay [PLACEHOLDER]
        assert not quote.startswith("[FIXTURE]"), f"{name}/{src['id']} still a paraphrase"
        is_reform = "reform-lever" in src.get("source_id", "")
        if is_reform or src["citation"].startswith("[PLACEHOLDER]"):
            assert quote.startswith("[PLACEHOLDER]")


@pytest.mark.skipif(not _CACHE.exists(), reason="source cache absent")
@pytest.mark.parametrize("name", _DIRS)
def test_realify_is_idempotent_from_cache(tmp_path: Path, name: str) -> None:
    work = tmp_path / name
    shutil.copytree(_FIXTURES / name, work)
    resolver = build_resolver(Fetcher(_CACHE, offline_client()))

    first_changes = realify_fixture(work, resolver)
    after_first = (work / "sources.json").read_bytes()
    second_changes = realify_fixture(work, resolver)
    after_second = (work / "sources.json").read_bytes()

    # replaying against the same cache is byte-identical, and nothing regresses to unresolved
    assert after_first == after_second
    assert [c.status for c in first_changes] == [c.status for c in second_changes]
    assert all(c.status in {"realified", "kept_placeholder"} for c in second_changes)


@pytest.mark.skipif(not _CACHE.exists(), reason="source cache absent")
def test_realify_matches_committed_fixture(tmp_path: Path) -> None:
    # realifying a committed fixture from cache reproduces the committed sources.json
    work = tmp_path / "icfr"
    shutil.copytree(_FIXTURES / "icfr", work)
    resolver = build_resolver(Fetcher(_CACHE, offline_client()))
    realify_fixture(work, resolver)
    committed = (_FIXTURES / "icfr" / "sources.json").read_bytes()
    assert (work / "sources.json").read_bytes() == committed
