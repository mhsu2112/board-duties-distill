DISTILL — as-built (B3-T2). Refine one draft board-duty spec against its verified source
excerpt. You return JSON only, matching the schema you were given.

The SOURCE EXCERPT below is the verbatim, already-verified text pinned for this duty. It is
your **only** evidence. Every value you assert must be supported by a verbatim substring of
this excerpt, which you return in the matching `*_evidence` / `quote` field. If the excerpt
does not settle a field, do not guess — set it to the `none_specified` / neutral value, add
its name to `unresolved_fields`, and leave its evidence empty.

## Duty under distillation

- duty_id: $duty_id
- draft label: $label
- cluster: $cluster
- instrument (context only, not evidence): $instrument
- draft verb_standard: $draft_verb
- draft object: $draft_object
- draft cadence: $draft_cadence

## SOURCE EXCERPT (your only evidence)

<<<
$source_excerpt
>>>

## What to return

- `duty_id`: echo `$duty_id` exactly.
- `verb_standard`: the board's action standard for this duty, chosen from: $verb_options.
  Pick the one the excerpt supports; if the excerpt states no board-action standard, use
  `none_specified`. Put the exact supporting substring in `verb_evidence` (empty if
  `none_specified`/unresolved).
- `object`: a precise, concise statement of what the duty is about (the object acted upon),
  grounded in the excerpt. Put the supporting substring in `object_evidence`.
- `cadence`: the timing standard, chosen from: $cadence_options. Put the supporting
  substring in `cadence_evidence`; use `none_specified` with empty evidence if the excerpt
  gives no timing.
- `definitions_used`: defined terms the duty relies on that appear in the excerpt — each a
  `{term, quote}` where `quote` is the verbatim defining/using text from the excerpt.
- `elements`: the intra-duty structure — each distinct sub-requirement the excerpt states,
  as `{text, quote}` with `quote` a verbatim substring.
- `unresolved_fields`: names of any of the above the excerpt does not settle.
- `notes`: brief reasoning (not a legal claim; not anchored).

Do not restate the draft as if it were the source. Refine only from the excerpt. Do not
introduce any actor, cadence, or requirement the excerpt does not contain.
