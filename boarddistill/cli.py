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
    import json

    from distillcore.pipeline.verify import reverify_dir

    result = reverify_dir(outdir)
    (outdir / "verification.json").write_text(
        json.dumps(
            {"records": result.records, "claim_status": result.claim_status},
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )
    total = len(result.claim_status)
    verified = sum(1 for s in result.claim_status.values() if s == "verified")
    typer.echo(f"[boarddistill] {outdir.name}: {verified}/{total} claims verified")
    typer.echo(f"  final-eligible findings: {len(result.final_eligible)}")
    typer.echo("  final-status blockers:")
    for line in result.blocker_lines:
        typer.echo(f"    {line}")


@app.command("eval-fixture")
def eval_fixture(
    directory: Annotated[Path, typer.Argument(help="Fixture directory to evaluate against gold.")],
) -> None:
    """Deterministic agreement on operation set + effect class vs gold_findings.json."""
    from adapters.fixture_loader import load_fixture
    from profiles.lex_balanus.pipeline import eval_fixture as _eval

    result = _eval(load_fixture(directory))
    typer.echo(f"[boarddistill] eval {result.name}: {len(result.rows)} findings")
    typer.echo(
        f"  effect agreement: {result.effect_agreement:.0%} · "
        f"operation agreement: {result.operation_agreement:.0%} · "
        f"disposition agreement: {result.disposition_agreement:.0%} · "
        f"residuals: {result.residuals}"
    )
    for row in result.rows:
        if not (row.effect_match and row.operation_match):
            typer.echo(
                f"  MISMATCH {row.finding_id}: computed effect {row.computed_effect!r} "
                f"vs gold {row.gold_effect!r} (op_match={row.operation_match})",
                err=True,
            )
    if not result.all_match:
        raise typer.Exit(code=1)


@app.command("import-inventory")
def import_inventory(
    xlsx: Annotated[Path, typer.Argument(help="Inventory .xlsx to import.")],
    out: Annotated[Path, typer.Option("--out", help="Output directory for draft DutySpecs.")],
) -> None:
    """T8 adapter: emit draft DutySpecs; every claim 'unverified'; banner in output."""
    import json

    from adapters.inventory_xlsx import import_inventory as _import

    result = _import(xlsx)
    out.mkdir(parents=True, exist_ok=True)
    dest = out / "imported_duties.json"
    dest.write_text(
        json.dumps(
            {
                "_banner": result.banner,
                "duties": [d.model_dump(mode="json") for d in result.duties],
            },
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )
    typer.echo(f"[boarddistill] imported {len(result.duties)} DRAFT duties -> {dest}")
    typer.echo(f"  {result.banner}")


@app.command("verify-live")
def verify_live(
    targets: Annotated[
        Path, typer.Option("--targets", help="targets.json from b1-targets.")
    ] = Path("outputs/b1/targets.json"),
    cache: Annotated[Path, typer.Option("--cache", help="Source cache directory.")] = Path(
        "data/sources"
    ),
    out: Annotated[Path, typer.Option("--out", help="Output directory.")] = Path("outputs/b1"),
    offline: Annotated[
        bool, typer.Option("--offline", help="Replay from cache only; no network.")
    ] = False,
) -> None:
    """B1-T2: verify each target row's citation against primary sources (allowlisted)."""
    import json
    from collections import Counter

    from adapters.resolvers import build_resolver
    from adapters.retrieval import Fetcher, default_client, offline_client
    from distillcore.pipeline.verify import verify_targets

    doc = json.loads(targets.read_text())
    client = offline_client() if offline else default_client()
    try:
        resolver = build_resolver(Fetcher(cache, client))
        rows = verify_targets(doc["targets"], resolver)
    finally:
        client.close()

    out.mkdir(parents=True, exist_ok=True)
    spans = [r.verdict.span.model_dump(mode="json") for r in rows if r.verdict.span is not None]
    summary: dict[str, int] = dict(Counter(r.record.status for r in rows))
    payload = {
        "records": [r.record.model_dump(mode="json") for r in rows],
        "spans": spans,
        "rows": [
            {
                "duty_id": r.duty_id,
                "cluster": r.cluster,
                "citation": r.citation,
                "status": r.record.status,
                "as_of_valid": r.verdict.as_of_valid,
                "support_signal": r.verdict.support_signal,
                "note": r.verdict.note,
            }
            for r in rows
        ],
        "summary": summary,
    }
    (out / "verification.json").write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    typer.echo(f"[boarddistill] verify-live: {len(rows)} rows -> {out / 'verification.json'}")
    typer.echo("  " + " · ".join(f"{k}={v}" for k, v in sorted(summary.items())))


@app.command("b1-targets")
def b1_targets(
    import_json: Annotated[
        Path,
        typer.Option("--import", help="Path to imported_duties.json."),
    ] = Path("outputs/import/imported_duties.json"),
    out: Annotated[Path, typer.Option("--out", help="Output directory for targets.json.")] = Path(
        "outputs/b1"
    ),
) -> None:
    """B1-T0: select the ~72 MVP-cluster target rows; write targets.json."""
    import json

    from adapters.b1_targets import build_targets

    doc = build_targets(import_json)
    out.mkdir(parents=True, exist_ok=True)
    dest = out / "targets.json"
    dest.write_text(json.dumps(doc, indent=2, sort_keys=True) + "\n")
    typer.echo(f"[boarddistill] B1 targets: {doc['count']} rows -> {dest}")
    typer.echo("  clusters: " + " · ".join(doc["clusters"]))
    typer.echo("  duty_ids: " + ", ".join(doc["duty_ids"]))


if __name__ == "__main__":
    app()
