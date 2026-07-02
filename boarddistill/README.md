# BoardDistill

First deterministic vertical slice of the shared distillation engine, with the
**banking profile (Lex-Balanus)** as the first fully-exercised profile.

Slice one is **deterministic and fixtures-first**: no LLM, no network, no scraping.
See `AGENTS.md` for the build contract and `specs/` for the PRDs.

## Quickstart

```bash
uv sync          # create the venv, install deps
make check       # ruff + mypy --strict + pytest  (the gate)
```

## CLI

```bash
uv run boarddistill --help
```

The full "next steps" roadmap is written at task T9.
