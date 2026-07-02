"""BoardDistill CLI (Typer).

Slice one is deterministic and fixtures-first: no LLM, no network, no scraping.
Command bodies are filled in across tasks T4-T9; the T0 scaffold registers the
surface and exits non-zero on any not-yet-implemented command.
"""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

app = typer.Typer(
    add_completion=False,
    no_args_is_help=True,
    help="BoardDistill — deterministic distillation engine (Lex-Balanus banking profile).",
)


def _stub(name: str) -> None:
    """Signal a command that is scaffolded but not yet implemented."""
    typer.echo(f"[boarddistill] '{name}' is not implemented yet (scaffold).", err=True)
    raise typer.Exit(code=1)


@app.command("validate-fixtures")
def validate_fixtures(
    directory: Annotated[Path, typer.Argument(help="Fixture directory to load and validate.")],
) -> None:
    """Load + schema-validate a fixture dir; non-zero exit on violation."""
    _stub("validate-fixtures")


@app.command("run-fixture")
def run_fixture(
    directory: Annotated[Path, typer.Argument(help="Fixture directory to distill.")],
    out: Annotated[Path, typer.Option("--out", help="Output directory.")],
) -> None:
    """Distill -> align -> diagnose -> operations -> classify -> verify -> write JSON."""
    _stub("run-fixture")


@app.command("render-package")
def render_package(
    outdir: Annotated[Path, typer.Argument(help="Output dir holding the JSON stage outputs.")],
) -> None:
    """Write package.md from the JSON stage outputs."""
    _stub("render-package")


@app.command("verify")
def verify(
    outdir: Annotated[Path, typer.Argument(help="Output dir to re-verify.")],
) -> None:
    """Recompute verifier statuses; print the final-status blocker summary."""
    _stub("verify")


@app.command("eval-fixture")
def eval_fixture(
    directory: Annotated[Path, typer.Argument(help="Fixture directory to evaluate against gold.")],
) -> None:
    """Deterministic agreement on operation set + effect class vs gold_findings.json."""
    _stub("eval-fixture")


@app.command("import-inventory")
def import_inventory(
    xlsx: Annotated[Path, typer.Argument(help="Inventory .xlsx to import.")],
    out: Annotated[Path, typer.Option("--out", help="Output directory for draft DutySpecs.")],
) -> None:
    """T8 adapter: emit draft DutySpecs; every claim 'unverified'; banner in output."""
    _stub("import-inventory")


if __name__ == "__main__":
    app()
