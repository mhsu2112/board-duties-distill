# B3 checkpoint — TODO(human): export ANTHROPIC_API_KEY

**Raised:** 2026-07-02, after B3-T1. **Gate state:** `make check` green (148 passed).

## What's blocked

B3-T2 through B3-T6 are the LLM layer. Each needs **live** Claude calls to populate the
response cache under `data/llm_cache/`; once cached, `make check` replays them offline and
byte-identically. The cache is currently empty, so none of these can produce their
deliverables yet:

| Task | Needs live calls for |
|------|----------------------|
| B3-T2 Distill (as-built) | 50 distilled DutySpecs from cached source text |
| B3-T3 Intended layer | consolidated duty drafts for the 3 MVP clusters |
| B3-T4 Diagnose + classify | findings + effect classes across the 3 clusters |
| B3-T5 Render packages | (consumes T2–T4 output) |
| B3-T6 Eval | 3 live stability samples per stage on one cluster |

## Why this is a stop, not a workaround

`distillcore/llm.py` (B3-T1) is built to **stop** exactly here: a live call with no
`ANTHROPIC_API_KEY` raises `MissingApiKey` with this note and **does not substitute another
provider** (B3_TASKS §2; checkpoint §4). The environment currently has no key and no `ant`
profile. Per the standing rule I am not improvising around it.

## To unblock

Export a key, then run the B3-T2 live pass (which caches every call):

```bash
export ANTHROPIC_API_KEY=...        # or: ant auth login  (if the CLI is installed)
# then, once B3-T2's driver lands: boarddistill b3-distill --live
```

After the live pass, the cache is committed and all subsequent `make check` runs (and CI)
replay offline with no key. Only the *first* pass per prompt needs the network.

The harness is ready and tested (`tests/test_llm.py`): cache round-trip, replay-never-calls-live,
schema reject + retry-once, budget guard, missing-key stop. Distillation resumes at B3-T2
the moment a key is available.
