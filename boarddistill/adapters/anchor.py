"""Fuzzy anchor matching: locate a duty's paraphrased text inside a source document.

Used when a citation points at a location inside a guidance document (SR-letter attachment,
manual) rather than an addressable provision. We slide a window over the document and score
each by how much of the duty's content vocabulary it contains; the best window is the
candidate span. High confidence => pin it; borderline => record candidates (checkpoint §3).
"""

from __future__ import annotations

import re

HIGH_CONFIDENCE = 0.60  # >= this share of the anchor's content words present => a match
CANDIDATE_FLOOR = 0.40  # between floor and high => borderline, present candidates, do not pick

_STOP_WORDS = (
    "the a an and or of to in for with that which shall should must be is are as by on its "
    "their board director directors this these those such any all not may will can from at"
)
_STOP = frozenset(_STOP_WORDS.split())


def content_words(text: str) -> frozenset[str]:
    return frozenset(w for w in re.findall(r"[a-z]{4,}", text.lower()) if w not in _STOP)


def anchor_match(
    anchor: str, text: str, *, window: int = 500, stride: int = 250
) -> tuple[float, str]:
    """Best (score, window-text) for ``anchor`` within ``text``. Score in [0, 1]."""
    wanted = content_words(anchor)
    if not wanted:
        return 0.0, ""
    best_score = 0.0
    best_window = ""
    for start in range(0, max(1, len(text)), stride):
        chunk = text[start : start + window]
        score = len(wanted & content_words(chunk)) / len(wanted)
        if score > best_score:
            best_score = score
            best_window = chunk
    return best_score, best_window
