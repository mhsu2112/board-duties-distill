SHARED PREAMBLE — prepended to every Lex-Balanus distillation/diagnosis/classification
prompt (B3_TASKS §2). Versioned as a file, never inlined. Two rules are stated here
verbatim; every template inherits them.

## Span-anchoring requirement (verbatim)

You may not assert any legal claim without a SourceSpan into the cached corpus. Every
field you populate that makes a legal assertion must quote the exact supporting text from
the source provided to you, and give the character offsets of that quote within that
source. If a claim cannot be tied to a verbatim quote from the source text in front of
you, you may not make the claim. Do not cite from memory. Do not cite a document you were
not given. A span that does not resolve to the provided cached text is a hallucinated
citation and a hard failure.

## Unresolved over guess (verbatim)

When the source text does not settle a field, mark that field `unresolved` — do not
guess, infer, or fill it from background knowledge. An honest `unresolved` is correct
output; a plausible-but-unsupported value is an error. Prefer leaving a field empty and
saying why over supplying a value the text does not support.

---
