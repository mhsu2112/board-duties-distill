INTENDED — consolidated duty (B3-T3). Draft the **illustrative** consolidated duty
language for one B0 reform lever. You return JSON only, matching the schema you were given.

This is an intended-layer draft (NG2: **non-authoritative and illustrative**). It is NOT a
statement of current law and NOT a legal claim about any existing instrument — it is a
proposed consolidation of the operand duties below into one duty statement. Because it is
explicitly illustrative, the source-anchoring rule above is satisfied by **citing every
operand** you consolidate (the operands are your citations); you are not quoting a single
source excerpt. The unresolved-over-guess rule still binds: consolidate only what the
operands support, and do not invent scope, actors, or standards the lever does not describe.

## The reform lever

- decomposition: $dec_id
- cluster: $cluster
- lever (the consolidation to express): $lever
- instrument required (context): $instrument_required

## Operations composing this lever (scaffolded — do not re-derive)

$operations

## Operand duties to consolidate and cite (each is one of your citations)

$operands

## What to return

- `decomposition_id`: echo `$dec_id`.
- `label`: a short name for the consolidated duty (do not prepend any marker — the pipeline
  adds the illustrative tag).
- `object`: what the consolidated duty is about, in one clause.
- `consolidated_text`: the illustrative consolidated duty language — one coherent statement
  that expresses the lever over its operands. Keep it faithful to the operands; do not add
  requirements none of them contain.
- `operands_cited`: the list of operand identifiers you consolidated — **include every
  operand listed above**, verbatim. This is the citation set; omitting one is an error.
- `notes`: brief reasoning (not a claim).
