"""Lex-Balanus (banking) profile enums.

``PrimitiveOp`` is the closed, human-approved set (B0 §14; AGENTS §5) — **exactly 16
members in this order**. The derivation from the engine's set: RELATE_OFFENSE ->
RELATE_OBLIGATION, ASSIGN_MENS_REA -> ASSIGN_DUTY_PARAMETER (the approved
generalization over {verb_standard, cadence}; ASSIGN_DUTY_STANDARD is NOT a member),
plus the fifteenth-primitive residual DEEM_SATISFIED.
"""

from __future__ import annotations

from enum import StrEnum


class PrimitiveOp(StrEnum):
    """The 16-member banking calculus. The set changes only by the B0 checkpoint route."""

    MERGE = "MERGE"
    SPLIT = "SPLIT"
    INTRODUCE = "INTRODUCE"
    REPEAL = "REPEAL"
    RELOCATE = "RELOCATE"
    RELATE_OBLIGATION = "RELATE_OBLIGATION"
    CANONICALIZE_DEFINITION = "CANONICALIZE_DEFINITION"
    DEFINE_TERM = "DEFINE_TERM"
    SUBSTITUTE_TERM = "SUBSTITUTE_TERM"
    NORMALIZE_ELEMENTS = "NORMALIZE_ELEMENTS"
    ASSIGN_DUTY_PARAMETER = "ASSIGN_DUTY_PARAMETER"
    FACTOR_EXCEPTION = "FACTOR_EXCEPTION"
    REGRADE = "REGRADE"
    ELEVATE_GENERAL_RULE = "ELEVATE_GENERAL_RULE"
    RESOLVE_CROSS_REFERENCE = "RESOLVE_CROSS_REFERENCE"
    DEEM_SATISFIED = "DEEM_SATISFIED"


class RelationType(StrEnum):
    """Set iff ``primitive == RELATE_OBLIGATION`` (validated in T-CALCULUS)."""

    IMPLEMENTS = "implements"
    ELABORATES = "elaborates"
    PARALLEL_DISTINCT_PURPOSE = "parallel_distinct_purpose"
    ENTITY_LEVEL_MIRROR = "entity_level_mirror"
    SHARES_TERM = "shares_term"


class VerbStandard(StrEnum):
    """The board's standard of engagement with a duty's object.

    Also the value space of the ``verb_standard`` parameter of ASSIGN_DUTY_PARAMETER.
    """

    APPROVE = "approve"
    REVIEW_AND_CHALLENGE = "review_and_challenge"
    RECEIVE_REPORT = "receive_report"
    BE_INFORMED = "be_informed"
    CERTIFY = "certify"
    NONE_SPECIFIED = "none_specified"


class LegalForce(StrEnum):
    """The binding force / stratum of an instrument. Ordered by STRATUM_RANK below."""

    STATUTE = "statute"
    REGULATION = "regulation"
    ENFORCEABLE_GUIDELINE = "enforceable_guideline"
    GUIDANCE = "guidance"
    MANUAL = "manual"


class TreatmentStatus(StrEnum):
    """Currency of an instrument/duty as of a snapshot date."""

    ACTIVE = "active"
    AMENDED = "amended"
    SUPERSEDED = "superseded"
    RESCINDED_FORMAL = "rescinded_formal"
    RESCINDED_INFORMAL = "rescinded_informal"
    STALE_UNVERIFIED = "stale_unverified"


class NormativeKind(StrEnum):
    """Why a finding needs human judgment (the normative gate keys on non-empty sets)."""

    POLICY_CHOICE = "policy_choice"
    SUPERVISORY_VALUE_JUDGMENT = "supervisory_value_judgment"
    STATUTORY_CONSTRAINT = "statutory_constraint"
    INTERPRETIVE_AMBIGUITY = "interpretive_ambiguity"
    INSTITUTIONAL_DISCRETION = "institutional_discretion"
    INTERAGENCY_COORDINATION = "interagency_coordination"


class InstrumentRequired(StrEnum):
    """The lawful pathway a change must travel (APA pathway invariant, §2.11)."""

    RULE_APA = "rule_apa"
    JOINT_RULEMAKING = "joint_rulemaking"
    INTERAGENCY_STATEMENT = "interagency_statement"
    GUIDANCE_ACTION = "guidance_action"
    STATUTORY_AMENDMENT = "statutory_amendment"


class Consequence(StrEnum):
    """What attaches on failure of a duty (profile placeholder vocabulary)."""

    NONE_SPECIFIED = "none_specified"
    SUPERVISORY_FINDING = "supervisory_finding"
    ENFORCEMENT_ACTION = "enforcement_action"
    CERTIFICATION_REQUIRED = "certification_required"
    PUBLIC_DISCLOSURE = "public_disclosure"


class Cadence(StrEnum):
    """A duty's recurrence. Calendar vs fiscal basis is explicit so a basis change is
    a visible parameter re-assignment (D4)."""

    NONE_SPECIFIED = "none_specified"
    EVENT_DRIVEN = "event_driven"
    CONTINUOUS = "continuous"
    ANNUAL = "annual"
    ANNUAL_CALENDAR = "annual_calendar"
    ANNUAL_FISCAL = "annual_fiscal"
    SEMIANNUAL = "semiannual"
    QUARTERLY = "quarterly"


# Stratum ranking for baseline selection (higher wins).
STRATUM_RANK: dict[LegalForce, int] = {
    LegalForce.STATUTE: 5,
    LegalForce.REGULATION: 4,
    LegalForce.ENFORCEABLE_GUIDELINE: 3,
    LegalForce.GUIDANCE: 2,
    LegalForce.MANUAL: 1,
}

# Binding vs non-binding force (§2.9 force conservation; §2.11 APA pathway).
BINDING_FORCES: frozenset[LegalForce] = frozenset(
    {LegalForce.STATUTE, LegalForce.REGULATION, LegalForce.ENFORCEABLE_GUIDELINE}
)


def is_binding(force: LegalForce) -> bool:
    """True iff a duty at this force is legally binding (not mere guidance/manual)."""
    return force in BINDING_FORCES
