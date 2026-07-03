DECOMPOSE — express one reform lever as a composition of calculus primitives (B5-T4). You
return JSON only, matching the schema you were given. You are proposing structure; a human
approves it. The point is a closure test: does the fixed 16-primitive set express this lever?

## The 16 primitives (the ONLY allowed operations)

MERGE, SPLIT, INTRODUCE, REPEAL, RELOCATE, RELATE_OBLIGATION, CANONICALIZE_DEFINITION,
DEFINE_TERM, SUBSTITUTE_TERM, NORMALIZE_ELEMENTS, ASSIGN_DUTY_PARAMETER, FACTOR_EXCEPTION,
REGRADE, ELEVATE_GENERAL_RULE, RESOLVE_CROSS_REFERENCE, DEEM_SATISFIED

Rules the schema enforces (respect them or the composition is invalid):
- `relation` is set IF AND ONLY IF `primitive` is `RELATE_OBLIGATION` (one of: implements,
  elaborates, parallel_distinct_purpose, entity_level_mirror, shares_term).
- `satisfied_ref` + `satisfying_ref` + non-empty `conditions` are set IF AND ONLY IF
  `primitive` is `DEEM_SATISFIED`. Both refs must name duties that SURVIVE (deem ≠ merge).
- `parameter` (verb_standard | cadence) is set IF AND ONLY IF `primitive` is
  `ASSIGN_DUTY_PARAMETER`.

## The 4 named composites (a multi-op lever MUST match one of these, by primitive set)

- `consolidation` = MERGE + CANONICALIZE_DEFINITION + RESOLVE_CROSS_REFERENCE
- `master_direction_build` = INTRODUCE(general_part) + MERGE + REPEAL + RESOLVE_CROSS_REFERENCE
- `board_role_clarification` = ASSIGN_DUTY_PARAMETER + SPLIT
- `vertical_rationalization` = RELATE_OBLIGATION(entity_level_mirror) + DEEM_SATISFIED + FACTOR_EXCEPTION

## How to answer

Set `composition` to exactly one of these SEVEN values (never any other string, never "empty"):
- `single` — the lever is ONE primitive. Return exactly one operation.
- one of the four composite names above — the lever is that bundle. Return exactly its primitives.
- `residual` — the lever CANNOT be expressed as one primitive or one of the four composites.
  Do NOT invent a new primitive or composite. Set `residual_reason` to what structure is
  missing. A residual is a legitimate finding, not a failure — be honest.
- `non_target` — the lever is a "retain / coordinate / clarify / confirm / documented" action
  that is NOT a structural consolidation (no primitive applies). Set `is_consolidation` false and
  return NO operations. Use this for pure-coordination or "keep as-is" levers.

Whenever `composition` is `single` or a composite name you MUST return at least one operation
(the primitive(s)). Returning `single` with no operations is invalid. If a lever is bare
cross-referencing ("cross-reference the manual to the rule"), that IS one `RESOLVE_CROSS_REFERENCE`
operation — return it, do not leave operations empty.

Guidance on common shapes (map, don't force):
- "cross-reference the manual to the rule; stop restating" → `RESOLVE_CROSS_REFERENCE` (single).
- "permit X to satisfy Y by cross-reference / deem" → `DEEM_SATISFIED` (single; both survive).
- "one enterprise program approval; fold parallel appendices" → `MERGE` (single) or `consolidation`.
- "single/uniform definition across regimes" → `CANONICALIZE_DEFINITION` (single).
- "fold duty into the risk-appetite approval" → `ELEVATE_GENERAL_RULE` (single).
- "coordinate/align parallel processes (kept distinct)" → `RELATE_OBLIGATION(parallel_distinct_purpose)`.
- "quantitative threshold for board attention" → `ASSIGN_DUTY_PARAMETER` or `FACTOR_EXCEPTION`.
- "expanded reliance so the bank board relies on the parent" → `vertical_rationalization`.
- "retain; distinct purpose / not a consolidation target" → set `is_consolidation` false, no ops.

Also return:
- `actor_with_authority`: the agencies that can act (e.g. FRB, OCC, FDIC, SEC, Congress, FinCEN).
- `instrument_required`: one of rule_apa, joint_rulemaking, interagency_statement, guidance_action,
  statutory_amendment — the lawful pathway. A binding change needs a rule/statute, not guidance.
- `normative_kinds`: zero or more of $normative_kinds (proposals for human review).
- `statutory_floor_candidates`: any statute this lever touches that should be PROPOSED (not added)
  to the statutory floor — e.g. GLBA §501(b), DFA §956, 12 U.S.C. 371c/375b, FDI Act §36. List the
  citation strings; a human owns the floor file.
- `operands`: short concept labels for what each operation acts on (duty ids or concept names).

## The lever

lever_id: $lever_id
cluster: $cluster
minimum reform lever: $min_reform_lever
what is duplicative: $whats_duplicative
what is legally distinct: $whats_distinct
overlapping sources: $overlapping_sources
roadmap (actor / authority / instrument / statutory obstacle): $roadmap
