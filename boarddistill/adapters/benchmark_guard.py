"""B6 — the sealed answer-key path guard (leakage control §1.3 / T1).

The RBI traceability appendices ARE the held-out answer key. They live under
``data/benchmark/answer_key/`` and the proposal pipeline (engine run T3, baseline T4) must never
read them — only the scorer (T5) may, and only after explicitly lifting the guard. This module is
the code enforcement: the proposal pipeline reads corpus files ONLY through :func:`guarded_read`,
which refuses any path under the answer-key dir. The scorer reads through :func:`unseal_read`,
which is the single audited exception.

A path check, not a permission system — but enough to make an accidental read a hard error rather
than a silent leak, and to make any deliberate read grep-able (``unseal_read``).
"""

from __future__ import annotations

from pathlib import Path

BENCHMARK_ROOT = Path("data/benchmark")
ANSWER_KEY_DIR = BENCHMARK_ROOT / "answer_key"
CORPUS_DIR = BENCHMARK_ROOT / "corpus"
# The pseudonym map (real↔stable-random id) is also held out of the LLM-facing corpus.
PSEUDONYM_DIR = BENCHMARK_ROOT / "pseudonym_map"


class AnswerKeyAccessError(RuntimeError):
    """The proposal pipeline attempted to read the sealed answer key (a §3.2 checkpoint)."""


def _under(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
    except ValueError:
        return False
    return True


def is_answer_key_path(path: str | Path) -> bool:
    return _under(Path(path), ANSWER_KEY_DIR) or _under(Path(path), PSEUDONYM_DIR)


def assert_proposal_safe(path: str | Path) -> None:
    """Raise if ``path`` is sealed (answer key or pseudonym map). Called by the proposal pipeline
    before every read."""
    if is_answer_key_path(path):
        raise AnswerKeyAccessError(
            f"proposal pipeline attempted to read sealed path {path!r} — the answer key and "
            "pseudonym map are held out of the engine/baseline runs (B6 §1.3, checkpoint 3.2)."
        )


def guarded_read(path: str | Path) -> str:
    """Read a corpus file for the proposal pipeline. Refuses sealed paths."""
    assert_proposal_safe(path)
    return Path(path).read_text()


def unseal_read(path: str | Path) -> str:
    """The SINGLE audited exception (scorer only, T5): read a sealed answer-key file. Every call
    is a deliberate unseal — grep for ``unseal_read`` to audit that only the scorer uses it."""
    return Path(path).read_text()
