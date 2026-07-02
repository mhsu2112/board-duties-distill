"""Lex-Allium (criminal) profile enums — STUB.

The engine's 14-member criminal calculus (engine AGENTS §5), present so the criminal
slice can land later without core changes. Not exercised in slice one.
"""

from __future__ import annotations

from enum import StrEnum


class PrimitiveOp(StrEnum):
    """The engine's 14 criminal primitives (contrast: banking generalizes two of
    these and adds DEEM_SATISFIED for 16)."""

    MERGE = "MERGE"
    SPLIT = "SPLIT"
    INTRODUCE = "INTRODUCE"
    REPEAL = "REPEAL"
    RELOCATE = "RELOCATE"
    RELATE_OFFENSE = "RELATE_OFFENSE"
    CANONICALIZE_DEFINITION = "CANONICALIZE_DEFINITION"
    DEFINE_TERM = "DEFINE_TERM"
    SUBSTITUTE_TERM = "SUBSTITUTE_TERM"
    NORMALIZE_ELEMENTS = "NORMALIZE_ELEMENTS"
    ASSIGN_MENS_REA = "ASSIGN_MENS_REA"
    FACTOR_EXCEPTION = "FACTOR_EXCEPTION"
    REGRADE = "REGRADE"
    ELEVATE_GENERAL_RULE = "ELEVATE_GENERAL_RULE"
    RESOLVE_CROSS_REFERENCE = "RESOLVE_CROSS_REFERENCE"


class RelationType(StrEnum):
    """Criminal relation vocabulary (set iff primitive == RELATE_OFFENSE)."""

    AGGRAVATED_FORM_OF = "aggravated_form_of"
    SHARES_TERM = "shares_term"
    MERGES_WITH = "merges_with"
