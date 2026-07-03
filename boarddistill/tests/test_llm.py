"""B3-T1 — LLM harness: cache round-trip, replay-never-calls-live, schema-reject,
budget guard, missing-key stop, and template rendering. All offline (fake transport)."""

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import BaseModel, Field

from distillcore import llm
from distillcore.llm import (
    Budget,
    BudgetExceeded,
    CacheMiss,
    CompletionRequest,
    LlmHarness,
    MissingApiKey,
    RawCompletion,
    SchemaRejection,
    render,
    sanitize_json_schema,
)


class _Toy(BaseModel):
    verb: str
    cadence: str


class _Bounded(BaseModel):
    model_config = {"extra": "forbid"}
    confidence: float = Field(ge=0.0, le=1.0)
    note: str


def test_sanitize_strips_bounds_and_adds_additional_properties() -> None:
    san = sanitize_json_schema(_Bounded.model_json_schema())
    assert san["additionalProperties"] is False
    conf = san["properties"]["confidence"]
    assert "minimum" not in conf and "maximum" not in conf
    # Pydantic still enforces the bound client-side — the model is the real validator.
    with pytest.raises(ValueError):
        _Bounded(confidence=2.0, note="x")


def test_sanitize_recurses_into_nested_objects() -> None:
    schema = {
        "type": "object",
        "properties": {
            "inner": {
                "type": "object",
                "properties": {"n": {"type": "integer", "minimum": 0}},
            }
        },
    }
    san = sanitize_json_schema(schema)
    assert san["additionalProperties"] is False
    assert san["properties"]["inner"]["additionalProperties"] is False
    assert "minimum" not in san["properties"]["inner"]["properties"]["n"]


def _fake_transport(texts: list[str], calls: list[int]) -> object:
    """A transport that hands back ``texts`` in order and records how many times it ran."""

    remaining = list(texts)

    def _call(req: CompletionRequest) -> RawCompletion:
        calls[0] += 1
        text = remaining.pop(0)
        return RawCompletion(text=text, input_tokens=100, output_tokens=50)

    return _call


def _harness(tmp_path: Path, **kw: object) -> LlmHarness:
    return LlmHarness(cache_root=tmp_path / "cache", **kw)  # type: ignore[arg-type]


# --- replay never calls live (DoD) -----------------------------------------------------


def test_replay_miss_raises_never_calls_live(tmp_path: Path) -> None:
    h = _harness(tmp_path)  # live=False, empty cache
    with pytest.raises(CacheMiss):
        h.complete("some prompt", _Toy)


# --- cache round-trip ------------------------------------------------------------------


def test_cache_round_trip(tmp_path: Path) -> None:
    calls = [0]
    good = _Toy(verb="review", cadence="annual").model_dump_json()
    live = _harness(tmp_path, live=True, transport=_fake_transport([good], calls))

    first = live.complete("P", _Toy)
    assert first.verb == "review" and calls[0] == 1

    # A fresh replay-only harness on the same cache returns the same object, no call.
    replay = _harness(tmp_path)  # live=False, no transport
    second = replay.complete("P", _Toy)
    assert second == first
    assert (tmp_path / "cache").exists()


def test_cache_miss_on_model_change(tmp_path: Path) -> None:
    calls = [0]
    good = _Toy(verb="review", cadence="annual").model_dump_json()
    live = _harness(tmp_path, live=True, transport=_fake_transport([good], calls))
    live.complete("P", _Toy)

    # Same prompt + cache, different pinned model → a miss, not a stale hit.
    other = _harness(tmp_path, model="claude-sonnet-5")
    with pytest.raises(CacheMiss):
        other.complete("P", _Toy)


# --- schema reject: retry once, then hard-fail -----------------------------------------


def test_schema_reject_retries_once_then_succeeds(tmp_path: Path) -> None:
    calls = [0]
    good = _Toy(verb="review", cadence="annual").model_dump_json()
    live = _harness(tmp_path, live=True, transport=_fake_transport(['{"bad":1}', good], calls))
    obj = live.complete("P", _Toy)
    assert obj.verb == "review"
    assert calls[0] == 2  # one reject + one successful retry


def test_schema_reject_twice_hard_fails(tmp_path: Path) -> None:
    calls = [0]
    live = _harness(tmp_path, live=True, transport=_fake_transport(['{"bad":1}', "{}"], calls))
    with pytest.raises(SchemaRejection):
        live.complete("P", _Toy)
    assert calls[0] == 2
    # Nothing cached on a hard fail.
    assert not any((tmp_path / "cache").glob("*.json")) if (tmp_path / "cache").exists() else True


# --- budget guard ----------------------------------------------------------------------


def test_budget_call_cap(tmp_path: Path) -> None:
    calls = [0]
    bad = '{"bad":1}'
    live = _harness(
        tmp_path,
        live=True,
        transport=_fake_transport([bad, bad], calls),
        budget=Budget(max_calls=1, max_output_tokens=10_000),
    )
    # First attempt rejects; the retry would be call #2 → budget stops it before hard-fail.
    with pytest.raises(BudgetExceeded):
        live.complete("P", _Toy)
    assert calls[0] == 1


def test_budget_output_token_cap(tmp_path: Path) -> None:
    calls = [0]
    good = _Toy(verb="review", cadence="annual").model_dump_json()

    def _big(req: CompletionRequest) -> RawCompletion:
        calls[0] += 1
        return RawCompletion(text=good, input_tokens=10, output_tokens=100)

    live = _harness(
        tmp_path,
        live=True,
        transport=_big,
        budget=Budget(max_calls=5, max_output_tokens=50),
    )
    with pytest.raises(BudgetExceeded):
        live.complete("P", _Toy)


# --- missing-key stop ------------------------------------------------------------------


def test_missing_key_stops_with_todo(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    with pytest.raises(MissingApiKey) as exc:
        llm.anthropic_transport()
    assert "TODO(human): export ANTHROPIC_API_KEY" in str(exc.value)


def test_live_without_key_stops(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # live=True with no injected transport must build the live one → missing key stop.
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    h = _harness(tmp_path, live=True)
    with pytest.raises(MissingApiKey):
        h.complete("P", _Toy)


# --- templating: shared preamble carries the two verbatim rules ------------------------


def test_render_prepends_preamble_and_substitutes() -> None:
    out = render("Duty: $duty_id\nSource:\n$source", {"duty_id": "b:AUD-02", "source": "..."})
    assert "b:AUD-02" in out
    assert "span" in out.lower() and "unresolved" in out.lower()


def test_render_strict_on_missing_variable() -> None:
    with pytest.raises(KeyError):
        render("needs $missing", {})
