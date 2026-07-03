"""B3-T1 — the LLM harness. The only module that calls an LLM, behind the interfaces
slice one proved.

Contract (B3_TASKS §2):

* **Pinned model in one constant** (``PINNED_MODEL``). Determinism for the gate comes from
  the response cache, not from sampling params: Opus 4.8 rejects ``temperature`` (400), so
  the §2 "temperature 0" intent is honoured by *not sampling twice on the same key* — every
  ``(model, prompt_sha256)`` maps to exactly one cached response, replayed byte-identically.
* **Structured output** validated against a caller-supplied Pydantic schema, with
  **reject-and-retry once** on schema failure, then hard-fail (``SchemaRejection``).
* **Response cache** under ``data/llm_cache/`` keyed by ``(model, prompt_sha256)``. Replay is
  the default; a miss in replay mode raises ``CacheMiss`` — the harness never silently calls
  live. ``make check`` runs entirely from cache, no keys needed.
* **Live** requires ``live=True`` and ``ANTHROPIC_API_KEY``. If the key is absent the harness
  stops with the exact ``TODO(human)`` note (``MissingApiKey``) and does not improvise another
  provider.
* **Budget guard** (max calls, max output tokens) with a visible counter in the run log.

Prompt *templates* live in ``profiles/lex_balanus/prompts/`` as versioned files, each
inheriting the shared preamble (span-anchoring + unresolved-over-guess, verbatim). Rendering
lives in :func:`render`; the harness itself is prompt-in, validated-object-out.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from string import Template
from typing import Any, TypeVar

from pydantic import BaseModel, ValidationError

logger = logging.getLogger("boarddistill.llm")

# --- Pinned configuration (single source) ----------------------------------------------

PINNED_MODEL = "claude-opus-4-8"

# A short role-setter; the load-bearing rules (anchoring, unresolved-over-guess) ride in the
# per-template shared preamble, not here.
SYSTEM_PROMPT = (
    "You are a deterministic legal-text distillation function for the Lex-Balanus banking "
    "profile. You extract structure from the exact source text provided and return it as "
    "JSON matching the given schema. You never assert anything the provided text does not "
    "support."
)

MISSING_KEY_MSG = "TODO(human): export ANTHROPIC_API_KEY — do not improvise another provider."

PROMPTS_DIR = Path(__file__).resolve().parent.parent / "profiles" / "lex_balanus" / "prompts"
DEFAULT_CACHE_ROOT = Path("data/llm_cache")

T = TypeVar("T", bound=BaseModel)


# --- Errors ----------------------------------------------------------------------------


class LlmError(RuntimeError):
    """Base for every harness failure."""


class MissingApiKey(LlmError):
    """Live call requested but ``ANTHROPIC_API_KEY`` is absent (a checkpoint, §4)."""


class CacheMiss(LlmError):
    """Replay mode and the key is not cached — the harness will not silently call live."""


class SchemaRejection(LlmError):
    """The model's output failed schema validation twice (initial + one retry)."""


class BudgetExceeded(LlmError):
    """A per-run budget cap (calls or output tokens) would be exceeded."""


class LlmRefusal(LlmError):
    """The model returned ``stop_reason == "refusal"`` (a checkpoint, §4)."""


# --- Templating ------------------------------------------------------------------------


def load_shared_preamble() -> str:
    return (PROMPTS_DIR / "_shared_preamble.md").read_text()


def load_template(name: str) -> str:
    """Load a versioned prompt template ``profiles/lex_balanus/prompts/<name>.md``."""
    return (PROMPTS_DIR / f"{name}.md").read_text()


def render(template_text: str, variables: dict[str, str]) -> str:
    """Prepend the shared preamble and substitute ``$var`` placeholders (strict — a missing
    variable raises). ``$`` is the only special char, so JSON braces in a template are safe."""
    body = Template(template_text).substitute(variables)
    return f"{load_shared_preamble()}\n\n{body}"


# --- Transport (abstracted so replay/tests never import the SDK) ------------------------


@dataclass(frozen=True)
class CompletionRequest:
    model: str
    system: str
    prompt: str
    max_tokens: int
    schema_name: str
    json_schema: dict[str, Any]


@dataclass(frozen=True)
class RawCompletion:
    text: str
    input_tokens: int
    output_tokens: int


# A transport turns a request into raw text + usage. The live one imports the SDK lazily;
# tests inject a fake so the offline gate never touches the network.
Transport = Callable[[CompletionRequest], RawCompletion]


