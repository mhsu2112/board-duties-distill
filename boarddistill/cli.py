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
    from adapters.fixture_loader import load_fixture, validate_bundle

    try:
        bundle = load_fixture(directory)
    except Exception as exc:  # noqa: BLE001 — surface any schema/parse failure to the user
        typer.echo(f"[boarddistill] {directory}: schema validation FAILED — {exc}", err=True)
        raise typer.Exit(code=1) from exc

    problems = validate_bundle(bundle)
    if problems:
        typer.echo(f"[boarddistill] {directory}: {len(problems)} referential problem(s):", err=True)
        for problem in problems:
            typer.echo(f"  - {problem}", err=True)
        raise typer.Exit(code=1)

    typer.echo(
        f"[boarddistill] {bundle.name}: OK "
        f"({len(bundle.as_built)} as-built, {len(bundle.intended)} intended, "
        f"{len(bundle.gold_operations)} operations, {len(bundle.gold_findings)} findings)"
    )


@app.command("run-fixture")
def run_fixture(
    directory: Annotated[Path, typer.Argument(help="Fixture directory to distill.")],
    out: Annotated[Path, typer.Option("--out", help="Output directory.")],
) -> None:
    """Distill -> align -> diagnose -> operations -> classify -> verify -> write JSON."""
    from adapters.fixture_loader import load_fixture
    from profiles.lex_balanus.pipeline import run_fixture as _run
    from profiles.lex_balanus.pipeline import write_outputs

    bundle = load_fixture(directory)
    result = _run(bundle)
    dest = write_outputs(result, bundle, out)
    typer.echo(f"[boarddistill] {result.name}: wrote {dest}")
    typer.echo(
        f"  findings={len(result.computed_findings)} "
        f"residuals={len(result.residuals)} violations={len(result.violations)}"
    )
    if result.residuals:
        for residual in result.residuals:
            typer.echo(f"  RESIDUAL {residual.finding_id}: {residual.primitives}", err=True)
    if result.violations:
        for violation in result.violations:
            typer.echo(f"  VIOLATION {violation.code} [{violation.subject_id}]", err=True)
    if not result.ok:
        raise typer.Exit(code=1)


@app.command("render-package")
def render_package(
    outdir: Annotated[Path, typer.Argument(help="Output dir holding the JSON stage outputs.")],
) -> None:
    """Write package.md from the JSON stage outputs."""
    from distillcore.pipeline.render import render_package as _render

    markdown = _render(outdir)
    dest = outdir / "package.md"
    dest.write_text(markdown)
    typer.echo(f"[boarddistill] wrote {dest} ({len(markdown)} chars)")


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
