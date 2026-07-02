# FIXTURE_NOTES — dc/theft

Concrete placeholder data for AGENTS.md task **T3**. Schema-valid for the §5 models; also pins the shapes the AGENTS file left loose (gradations, defenses, definitions, id-referencing). The agent should make the Pydantic models accept these files unchanged.

## Status: openly placeholder
Per AGENTS §8, nothing here is authoritative unless real source text is present. Labeling convention inside `quote` fields:
- **`[PLACEHOLDER]`** — fabricated; not a real citation or quotation. There is exactly one such authority: `a-theft-consent-PLACEHOLDER` / `src-dca-theft-consent-PLACEHOLDER`, standing in for the controlling DCCA holding that supplies the consent/intent reading of current theft. Replace with a real cite at README next-step 1.
- **`[FIXTURE]`** — paraphrased/structural reconstruction, not verbatim source text.
- Unmarked quotes are short fragments drawn from public-domain sources (D.C. Code; the RCC § 22E-701 "property of another" definition).

## Real anchors used
- Current theft: D.C. Code § 22-3211 (conduct + intent to deprive); degrees § 22-3212.
- RCC: theft § 22E-2101; UUP carve-out § 22E-2102; "property of another" § 22E-701; merger § 22E-214; General Part culpability §§ 22E-205–207; robbery § 22E-1201; theft-from-a-person gradation § 22E-2101(d)(4)(B).
- Case law: Lattimore v. United States, 684 A.2d 357 (D.C. 1996) (real). The theft consent/intent holding is a PLACEHOLDER (I did not verify a specific cite).

## Snapshot dates (illustrative)
- `before_as_of` = 2020-01-01 (vintage of current law the RCC property-offense work analyzed).
- `reform_as_of` = 2021-03-24 (RCC Advisory Group approval — real date).
- `current_as_of` = 2026-06-11 (live-code reference; illustrative).
The as-built spec is the `before_as_of` law, not today's code — preserve this when real ingestion lands.

## Conventions the loader must honor
- **Source spans** live only in `sources.json` (`{"sources": [...]}`); everything else references them by id via `source_span_ids` / `source_citations` (list of span ids).
- **Cross-offense / authority targets** use the form `offense_id@layer:element_id` (e.g., `dc-theft@as_built:el-circ-consent`). `authority_graph.json` edges carry `source_span_id`.
- **Files** map to models: `as_built.json` and `intended.json` are single `OffenseSpec`s; `authority_graph.json` is an `AuthorityGraph`; `gold_findings.json` is `{"operations": [Operation...], "findings": [Finding...]}` so `Finding.operation_ids` resolve.
- **Shapes pinned here** (the AGENTS file left these loose): `Gradation{id, degree:int, criterion, source_span_ids}`; `Defense{id, kind: affirmative|justification|exception, text, source_span_ids}`; `Definition{term, text, canonical:bool, source_span_ids}`.

## What this fixture exercises (maps to required tests)
- An element (`el-circ-consent`) whose mens rea is `unresolved`/`implicit` in as-built → tests the "implicit mens rea" representation.
- A controlling, good-treatment holding bearing on that element → lets `classify` produce a baseline and label finding 1 `clarify` (not `unresolved`).
- Two gold findings whose operations are distinct primitives with distinct effect classes → the `effect_class != primitive` test, and the M0 composition check.
- Finding 1 carries `normative_kind=[doctrinal_ambiguity]`, finding 2 `[policy_choice]`, both `needs_review` → the normative-gate and final-status-blocker tests.

## Known fidelity caveat
Finding 2 (`MERGE`, effect `change`) matches the AGENTS §8 contract. It is framed as the RCC consolidating overlapping theft-related provisions and carving non-deprivation takings to UUP — a real, documented "change"-class move — rather than the §16 PRD wording ("fold false-pretense conduct into fraud"), which is less faithful to how the RCC actually structured theft/fraud/UUP. Confirm against the real CCRC theft report at README next-step 1.

## _calculus/relate_offense_case.json
Separate stub proving the 14th primitive: robbery and theft-from-a-person both survive, related by a single `RELATE_OFFENSE(aggravated_form_of)`, `expected_residual` empty. Used only by `test_calculus_theft.py`.
