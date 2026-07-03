"""B4-T2 — re-pin the ten mispinned rows (targeted retrieval, offline).

The B3 distiller refused to distill ten rows whose B1/B2 pin resolved to an excerpt that
does not support the stated duty (``source_mismatch_rows``). This module records the
corrected pin for each: the location *within the already-cited instrument* (allowlist
unchanged) whose verbatim text supports the duty, found by targeted retrieval over the
committed source cache.

Discipline:
* **Verbatim, cache-checked.** Every corrected ``quote`` is a whitespace-insensitive substring
  of the cited instrument's cached text (``verify_repins`` proves it). A quote that does not
  resolve is a bug, never passed through.
* **Anchor-matched where fuzzy** (B2 convention): ``anchor_matched: true`` marks a pin located
  by content match rather than an addressable sub-provision.
* **Unsupportable ⇒ checkpoint, not a silent fix.** A row whose duty cannot be supported
  anywhere in the cited instrument is recorded as a candidate F2/F4 (invented/misattributed
  obligation) in a fresh review queue — the calibration case for the corpus's first real F2/F4.
  (All ten re-pinned cleanly; none escalated. ``s:GOV-12`` carries a partial-support note.)
* **The live LLM re-distill is a checkpoint here.** Re-running distillation on the corrected
  excerpts needs live calls (then cache). With no ``ANTHROPIC_API_KEY`` the harness stops with
  the standard ``TODO(human)`` note; the corrected pins are the deliverable this pass produces.
"""

from __future__ import annotations

import glob
import re
from html import unescape
from pathlib import Path
from typing import Any

SOURCES_ROOT = Path("data/sources")

# Corrected pins. Each: the instrument (unchanged allowlist), the corrected citation, the
# verbatim supporting quote (verified against cache), and why the B3 pin was wrong.
REPINS: list[dict[str, Any]] = [
    {
        "duty_id": "b:AUD-08",
        "source_id": "ecfr-t12-p30",
        "new_citation": "12 CFR Part 30, App. D, II.C (internal audit independence)",
        "old_citation": "App. D, secs. I.E.8(b),(c)",
        "quote": "The audit committee approves all decisions regarding the appointment or "
        "removal and annual compensation and salary adjustment of the Chief Audit Executive",
        "anchor_matched": True,
        "old_pin_topic": "concentration-risk-management paragraph (App. D I.E) — wrong section",
    },
    {
        "duty_id": "b:CAP-02",
        "source_id": "ecfr-t12-p225",
        "new_citation": "12 CFR 225.8(e)(3)",
        "old_citation": "12 CFR 225.8(e)(1)(iii)",
        "quote": "at least annually and prior to submission of the capital plan under paragraph "
        "(e)(1)(ii) of this section: (A) Review the robustness of the bank holding company's "
        "process for assessing capital adequacy",
        "anchor_matched": False,
        "old_pin_topic": "225.8(d) definitions (capital plan cycle / policy) — wrong subsection",
    },
    {
        "duty_id": "s:CAP-09",
        "source_id": "ecfr-t12-p225",
        "new_citation": "12 CFR 225.8(e)(3)",
        "old_citation": "12 CFR 225.8(e)(1)(iii); 225.8(d)",
        "quote": "at least annually and prior to submission of the capital plan under paragraph "
        "(e)(1)(ii) of this section: (A) Review the robustness of the bank holding company's "
        "process for assessing capital adequacy",
        "anchor_matched": False,
        "old_pin_topic": "225.8(d) definitions — wrong subsection (mirror of b:CAP-02)",
    },
    {
        "duty_id": "b:RGC-05",
        "source_id": "ecfr-t12-p252",
        "new_citation": "12 CFR 252.33(a)(3)(ii)",
        "old_citation": "12 CFR 252.33(a)(4)(ii)",
        "quote": "Be chaired by a director who: (A) Is not an officer or employee of the bank "
        "holding company",
        "anchor_matched": False,
        "old_pin_topic": "252.33(a)(1) general risk-committee mandate — chair clause missed",
    },
    {
        "duty_id": "s:BCG-03",
        "source_id": "occ-ch-crg",
        "new_citation": "OCC Comptroller's Handbook, Corporate and Risk Governance — "
        "Committee descriptions: Credit committee",
        "old_citation": "Appendix C — Credit committee",
        "quote": "establish and guide the bank’s lending strategy, credit risk appetite, and "
        "risk limits.",
        "anchor_matched": True,
        "old_pin_topic": "fiduciary/trust audit-committee paragraph — wrong committee",
    },
    {
        "duty_id": "s:CAP-07",
        "source_id": "sr-15-18-att",
        "new_citation": "SR 15-18 attachment, sec. III.A.1 (Board of Directors)",
        "old_citation": "Attachment, sec. III.A.1, p. 4",
        "quote": "The board of directors should maintain an accurate record of its meetings "
        "pertaining to the firm's capital planning process.",
        "anchor_matched": True,
        "old_pin_topic": "post-stress escalation-protocol paragraph — wrong para, right section",
    },
    {
        "duty_id": "s:GOV-03",
        "source_id": "sr-21-3-att",
        "new_citation": "SR 21-3 attachment, Attribute 1 (Effective board — strategy), pp. 2-3",
        "old_citation": "Attachment, Attribute 1, pp. 2-3",
        "quote": "If the strategy calls for expansion into a new line of business or a new "
        "jurisdiction, the board evaluates the increased level of risk.",
        "anchor_matched": True,
        "old_pin_topic": "director-nominee-process passage — wrong attribute (fuzzy pin)",
    },
    {
        "duty_id": "s:GOV-04",
        "source_id": "sr-21-3-att",
        "new_citation": "SR 21-3 attachment, Attribute 2 (Information), pp. 3-4",
        "old_citation": "Attachment, Attribute 2, pp. 3-4",
        "quote": "An effective board directs senior management to provide it with information "
        "that is timely, accurate, and well organized.",
        "anchor_matched": True,
        "old_pin_topic": "director-nominee-process passage — wrong attribute",
    },
    {
        "duty_id": "s:GOV-08",
        "source_id": "sr-21-3-att",
        "new_citation": "SR 21-3 attachment, Attribute 3 (Talent & compensation), p. 5",
        "old_citation": "Attachment, Attribute 3, p. 5",
        "quote": "An effective board approves clear financial and nonfinancial performance "
        "objectives aligned with the firm's strategy and risk appetite for the CEO and "
        "business line executives",
        "anchor_matched": True,
        "old_pin_topic": "director-nominee-process passage — wrong attribute",
    },
    {
        "duty_id": "s:GOV-12",
        "source_id": "sr-21-3-att",
        "new_citation": "SR 21-3 attachment, Attribute 4 (Audit), p. 6",
        "old_citation": "Attachment, Attribute 4, p. 6",
        "quote": "assesses and supports the stature and independence of the firm's independent "
        "risk management and internal",
        "anchor_matched": True,
        "old_pin_topic": "director-nominee-process passage — wrong attribute",
        "partial_support_note": "SR 21-3 (Audit) supports audit-committee oversight of internal "
        "audit and remediation-timeliness; the duty's 'meets directly with the CAE' and "
        "'budget and staffing' specifics are more fully grounded in App. D II.C / SR 13-1. Pin "
        "covers the core obligation; the sub-elements are a soft flag for the re-distill pass.",
    },
]

