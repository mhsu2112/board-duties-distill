"""B1-T1 — allowlisted fetcher + content cache. The ONLY module that touches the network.

Enforces the B1_TASKS §3 allowlist in code (a non-allowlisted URL raises before any
request), caches every retrieved document under ``<cache_root>/<source_id>/`` with a
``manifest.json`` entry, and replays from cache without touching the network on a hit.
Verification must be auditable and replayable from the cache alone; a cache hit never
mutates the cache, so same-cache re-runs are byte-identical.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlparse

import httpx

# Primary-source allowlist (host suffixes). Anything else is a checkpoint (§3 / §6.3).
ALLOWLIST_SUFFIXES: frozenset[str] = frozenset(
    {
        "ecfr.gov",
        "govinfo.gov",
        "uscode.house.gov",
        "federalregister.gov",
        "federalreserve.gov",
        "occ.gov",
        "occ.treas.gov",
        "fdic.gov",
        "ffiec.gov",
        "sec.gov",
        "web.archive.org",
        "nyse.com",
        "listingcenter.nasdaq.com",
    }
)

_USER_AGENT = "BoardDistill-B1/0.1 (research; primary-source verification)"


class NotAllowedError(RuntimeError):
    """Raised when a URL is not on the B1 primary-source allowlist."""


def host_of(url: str) -> str:
    return (urlparse(url).hostname or "").lower()


def is_allowed(url: str) -> bool:
    host = host_of(url)
    return any(host == suffix or host.endswith("." + suffix) for suffix in ALLOWLIST_SUFFIXES)


def check_allowed(url: str) -> None:
    if not is_allowed(url):
        raise NotAllowedError(
            f"{url!r} is not on the B1 primary-source allowlist (§3); "
            "non-allowlisted / paywalled / CSI sources are a checkpoint (§6.3)."
        )


def _utc_now() -> datetime:
    return datetime.now(UTC)


def _url_key(url: str) -> str:
    return hashlib.sha256(url.encode("utf-8")).hexdigest()[:16]


@dataclass(frozen=True)
class CachedDocument:
    source_id: str
    url: str
    path: Path
    sha256: str
    title: str | None
    retrieved_at: str
    from_cache: bool
    text: str


def default_client(timeout: float = 30.0) -> httpx.Client:
    """A polite client for live use. Injected into ``Fetcher`` so tests can substitute."""
    return httpx.Client(
        timeout=timeout,
        follow_redirects=True,
        headers={"User-Agent": _USER_AGENT},
    )


@dataclass
class Fetcher:
    """Allowlisted, caching fetcher. Sequential and non-crawling by construction."""

    cache_root: Path
    client: httpx.Client
    clock: Callable[[], datetime] = _utc_now

    def _manifest_path(self, source_id: str) -> Path:
        return self.cache_root / source_id / "manifest.json"

    def _load_manifest(self, source_id: str) -> dict[str, dict[str, object]]:
        path = self._manifest_path(source_id)
        if not path.exists():
            return {}
        data = json.loads(path.read_text())
        entries: dict[str, dict[str, object]] = {e["url"]: e for e in data.get("entries", [])}
        return entries

    def _save_manifest(self, source_id: str, entries: dict[str, dict[str, object]]) -> None:
        path = self._manifest_path(source_id)
        ordered = sorted(entries.values(), key=lambda e: str(e["url"]))
        path.write_text(json.dumps({"entries": ordered}, indent=2, sort_keys=True) + "\n")

    def cached(self, url: str, source_id: str) -> CachedDocument | None:
        """Return the cached document for ``url`` if present, else None. No network."""
        entry = self._load_manifest(source_id).get(url)
        if entry is None:
            return None
        path = self.cache_root / source_id / str(entry["filename"])
        raw_title = entry.get("title")
        return CachedDocument(
            source_id=source_id,
            url=url,
            path=path,
            sha256=str(entry["sha256"]),
            title=None if raw_title is None else str(raw_title),
            retrieved_at=str(entry["retrieved_at"]),
            from_cache=True,
            text=path.read_text(),
        )

    def fetch(
        self,
        url: str,
        source_id: str,
        *,
        title: str | None = None,
        notes: str | None = None,
        force: bool = False,
    ) -> CachedDocument:
        """Fetch ``url`` into ``<cache_root>/<source_id>/``. Allowlist is checked first;
        a cache hit replays without touching the network (unless ``force``)."""
        check_allowed(url)

        if not force:
            hit = self.cached(url, source_id)
            if hit is not None:
                return hit

        response = self.client.get(url)
        response.raise_for_status()
        text = response.text
        sha = hashlib.sha256(text.encode("utf-8")).hexdigest()
        filename = f"{_url_key(url)}.html"

        src_dir = self.cache_root / source_id
        src_dir.mkdir(parents=True, exist_ok=True)
        (src_dir / filename).write_text(text)

        entries = self._load_manifest(source_id)
        retrieved_at = self.clock().isoformat()
        entries[url] = {
            "url": url,
            "retrieved_at": retrieved_at,
            "sha256": sha,
            "title": title,
            "notes": notes,
            "filename": filename,
        }
        self._save_manifest(source_id, entries)

        return CachedDocument(
            source_id=source_id,
            url=url,
            path=src_dir / filename,
            sha256=sha,
            title=title,
            retrieved_at=retrieved_at,
            from_cache=False,
            text=text,
        )