def anthropic_transport(*, thinking_disabled: bool = True) -> Transport:
    """Build the live transport. Stops with ``MissingApiKey`` if the key is absent — the SDK
    is imported lazily so replay never needs it, and no other provider is substituted."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise MissingApiKey(MISSING_KEY_MSG)

    import anthropic  # lazy: only on a live path

    client: Any = anthropic.Anthropic(api_key=api_key)

    def _call(req: CompletionRequest) -> RawCompletion:
        kwargs: dict[str, Any] = {
            "model": req.model,
            "max_tokens": req.max_tokens,
            "system": req.system,
            "messages": [{"role": "user", "content": req.prompt}],
            "output_config": {
                "format": {
                    "type": "json_schema",
                    "schema": req.json_schema,
                }
            },
        }
        if thinking_disabled:
            # Deterministic structured extraction; determinism for the gate is the cache.
            kwargs["thinking"] = {"type": "disabled"}
        resp = client.messages.create(**kwargs)
        stop = getattr(resp, "stop_reason", None)
        if stop == "refusal":
            raise LlmRefusal(f"model refused: {getattr(resp, 'stop_details', None)}")
        if stop == "max_tokens":
            raise LlmError(f"hit max_tokens ({req.max_tokens}); raise max_tokens and re-run")
        text = next((b.text for b in resp.content if getattr(b, "type", None) == "text"), "")
        usage = resp.usage
        return RawCompletion(
            text=text,
            input_tokens=int(getattr(usage, "input_tokens", 0)),
            output_tokens=int(getattr(usage, "output_tokens", 0)),
        )

    return _call


# --- Budget guard ----------------------------------------------------------------------


@dataclass
class Budget:
    """Per-run guard with a visible counter. ``charge_call`` is checked *before* a call;
    ``charge_tokens`` *after* (tokens are only known once the response returns)."""

    max_calls: int
    max_output_tokens: int
    calls: int = 0
    input_tokens: int = 0
    output_tokens: int = 0

    def charge_call(self) -> None:
        if self.calls + 1 > self.max_calls:
            raise BudgetExceeded(f"call budget exhausted ({self.calls}/{self.max_calls})")
        self.calls += 1

    def charge_tokens(self, raw: RawCompletion) -> None:
        self.input_tokens += raw.input_tokens
        self.output_tokens += raw.output_tokens
        logger.info(
            "llm call %d/%d — tokens in=%d out=%d (out total %d/%d)",
            self.calls,
            self.max_calls,
            raw.input_tokens,
            raw.output_tokens,
            self.output_tokens,
            self.max_output_tokens,
        )
        if self.output_tokens > self.max_output_tokens:
            raise BudgetExceeded(
                f"output-token budget exhausted ({self.output_tokens}/{self.max_output_tokens})"
            )

    def summary(self) -> str:
        return (
            f"calls={self.calls}/{self.max_calls} "
            f"in={self.input_tokens} out={self.output_tokens}/{self.max_output_tokens}"
        )


# --- The harness -----------------------------------------------------------------------


def _prompt_sha256(prompt: str) -> str:
    return hashlib.sha256(prompt.encode("utf-8")).hexdigest()


@dataclass
class LlmHarness:
    """Prompt-in, validated-object-out, cache-first. ``live=False`` (the default) replays and
    never touches the network."""

    cache_root: Path = DEFAULT_CACHE_ROOT
    model: str = PINNED_MODEL
    max_tokens: int = 8000
    live: bool = False
    transport: Transport | None = None
    budget: Budget = field(default_factory=lambda: Budget(max_calls=200, max_output_tokens=400_000))

    def _cache_path(self, prompt_sha: str) -> Path:
        return self.cache_root / f"{prompt_sha}.json"

    def _cache_get(self, prompt_sha: str) -> str | None:
        path = self._cache_path(prompt_sha)
        if not path.exists():
            return None
        record = json.loads(path.read_text())
        # Keyed by (model, prompt_sha256): a model change is a miss, not a stale hit.
        if record.get("model") != self.model:
            return None
        return str(record["response_text"])

    def _cache_put(self, prompt_sha: str, text: str) -> None:
        self.cache_root.mkdir(parents=True, exist_ok=True)
        record = {"model": self.model, "prompt_sha256": prompt_sha, "response_text": text}
        self._cache_path(prompt_sha).write_text(
            json.dumps(record, indent=2, sort_keys=True) + "\n"
        )

    def complete(self, prompt: str, schema: type[T]) -> T:
        """Return a validated ``schema`` instance for ``prompt``. Replays from cache when
        possible; on a live call, validates with one retry, then hard-fails."""
        prompt_sha = _prompt_sha256(prompt)

        cached = self._cache_get(prompt_sha)
        if cached is not None:
            try:
                return schema.model_validate_json(cached)
            except ValidationError as exc:  # corrupted cache — surface, never re-call silently
                raise SchemaRejection(
                    f"cached response for {prompt_sha[:12]} no longer validates against "
                    f"{schema.__name__}: {exc}"
                ) from exc

        if not self.live:
            raise CacheMiss(
                f"no cached response for {prompt_sha[:12]} ({schema.__name__}); "
                "replay mode will not call live. Re-run with live=True and ANTHROPIC_API_KEY."
            )

        transport = self.transport or anthropic_transport()
        req = CompletionRequest(
            model=self.model,
            system=SYSTEM_PROMPT,
            prompt=prompt,
            max_tokens=self.max_tokens,
            schema_name=schema.__name__,
            json_schema=schema.model_json_schema(),
        )

        last_error: ValidationError | None = None
        for attempt in range(2):  # initial + one retry (§2)
            self.budget.charge_call()
            raw = transport(req)
            self.budget.charge_tokens(raw)
            try:
                obj = schema.model_validate_json(raw.text)
            except ValidationError as exc:
                last_error = exc
                logger.warning(
                    "schema reject (attempt %d) for %s: %s", attempt + 1, schema.__name__, exc
                )
                continue
            self._cache_put(prompt_sha, raw.text)
            return obj

        raise SchemaRejection(
            f"{schema.__name__} validation failed twice (initial + retry): {last_error}"
        )
