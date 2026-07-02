"""Minimal HTML → text extraction (stdlib only) for SR letters and U.S.C. granules."""

from __future__ import annotations

import re
from html.parser import HTMLParser

_WS = re.compile(r"\s+")
_SKIP = {"script", "style", "head", "nav", "footer"}


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []
        self._skip = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in _SKIP:
            self._skip += 1

    def handle_endtag(self, tag: str) -> None:
        if tag in _SKIP and self._skip:
            self._skip -= 1

    def handle_data(self, data: str) -> None:
        if not self._skip and data.strip():
            self.parts.append(data)


def html_to_text(html: str) -> str:
    parser = _TextExtractor()
    parser.feed(html)
    return _WS.sub(" ", " ".join(parser.parts)).strip()
