"""B1-T4 — build the human-facing report, the review queue, and the status write-back.

Inputs: the ``verification.json`` from ``verify-live`` and the ``imported_duties.json``
drafts. Outputs: ``B1_report.md`` (per-row status + verified quote snippets + review
queue), ``review_queue.json`` (every non-verified row plus F2 / fidelity flags — the
TODO(human) list), and an updated ``imported_duties.json`` (claim ``verifier_status`` set
for the target rows; duty text never changed — §6.1).
"""

from __future__ import annotations

from collections import Counter
from typing import Any

_BINDING_HINTS = ("statute", "u.s.c", "cfr")  # a binding-cite row we'd expect board support in


def _by_duty(verification: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {r["duty_id"]: r for r in verification["rows"]}


def _spans_by_citation(verification: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {s["citation"]: s for s in verification.get("spans", [])}


def build_review_queue(verification: dict[str, Any]) -> dict[str, Any]:
    """Every row a human must accept or fix: non-verified rows, plus verified rows with a
    weak/absent board-support signal (F2) or a fidelity caveat (section-level / cover-letter)."""
    queue: list[dict[str, Any]] = []
    for row in sorted(verification["rows"], key=lambda r: r["duty_id"]):
        status = row["status"]
        note = row["note"]
        if status in ("contradicted", "unverified"):
            queue.append({**_row_ref(row), "kind": status, "reason": note})
            continue
        # verified — surface F2 and fidelity caveats for human confirmation
        if row.get("support_signal") in ("none", "weak"):
            queue.append(
                {
                    **_row_ref(row),
                    "kind": "f2_support",
                    "reason": f"citation verified but board support is {row['support_signal']}",
                }
            )
        elif "U.S. Code" in note or "cover-letter" in note:
            queue.append({**_row_ref(row), "kind": "fidelity_caveat", "reason": note})
    counts = Counter(item["kind"] for item in queue)
    return {
        "_meta": "B1 review queue — TODO(human). Non-verified rows + F2/fidelity flags. "
        "The agent records these; it never edits the inventory, drafts, or B0 to match (§6.1).",
        "counts": dict(sorted(counts.items())),
        "queue": queue,
    }


def _row_ref(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "duty_id": row["duty_id"],
        "cluster": row["cluster"],
        "citation": row["citation"],
        "status": row["status"],
        "support_signal": row.get("support_signal"),
    }


def apply_statuses_to_import(
    import_doc: dict[str, Any], verification: dict[str, Any]
) -> dict[str, Any]:
    """Set each target row's claim ``verifier_status`` from the verification. Duty text is
    never touched (§6.1). Non-target rows keep ``unverified``."""
    status_by_duty = {r["duty_id"]: r["status"] for r in verification["rows"]}
    for duty in import_doc["duties"]:
        status = status_by_duty.get(duty["duty_id"])
        if status is None:
            continue
        for claim in duty.get("claims", []):
            claim["verifier_status"] = status
    import_doc["_banner"] = (
        "DRAFT imported from the inventory xlsx. Claims in the 5 B1 target clusters carry a "
        "verifier_status set by B1 verification (verified/contradicted/unverified); all other "
        "rows remain unverified. Duty text is unchanged. See outputs/b1/B1_report.md."
    )
    return import_doc


def _table(headers: list[str], rows: list[list[str]]) -> str:
    line = "| " + " | ".join(headers) + " |"
    sep = "| " + " | ".join("---" for _ in headers) + " |"
    body = ["| " + " | ".join(r) + " |" for r in rows]
    return "\n".join([line, sep, *body])


def _clip(text: str, n: int) -> str:
    text = " ".join(text.split())
    return text if len(text) <= n else text[: n - 1] + "…"


def build_report(verification: dict[str, Any]) -> str:
    rows = sorted(verification["rows"], key=lambda r: r["duty_id"])
    spans = _spans_by_citation(verification)
    summary = verification.get("summary", {})

    by_cluster: dict[str, Counter[str]] = {}
    for r in rows:
        by_cluster.setdefault(r["cluster"] or "—", Counter())[r["status"]] += 1

    parts: list[str] = ["# B1 verification report\n"]
    parts.append(
        "Full-coverage citation verification of the 72 MVP-cluster board-duty rows against "
        "primary sources (eCFR, govinfo U.S. Code, federalreserve.gov SR letters). "
        "Retrieval is allowlisted and cache-replayable; unreachable => unverified.\n"
    )

    parts.append("## Summary\n")
    parts.append(
        f"- rows: {len(rows)} · "
        + " · ".join(f"{k}: {v}" for k, v in sorted(summary.items()))
        + "\n"
    )
    cluster_rows = [
        [
            cluster,
            str(counts.get("verified", 0)),
            str(counts.get("contradicted", 0)),
            str(counts.get("unverified", 0)),
        ]
        for cluster, counts in sorted(by_cluster.items())
    ]
    parts.append(_table(["cluster", "verified", "contradicted", "unverified"], cluster_rows) + "\n")

    parts.append("## Per-row status\n")
    status_rows = [
        [
            r["duty_id"],
            r["status"],
            "yes" if r.get("as_of_valid") else "no",
            str(r.get("support_signal")),
            _clip(r["citation"], 34),
            _clip(r["note"], 60),
        ]
        for r in rows
    ]
    parts.append(
        _table(["duty", "status", "in_force", "support", "citation", "note"], status_rows) + "\n"
    )

    parts.append("## Verified provisions (verbatim snippets)\n")
    verified = [r for r in rows if r["status"] == "verified"]
    for r in verified:
        span = spans.get(_best_span_citation(r["citation"], spans))
        quote = _clip(span["quote"], 240) if span else "(quote unavailable)"
        parts.append(f"- **{r['duty_id']}** — {r['citation']}\n  > {quote}\n")

    parts.append("## Review queue (accept / fix — TODO(human))\n")
    queue = build_review_queue(verification)
    parts.append("Counts: " + ", ".join(f"{k}={v}" for k, v in queue["counts"].items()) + "\n")
    queue_rows = [
        [item["duty_id"], item["kind"], _clip(item["citation"], 34), _clip(item["reason"], 66)]
        for item in queue["queue"]
    ]
    parts.append(_table(["duty", "kind", "citation", "reason"], queue_rows) + "\n")

    parts.append("## Methodology & caveats\n")
    parts.append(
        "- **Allowlist only** (primary sources); secondary sources are never cited as evidence.\n"
        "- **support_signal** is a keyword heuristic (does the provision text name the stated "
        "board actor) surfaced for human F2 confirmation — it is not a machine legal claim.\n"
        "- **U.S. Code** quotes are section-level: the govinfo HTML granule is not "
        "paragraph-addressable, so a `(b)` sub-cite pins the whole section (§6.4).\n"
        "- **SR letters**: numbered attributes live in separate attachments; the cover-letter "
        "text (after `SUBJECT:`) is pinned, not the attribute-specific body (§6.4).\n"
        "- **Guidance-document citations** (SR-letter attachments, exam-manual components, local "
        "line numbers) are `unverified` by construction — they cite guidance locations, not "
        "addressable primary law. This is itself a sludge signal.\n"
    )
    return "\n".join(parts)


def _best_span_citation(citation: str, spans: dict[str, dict[str, Any]]) -> str:
    if citation in spans:
        return citation
    for cite in spans:
        if cite and cite in citation:
            return cite
    return citation
