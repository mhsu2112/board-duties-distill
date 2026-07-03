DIAGNOSE — over the distilled as-built duties of one cluster (B3-T4). Propose diagnostics,
each anchored to a verbatim substring of the DUTIES block below. You return JSON only,
matching the schema you were given.

Look across the duties in this cluster and flag issues of these kinds only:

- `duplicate_duty`: two or more duties that state the same obligation (e.g. a binding-layer
  and a supervisory-layer statement of one requirement). `target_ids` = the duplicate duty
  ids.
- `rule_guidance_restatement`: a guidance/manual duty that restates a binding rule duty
  without adding an obligation. `target_ids` = [the guidance duty, the rule duty].
- `undefined_term`: the duty relies on a term that is used but not defined in its own text.
  `target_ids` = [the duty]; put the undefined term in the evidence quote.
- `actor_ambiguity`: the duty's text does not make clear which board body bears it (board vs
  a committee vs management). `target_ids` = [the duty].

For each diagnostic:
- `evidence_quote`: a verbatim substring copied from the DUTIES block that supports the
  flag. It must appear exactly in the text below.
- `normative_kind`: propose zero or more of the allowed kinds ($normative_kinds). These are
  *proposals* for human review; do not treat any as decided.
- `rationale`: one sentence.

Do not invent duties or terms not present below. If the cluster shows no issue of a kind,
return no diagnostic of that kind. An honest empty list is correct; a fabricated flag is an
error.

## Cluster

$cluster

## DUTIES (id · verb · object · excerpt — your only evidence)

$duties
