# data/llm_cache/

Response cache for the B3 LLM layer (`distillcore/llm.py`). Every LLM call is keyed by
`(model, prompt_sha256)` and stored here as one JSON file per call. **Replay is the
default**: `make check` and every offline run read only from this cache and never touch
the network — the harness raises `CacheMiss` on a miss rather than silently calling live.

Files are committed so runs are reproducible from the cache alone. Live calls (which
populate the cache) require `--live` and `ANTHROPIC_API_KEY`; if the key is absent the
harness stops with `TODO(human): export ANTHROPIC_API_KEY` and does not improvise another
provider.

Each file: `{"model": ..., "prompt_sha256": ..., "response_text": ...}` — no timestamps,
so a same-cache re-run is byte-identical.