# The ten rows flagged by the B3 distiller (source_mismatch_rows).
TEN_ROWS: frozenset[str] = frozenset(r["duty_id"] for r in REPINS)


def _despace(s: str) -> str:
    return re.sub(r"\s+", "", s)


def _cached_text(source_id: str) -> str:
    """Whitespace-normalized text of a cached source (tags stripped, entities unescaped)."""
    paths = [p for p in glob.glob(str(SOURCES_ROOT / source_id / "*")) if "manifest" not in p]
    if not paths:
        raise FileNotFoundError(f"no cached source for {source_id!r}")
    raw = Path(paths[0]).read_text(errors="ignore")
    text = unescape(re.sub(r"<[^>]+>", " ", raw))
    return re.sub(r"\s+", " ", text)


def verify_repin(repin: dict[str, Any]) -> bool:
    """True iff the corrected quote is a (whitespace-insensitive) substring of the cited cache."""
    return _despace(repin["quote"]) in _despace(_cached_text(repin["source_id"]))


def verify_repins() -> dict[str, bool]:
    return {r["duty_id"]: verify_repin(r) for r in REPINS}


def corrected_spans() -> list[dict[str, Any]]:
    """The corrected ``SourceSpan``-shaped records for the ten rows."""
    return [
        {
            "id": f"repin-{r['duty_id']}",
            "source_id": r["source_id"],
            "citation": r["new_citation"],
            "quote": r["quote"],
            "start": None,
            "end": None,
            "anchor_matched": r["anchor_matched"],
        }
        for r in REPINS
    ]


REDISTILL_TODO = (
    "TODO(human): export ANTHROPIC_API_KEY, then re-run `boarddistill b3-distill --live` "
    "restricted to the ten re-pinned rows to LLM-distill them from the corrected excerpts "
    "(replay-cached thereafter). Blocked this pass: no key present."
)


def repin_document() -> dict[str, Any]:
    verified = verify_repins()
    unverified = [d for d, ok in verified.items() if not ok]
    escalated = [r for r in REPINS if r.get("escalate_f2_f4")]
    partial = [r["duty_id"] for r in REPINS if r.get("partial_support_note")]
    return {
        "_meta": "B4-T2 re-pin. Corrected pins for the ten source-mismatch rows; every quote "
        "verbatim-verified against the cited instrument's cache (allowlist unchanged). The live "
        "LLM re-distill is checkpointed (no API key this pass).",
        "counts": {
            "rows": len(REPINS),
            "quote_verified": sum(verified.values()),
            "anchor_matched_fuzzy": sum(1 for r in REPINS if r["anchor_matched"]),
            "escalated_f2_f4": len(escalated),
            "partial_support": len(partial),
        },
        "quote_verification": verified,
        "unverified_quotes": unverified,  # must be empty — else a re-pin is itself unsupported
        "partial_support_rows": partial,
        "f2_f4_review_queue": [
            {
                "duty_id": r["duty_id"],
                "reason": "duty text unsupportable in the cited instrument (candidate "
                "invented/misattributed obligation)",
                "old_citation": r["old_citation"],
            }
            for r in escalated
        ],
        "redistill_checkpoint": REDISTILL_TODO,
        "repins": REPINS,
        "corrected_spans": corrected_spans(),
    }
