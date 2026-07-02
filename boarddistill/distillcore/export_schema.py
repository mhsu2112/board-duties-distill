"""Export the canonical JSON Schema to ``schemas/canonical.schema.json``.

Deterministic: models are sorted by name and JSON keys are sorted, so re-exports are
byte-identical. Run via ``make schema``. This module is the schema *composition root*:
the canonical schema is the banking-bound one (DutySpec + Operation + Finding), so it
imports the ``lex_balanus`` profile here even though ``distillcore`` is otherwise
profile-independent.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel
from pydantic.json_schema import models_json_schema

from profiles.lex_balanus.models import BankingFinding, BankingOperation, DutySpec

from .models.base import LegalClaim, SnapshotDates, SourceSpan, VerifierRecord
from .models.calculus import Diagnostic

SCHEMA_PATH = Path(__file__).resolve().parent.parent / "schemas" / "canonical.schema.json"


def canonical_models() -> list[type[BaseModel]]:
    """The models composing the canonical schema, sorted for deterministic output."""
    models: list[type[BaseModel]] = [
        BankingFinding,
        BankingOperation,
        Diagnostic,
        DutySpec,
        LegalClaim,
        SnapshotDates,
        SourceSpan,
        VerifierRecord,
    ]
    return sorted(models, key=lambda m: m.__name__)


def build_schema() -> dict[str, Any]:
    _, top = models_json_schema(
        [(m, "validation") for m in canonical_models()],
        ref_template="#/$defs/{model}",
        title="BoardDistill canonical schema",
    )
    return top


def main() -> None:
    schema = build_schema()
    SCHEMA_PATH.parent.mkdir(parents=True, exist_ok=True)
    SCHEMA_PATH.write_text(json.dumps(schema, indent=2, sort_keys=True) + "\n")
    print(f"wrote {SCHEMA_PATH}")


if __name__ == "__main__":
    main()
