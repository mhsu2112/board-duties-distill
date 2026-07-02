"""B1-T1 — allowlist enforcement + record/replay cache, all offline via a fake transport."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import httpx
import pytest

from adapters.retrieval import (
    Fetcher,
    NotAllowedError,
    check_allowed,
    is_allowed,
)

_URL = "https://www.ecfr.gov/current/title-12/part-363/section-363.2"
_FIXED_CLOCK = lambda: datetime(2026, 7, 2, 12, 0, tzinfo=UTC)  # noqa: E731


def _recording_client(body: str, calls: list[str]) -> httpx.Client:
    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(str(request.url))
        return httpx.Response(200, text=body)

    return httpx.Client(transport=httpx.MockTransport(handler))


def _offline_client() -> httpx.Client:
    def handler(request: httpx.Request) -> httpx.Response:
        raise AssertionError(f"network hit on replay: {request.url}")

    return httpx.Client(transport=httpx.MockTransport(handler))


# ---- allowlist ---------------------------------------------------------------------


def test_allowlist_accepts_primary_sources_and_subdomains() -> None:
    assert is_allowed("https://ecfr.gov/x")
    assert is_allowed("https://www.ecfr.gov/x")
    assert is_allowed("https://occ.treas.gov/x")
    assert is_allowed("https://web.archive.org/web/2020/https://sr.gov")
    assert is_allowed("https://listingcenter.nasdaq.com/rulebook")


def test_allowlist_rejects_others_and_lookalikes() -> None:
    assert not is_allowed("https://evil.example.com/x")
    assert not is_allowed("https://ecfr.gov.evil.com/x")  # suffix spoof
    assert not is_allowed("https://en.wikipedia.org/wiki/SOX")
    with pytest.raises(NotAllowedError):
        check_allowed("https://evil.example.com/x")


def test_fetch_rejects_non_allowlisted_url_without_network_or_cache(tmp_path: Path) -> None:
    calls: list[str] = []
    fetcher = Fetcher(tmp_path, _recording_client("x", calls), clock=_FIXED_CLOCK)
    with pytest.raises(NotAllowedError):
        fetcher.fetch("https://evil.example.com/x", "evil")
    assert calls == []  # never hit the network
    assert not (tmp_path / "evil").exists()  # never wrote a cache dir


# ---- record / replay ---------------------------------------------------------------


def test_record_then_replay_is_offline_and_byte_identical(tmp_path: Path) -> None:
    body = "<html><body>12 CFR 363.2(b) text</body></html>"
    calls: list[str] = []
    rec = Fetcher(tmp_path, _recording_client(body, calls), clock=_FIXED_CLOCK)

    first = rec.fetch(_URL, "part-363", title="Part 363")
    assert first.from_cache is False
    assert first.text == body
    assert calls == [_URL]

    manifest_path = tmp_path / "part-363" / "manifest.json"
    manifest_bytes = manifest_path.read_bytes()

    # replay with an offline client — must not touch the network
    rep = Fetcher(tmp_path, _offline_client(), clock=_FIXED_CLOCK)
    second = rep.fetch(_URL, "part-363", title="Part 363")
    assert second.from_cache is True
    assert second.text == body
    assert second.sha256 == first.sha256
    # a cache hit never mutates the cache
    assert manifest_path.read_bytes() == manifest_bytes


def test_manifest_records_required_fields(tmp_path: Path) -> None:
    import json

    calls: list[str] = []
    fetcher = Fetcher(tmp_path, _recording_client("hello", calls), clock=_FIXED_CLOCK)
    doc = fetcher.fetch(_URL, "part-363", title="Part 363", notes="section 363.2(b)")

    manifest = json.loads((tmp_path / "part-363" / "manifest.json").read_text())
    entry = manifest["entries"][0]
    assert entry["url"] == _URL
    assert entry["title"] == "Part 363"
    assert entry["notes"] == "section 363.2(b)"
    assert entry["retrieved_at"] == "2026-07-02T12:00:00+00:00"
    assert entry["sha256"] == doc.sha256
    assert (tmp_path / "part-363" / entry["filename"]).exists()


def test_force_refetches_and_updates_cache(tmp_path: Path) -> None:
    calls: list[str] = []
    fetcher = Fetcher(tmp_path, _recording_client("v1", calls), clock=_FIXED_CLOCK)
    fetcher.fetch(_URL, "part-363")
    assert len(calls) == 1
    fetcher.fetch(_URL, "part-363")  # cache hit
    assert len(calls) == 1
    fetcher.fetch(_URL, "part-363", force=True)  # forced re-fetch
    assert len(calls) == 2


def test_cached_returns_none_when_absent(tmp_path: Path) -> None:
    fetcher = Fetcher(tmp_path, _offline_client(), clock=_FIXED_CLOCK)
    assert fetcher.cached(_URL, "part-363") is None


@pytest.mark.live
def test_live_fetch_real_allowlisted_source(tmp_path: Path) -> None:
    from adapters.retrieval import default_client

    with default_client() as client:
        fetcher = Fetcher(tmp_path, client)
        doc = fetcher.fetch(
            "https://www.ecfr.gov/current/title-12/chapter-III/subchapter-B/part-363",
            "part-363",
            title="12 CFR Part 363",
        )
    assert doc.from_cache is False
    assert len(doc.text) > 0
