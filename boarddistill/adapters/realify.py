"""B1-T3 — replace fixture ``[FIXTURE]`` paraphrases with verified verbatim source text.

For each span in a fixture's ``sources.json``:
- ``[PLACEHOLDER]`` reform-lever spans are kept as-is (no source by design).
- ``[FIXTURE]`` paraphrases are resolved against primary sources; on ``verified`` the quote
  is replaced with the pinned verbatim text (now an unmarked, real quote).
- anything that does not verify is left unchanged and reported (checkpoint §6.4).

Deterministic and cache-replayable: given the committed cache, offline re-runs are no-ops.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from distillcore.pipeline.verify import SourceResolver

_QUOTE_CAP = 400


@dataclass(frozen=True)
class RealifyChange:
    span_id: str
    citation: str
    status: str  # "realified" | "kept_placeholder" | "already_verbatim" | "unresolved"
    note: str


def realify_fixture(fixture_dir: Path, resolver: SourceResolver) -> list[RealifyChange]:
    path = fixture_dir / "sources.json"
    doc = json.loads(path.read_text())
    changes: list[RealifyChange] = []
    for src in doc["sources"]:
        span_id = str(src["id"])
        citation = str(src.get("citation", ""))
        quote = str(src.get("quote") or "")
        # [PLACEHOLDER] reform-lever spans have no source by design — never touched.
        if quote.startswith("[PLACEHOLDER]"):
            changes.append(
                RealifyChange(span_id, citation, "kept_placeholder", "reform-lever span; no source")
            )
            continue

        # Idempotent: re-pin any resolvable span from its citation (picks up extraction fixes).
        verdict = resolver.verify(citation, expected_actor="")
        if verdict.status == "verified" and verdict.span is not None and verdict.span.quote:
            src["quote"] = verdict.span.quote[:_QUOTE_CAP].strip()
            changes.append(RealifyChange(span_id, citation, "realified", verdict.note))
        else:
            changes.append(RealifyChange(span_id, citation, "unresolved", verdict.note))

    path.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n")
    return changes
