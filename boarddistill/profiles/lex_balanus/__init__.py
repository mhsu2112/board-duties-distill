"""Lex-Balanus — the US GSIB banking profile (first fully-exercised profile).

## Held-out dials (NG1 analog — the R6 rule, codified B6-T0)

The calculus expresses the *move*, never the quantitative *value* the move carries. Threshold
values, chosen cadences, and other penalty-like dials are **held out** from the tool everywhere,
uniformly — surfaced to the human as ``policy_choice``, never set by the engine. This is the
profile analog of the engine's never-set-penalties rule (NG1); it was made explicit when the R6
third-party lever ("quantitative 'critical activity' threshold") decomposed cleanly into a
``DEFINE_TERM`` move whose *threshold value* the tool must not choose (see
``specs/B5_residual-closure.md``). ``HELD_OUT_DIALS`` names the categories.
"""

from __future__ import annotations

# Categories of quantitative value the calculus never sets — it expresses the operation that
# would carry the dial and routes the value to the human (policy_choice).
HELD_OUT_DIALS: tuple[str, ...] = (
    "threshold_value",  # e.g. the "critical activity" quantitative cutoff (R6)
    "chosen_cadence_value",  # the specific period a cadence is set to (vs. the ASSIGN move)
    "penalty_like_dial",  # any penalty/limit magnitude (the engine's NG1 category)
)
