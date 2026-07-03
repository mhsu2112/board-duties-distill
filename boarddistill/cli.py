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


@app.command("b2-report")
def b2_report(
    out: Annotated[Path, typer.Option("--out", help="B2 output directory.")] = Path("outputs/b2"),
    graph: Annotated[Path, typer.Option("--graph", help="Instrument graph json.")] = Path(
        "data/graph/us-gsib_v1.json"
    ),
) -> None:
    """B2-T7: write outputs/b2/B2_report.md from the b2 artifacts."""
    import json

    from adapters.b2_report import build_b2_report

    verif = json.loads((out / "verification.json").read_text())
    graph_doc = json.loads(graph.read_text())
    retags = json.loads((out / "retags.json").read_text()) if (out / "retags.json").exists() else {}
    disps = (
        json.loads((out / "dispositions.json").read_text())
        if (out / "dispositions.json").exists()
        else {}
    )
    report = build_b2_report(verif, graph_doc, retags, disps)
    (out / "B2_report.md").write_text(report)
    typer.echo(f"[boarddistill] B2 report -> {out / 'B2_report.md'} ({len(report)} chars)")


@app.command("b3-apply")
def b3_apply(
    verification: Annotated[
        Path, typer.Option("--verification", help="b2 verification.json.")
    ] = Path("outputs/b2/verification.json"),
    out: Annotated[Path, typer.Option("--out", help="B3 output directory.")] = Path("outputs/b3"),
) -> None:
    """B3-T0: accept-residual dispositions + s:CAP-11 reclassification."""
    import json

    from adapters.b3_dispositions import ledger

    verif = json.loads(verification.read_text())
    doc = ledger(verif)
    out.mkdir(parents=True, exist_ok=True)
    (out / "dispositions.json").write_text(json.dumps(doc, indent=2, sort_keys=True) + "\n")
    c = doc["counts"]
    typer.echo("[boarddistill] B3 dispositions applied:")
    typer.echo(
        f"  target duty rows: {c['target_duty_rows']} (s:CAP-11 -> supersession_note) · "
        f"verified: {c['verified_duties']} · residuals accepted: {c['residuals_accepted']}"
    )


@app.command("b4-apply")
def b4_apply(
    findings: Annotated[Path, typer.Option("--findings", help="B3-T4 findings.json.")] = Path(
        "outputs/b3/findings.json"
    ),
    out: Annotated[Path, typer.Option("--out", help="B4 output directory.")] = Path("outputs/b4"),
) -> None:
    """B4-T0: write back the B3 dispositions (f-D1…f-D9, AUD-07, the 18 diagnostics)."""
    import json

    from adapters.b4_dispositions import ledger

    findings_doc = json.loads(findings.read_text())
    doc = ledger(findings_doc)
    out.mkdir(parents=True, exist_ok=True)
    (out / "dispositions.json").write_text(json.dumps(doc, indent=2, sort_keys=True) + "\n")

    c = doc["counts"]
    b = doc["blocker_summary"]
    typer.echo("[boarddistill] B4-T0 dispositions written back (reviewer mhsu):")
    typer.echo(
        f"  {len(doc['consolidation_findings'])} consolidation + "
        f"{len(doc['diagnostic_findings'])} diagnostics + AUD-07 · states: {c}"
    )
    typer.echo(
        f"  blocker summary: {b['findings_draft']}/{b['findings_total']} draft, "
        f"{b['findings_final']} final (silently finalized: {b['silently_finalized'] or 'none'})"
    )


@app.command("b4-graph")
def b4_graph(
    graph: Annotated[Path, typer.Option("--graph", help="Instrument graph v1 json.")] = Path(
        "data/graph/us-gsib_v1.json"
    ),
    out: Annotated[Path, typer.Option("--out", help="Extended graph output path.")] = Path(
        "data/graph/us-gsib_v2.json"
    ),
) -> None:
    """B4-T4: extend instrument-graph v1 with grounded concept nodes for the lever operands."""
    import json

    from adapters.concept_graph import extended_graph_document

    base_doc = json.loads(graph.read_text())
    doc = extended_graph_document(base_doc)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(doc, indent=2, sort_keys=True) + "\n")

    cov = doc["coverage"]
    typer.echo(f"[boarddistill] concept-extended graph -> {out}")
    typer.echo(
        f"  concept nodes: {cov['concept_nodes']} · groundings all verified: "
        f"{cov['grounded_all_verified']} · B0 concept operands answered: "
        f"{cov['b0_concept_operands_answered']}/{cov['b0_concept_operands_total']}"
    )
    if not cov["grounded_all_verified"]:
        typer.echo("  ⚠ some concept grounding quote did not resolve to cache", err=True)
        raise typer.Exit(code=1)


@app.command("b4-repin")
def b4_repin(
    out: Annotated[Path, typer.Option("--out", help="B4 output directory.")] = Path("outputs/b4"),
) -> None:
    """B4-T2: re-pin the ten source-mismatch rows (cache-verified corrected quotes)."""
    import json

    from adapters.repin import repin_document

    doc = repin_document()
    out.mkdir(parents=True, exist_ok=True)
    (out / "repins.json").write_text(json.dumps(doc, indent=2, sort_keys=True) + "\n")

    c = doc["counts"]
    typer.echo("[boarddistill] B4-T2 re-pin:")
    typer.echo(
        f"  {c['rows']} rows re-pinned · quotes verified: {c['quote_verified']}/{c['rows']} · "
        f"fuzzy anchor-matched: {c['anchor_matched_fuzzy']} · F2/F4 escalations: "
        f"{c['escalated_f2_f4']} · partial-support: {c['partial_support']}"
    )
    if doc["unverified_quotes"]:
        typer.echo(f"  ⚠ UNVERIFIED quotes: {doc['unverified_quotes']}", err=True)
        raise typer.Exit(code=1)
    typer.echo(f"  {doc['redistill_checkpoint']}")


@app.command("b4-aud07")
def b4_aud07(
    distilled: Annotated[
        Path, typer.Option("--distilled", help="B3-T2 as_built_distilled.json.")
    ] = Path("outputs/b3/as_built_distilled.json"),
    retags: Annotated[Path, typer.Option("--retags", help="b2 retags.json.")] = Path(
        "outputs/b2/retags.json"
    ),
    out: Annotated[Path, typer.Option("--out", help="B4 output directory.")] = Path("outputs/b4"),
) -> None:
    """B4-T1: apply the AUD-07 resolution (board oversight; certify→CEO/CFO)."""
    import json

    from adapters.aud07 import AUD07, apply_to_distilled

    distilled_doc = json.loads(distilled.read_text())
    empty: dict[str, object] = {}
    retag = next(
        (r for r in json.loads(retags.read_text())["retags"] if r["duty_id"] == AUD07), empty
    )
    doc = apply_to_distilled(distilled_doc, retag)
    out.mkdir(parents=True, exist_ok=True)
    (out / "as_built_distilled.json").write_text(json.dumps(doc, indent=2, sort_keys=True) + "\n")
    (out / "aud07_resolution.json").write_text(
        json.dumps(doc["aud07_resolution"], indent=2, sort_keys=True) + "\n"
    )
    typer.echo("[boarddistill] B4-T1 AUD-07 resolved:")
    typer.echo(
        f"  board-side verb → review_and_challenge · certify → CEO/CFO actor record · "
        f"verb-vs-retag conflicts now: {doc['counts']['verb_retag_conflicts']}"
    )


@app.command("b3-distill")
def b3_distill(
    verification: Annotated[
        Path, typer.Option("--verification", help="b2 verification.json.")
    ] = Path("outputs/b2/verification.json"),
    import_json: Annotated[
        Path, typer.Option("--import", help="imported_duties.json (draft specs).")
    ] = Path("outputs/import/imported_duties.json"),
    retags: Annotated[Path, typer.Option("--retags", help="b2 retags.json.")] = Path(
        "outputs/b2/retags.json"
    ),
    cache: Annotated[Path, typer.Option("--cache", help="LLM response cache directory.")] = Path(
        "data/llm_cache"
    ),
    out: Annotated[Path, typer.Option("--out", help="B3 output directory.")] = Path("outputs/b3"),
    live: Annotated[
        bool, typer.Option("--live", help="Populate the cache via live calls (needs API key).")
    ] = False,
) -> None:
    """B3-T2: LLM-distill the 50 verified as-built duties against their pinned excerpts.

    Replay is the default and reads only the cache. ``--live`` populates it (requires
    ANTHROPIC_API_KEY; the harness stops with a TODO(human) note if it is absent)."""
    import json

    from adapters.distill import diff_report, distill_all, distilled_document
    from distillcore.llm import LlmHarness

    verif = json.loads(verification.read_text())
    imported = json.loads(import_json.read_text())
    drafts = {d["duty_id"]: d for d in imported["duties"]}
    retag_ledger = {r["duty_id"]: r for r in json.loads(retags.read_text())["retags"]}

    harness = LlmHarness(cache_root=cache, live=live)
    rows = distill_all(harness, verif, drafts, retag_ledger)

    out.mkdir(parents=True, exist_ok=True)
    doc = distilled_document(rows)
    (out / "as_built_distilled.json").write_text(json.dumps(doc, indent=2, sort_keys=True) + "\n")
    (out / "distill_diff.md").write_text(diff_report(rows, drafts))

    c = doc["counts"]
    typer.echo("[boarddistill] B3-T2 distilled as-built:")
    typer.echo(
        f"  distilled: {c['distilled']} · anchor-clean: {c['anchor_clean']} · "
        f"anchor-failures: {c['anchor_failures']} · verb-vs-retag conflicts: "
        f"{c['verb_retag_conflicts']} · budget: {harness.budget.summary()}"
    )
    if c["anchor_failures"]:
        typer.echo(
            f"  ⚠ anchor failures (checkpoint 1): {', '.join(doc['anchor_failure_rows'])}", err=True
        )


@app.command("b5-corpus")
def b5_corpus(
    waves_json: Annotated[Path, typer.Option("--waves")] = Path("outputs/b5/waves.json"),
    targets: Annotated[Path, typer.Option("--targets")] = Path("outputs/b1/targets.json"),
    import_json: Annotated[Path, typer.Option("--import")] = Path(
        "outputs/import/imported_duties.json"
    ),
    decompositions: Annotated[Path, typer.Option("--decompositions")] = Path(
        "outputs/b5/corpus/lever_decompositions.json"
    ),
    b0: Annotated[Path, typer.Option("--b0")] = Path("../b0_decompositions.json"),
    mvp_findings: Annotated[Path, typer.Option("--mvp-findings")] = Path(
        "outputs/b4/findings.json"
    ),
    mvp_distilled: Annotated[Path, typer.Option("--mvp-distilled")] = Path(
        "outputs/b4/as_built_distilled.json"
    ),
    graph: Annotated[Path, typer.Option("--graph")] = Path("data/graph/us-gsib_v3.json"),
    cache: Annotated[Path, typer.Option("--cache")] = Path("data/sources"),
    out: Annotated[Path, typer.Option("--out")] = Path("outputs/b5/corpus"),
    packet: Annotated[Path, typer.Option("--packet")] = Path("../REVIEW_PACKET_B5.md"),
) -> None:
    """B5-T6: build the corpus roll-up — master crosswalk, reform roadmap v2, stats, packet."""
    import json
    from collections import Counter

    from adapters.b5_corpus import (
        b5_lever_records,
        corpus_stats_md,
        master_crosswalk_md,
        mvp_levers,
        reform_roadmap_v2_md,
        review_packet_b5_md,
    )
    from adapters.b5_graph import all_corpus_rows
    from adapters.resolvers import build_resolver
    from adapters.retrieval import Fetcher, offline_client

    waves_doc = json.loads(waves_json.read_text())
    drafts = {d["duty_id"]: d for d in json.loads(import_json.read_text())["duties"]}
    mvp_targets = json.loads(targets.read_text())["targets"]
    corpus_rows = all_corpus_rows(
        mvp_targets, waves_doc, drafts, build_resolver(Fetcher(cache, offline_client()))
    )

    decs = json.loads(b0.read_text())["decompositions"]
    mvp_f = json.loads(mvp_findings.read_text())["findings"]
    b5_decomp = json.loads(decompositions.read_text())
    cluster_to_wave = {c: w["wave"] for w in waves_doc["waves"] for c in w["clusters"]}

    levers = mvp_levers(decs, mvp_f) + b5_lever_records(b5_decomp["levers"], cluster_to_wave)
    levers_by_cluster = {x["cluster"]: x for x in levers}

    # verb standards + findings + finding_kind across MVP (b4) and all B5 waves
    verb_standards: dict[str, str] = {}
    all_findings: list[dict[str, object]] = []
    finding_kind: dict[str, str] = {}
    for row in json.loads(mvp_distilled.read_text())["rows"]:
        verb_standards[row["duty_id"]] = row["distilled"]["verb_standard"]
    mvp_fdoc = json.loads(mvp_findings.read_text())
    all_findings += mvp_fdoc["findings"]
    finding_kind.update(mvp_fdoc.get("finding_kind", {}))
    for w in waves_doc["waves"]:
        wd = out.parent / w["wave"]
        dist = json.loads((wd / "as_built_distilled.json").read_text())
        for row in dist["rows"]:
            verb_standards[row["duty_id"]] = row["distilled"]["verb_standard"]
        fdoc = json.loads((wd / "findings.json").read_text())
        all_findings += fdoc["findings"]
        finding_kind.update(fdoc.get("finding_kind", {}))

    residual_taxonomy = dict(
        Counter(
            (r.verdict.note or "").split(";")[0].split("(")[0].strip()[:60]
            for r in corpus_rows
            if r.record.status != "verified"
        )
    )
    floor_candidates = b5_decomp["statutory_floor_candidates"]["candidates"]
    totals: dict[str, int] = dict(Counter(str(r.record.status) for r in corpus_rows))
    totals["rows"] = len(corpus_rows)
    wave_rates: dict[str, tuple[int, int]] = {}
    for w in waves_doc["waves"]:
        v = json.loads((out.parent / w["wave"] / "verification.json").read_text())
        s = v["summary"]
        wave_rates[w["wave"]] = (s.get("verified", 0), sum(s.values()))

    graph_doc = json.loads(graph.read_text())
    out.mkdir(parents=True, exist_ok=True)
    (out / "master_crosswalk.md").write_text(
        master_crosswalk_md(corpus_rows, levers_by_cluster, drafts)
    )
    (out / "reform_roadmap_v2.md").write_text(reform_roadmap_v2_md(levers))
    (out / "corpus_stats.md").write_text(
        corpus_stats_md(
            corpus_rows, graph_doc, verb_standards, all_findings, finding_kind, residual_taxonomy
        )
    )
    packet.write_text(
        review_packet_b5_md(levers, floor_candidates, residual_taxonomy, totals, wave_rates)
    )
    typer.echo("[boarddistill] B5-T6 corpus roll-up:")
    typer.echo(
        f"  levers: {len(levers)} (MVP {len(decs)} + B5 {len(b5_decomp['levers'])}) · "
        f"verified {totals.get('verified', 0)}/{totals['rows']} · "
        f"floor candidates {len(floor_candidates)}"
    )
    typer.echo(f"  wrote {out}/master_crosswalk.md, reform_roadmap_v2.md, corpus_stats.md")
    typer.echo(f"  wrote {packet}")


@app.command("b5-package")
def b5_package(
    wave: Annotated[str, typer.Option("--wave", help="Wave slug, or 'all'.")] = "all",
    waves_json: Annotated[Path, typer.Option("--waves", help="B5-T1 waves.json.")] = Path(
        "outputs/b5/waves.json"
    ),
    graph: Annotated[Path, typer.Option("--graph", help="Corpus instrument graph.")] = Path(
        "data/graph/us-gsib_v3.json"
    ),
    decompositions: Annotated[
        Path, typer.Option("--decompositions", help="B5-T4 lever_decompositions.json.")
    ] = Path("outputs/b5/corpus/lever_decompositions.json"),
    out: Annotated[Path, typer.Option("--out", help="B5 output directory.")] = Path("outputs/b5"),
) -> None:
    """B5-T5: render each wave's clusters into per-cluster consolidation packages."""
    import json

    from adapters.b5_package import build_wave_packages

    waves_doc = json.loads(waves_json.read_text())
    graph_doc = json.loads(graph.read_text())
    levers = json.loads(decompositions.read_text())["levers"]
    selected = [w for w in waves_doc["waves"] if wave in (w["wave"], "all")]

    typer.echo("[boarddistill] B5-T5 per-wave packages:")
    total = 0
    for w in selected:
        wave_dir = out / w["wave"]
        distilled = json.loads((wave_dir / "as_built_distilled.json").read_text())
        findings = json.loads((wave_dir / "findings.json").read_text())
        verif = json.loads((wave_dir / "verification.json").read_text())
        packages = build_wave_packages(w["wave"], w, distilled, findings, verif, graph_doc, levers)
        for slug, md in packages.items():
            pkg_dir = wave_dir / slug
            pkg_dir.mkdir(parents=True, exist_ok=True)
            (pkg_dir / "package.md").write_text(md)
            final = md.count("| final |")
            total += 1
            typer.echo(
                f"  {w['wave']}/{slug}/package.md · {len(md.splitlines())} lines · final: {final}"
            )
    typer.echo(f"  {total} packages rendered.")


@app.command("b5-decompose")
def b5_decompose(
    inventory: Annotated[Path, typer.Option("--inventory", help="Combined inventory xlsx.")] = Path(
        "../Synthesis/gsib-board_duties-combined_inventory.xlsx"
    ),
    cache: Annotated[Path, typer.Option("--cache", help="LLM response cache directory.")] = Path(
        "data/llm_cache"
    ),
    out: Annotated[Path, typer.Option("--out", help="B5 corpus output directory.")] = Path(
        "outputs/b5/corpus"
    ),
    max_calls: Annotated[int, typer.Option("--max-calls", help="LLM call ceiling.")] = 40,
    live: Annotated[
        bool, typer.Option("--live", help="Populate the cache via live calls (needs API key).")
    ] = False,
) -> None:
    """B5-T4: decompose the ~22 non-MVP reform levers into validated operation compositions."""
    import json

    from adapters.b5_decompose import decompose_all
    from adapters.b5_levers import extract_levers
    from distillcore.llm import Budget, LlmHarness

    lever_doc = extract_levers(inventory)
    out.mkdir(parents=True, exist_ok=True)
    (out / "levers_source.json").write_text(json.dumps(lever_doc, indent=2, sort_keys=True) + "\n")

    harness = LlmHarness(
        cache_root=cache, live=live, budget=Budget(max_calls=max_calls, max_output_tokens=400_000)
    )
    doc = decompose_all(harness, lever_doc["levers"])
    (out / "lever_decompositions.json").write_text(json.dumps(doc, indent=2, sort_keys=True) + "\n")

    c = doc["counts"]
    typer.echo("[boarddistill] B5-T4 lever decomposition:")
    typer.echo(
        f"  levers: {c['levers']} · by status: {c['by_status']} · residuals: {c['residuals']} · "
        f"closure holds: {c['closure_holds']} · budget: {harness.budget.summary()}"
    )
    if doc["residual_checkpoints"]:
        typer.echo(
            f"  ⚠ residual checkpoints (propose, never add): "
            f"{[r['lever_id'] for r in doc['residual_checkpoints']]}",
            err=True,
        )
    fc = doc["statutory_floor_candidates"]["candidates"]
    if fc:
        typer.echo(f"  statutory-floor candidates PROPOSED (human-owned): {sorted(fc)}")


@app.command("b5-waves")
def b5_waves(
    import_json: Annotated[Path, typer.Option("--import", help="imported_duties.json.")] = Path(
        "outputs/import/imported_duties.json"
    ),
    out: Annotated[Path, typer.Option("--out", help="B5 output directory.")] = Path("outputs/b5"),
) -> None:
    """B5-T1: partition the ~155 non-MVP rows into domain waves (deterministic)."""
    import json

    from adapters.b5_waves import build_wave_plan

    doc = build_wave_plan(json.loads(import_json.read_text())["duties"])
    out.mkdir(parents=True, exist_ok=True)
    (out / "waves.json").write_text(json.dumps(doc, indent=2, sort_keys=True) + "\n")

    c = doc["counts"]
    typer.echo("[boarddistill] B5-T1 wave plan:")
    typer.echo(
        f"  waves: {c['waves']} · non-MVP rows assigned: {c['non_mvp_rows_assigned']}"
        f"/{c['non_mvp_rows_total']}"
    )
    for w in doc["waves"]:
        typer.echo(f"  {w['wave']:26} {w['row_count']:3} rows · {w['cluster_count']} clusters")
    if c["non_mvp_rows_assigned"] != c["non_mvp_rows_total"]:
        typer.echo("  ⚠ some non-MVP row is unassigned", err=True)
        raise typer.Exit(code=1)


@app.command("b5-verify")
def b5_verify(
    wave: Annotated[
        str, typer.Option("--wave", help="Wave slug, or 'all' for every wave.")
    ] = "all",
    waves_json: Annotated[Path, typer.Option("--waves", help="B5-T1 waves.json.")] = Path(
        "outputs/b5/waves.json"
    ),
    import_json: Annotated[Path, typer.Option("--import", help="imported_duties.json.")] = Path(
        "outputs/import/imported_duties.json"
    ),
    cache: Annotated[Path, typer.Option("--cache", help="Source cache directory.")] = Path(
        "data/sources"
    ),
    out: Annotated[Path, typer.Option("--out", help="B5 output directory.")] = Path("outputs/b5"),
    offline: Annotated[
        bool, typer.Option("--offline", help="Replay from cache only; no network.")
    ] = False,
) -> None:
    """B5-T2: verify a wave's rows against primary sources (allowlisted)."""
    import json

    from adapters.b5_verify import verify_wave, wave_payload, wave_review_queue
    from adapters.resolvers import build_resolver
    from adapters.retrieval import Fetcher, default_client, offline_client

    waves_doc = json.loads(waves_json.read_text())
    drafts = {d["duty_id"]: d for d in json.loads(import_json.read_text())["duties"]}
    selected = [w for w in waves_doc["waves"] if wave in (w["wave"], "all")]
    if not selected:
        typer.echo(f"[boarddistill] no such wave: {wave}", err=True)
        raise typer.Exit(code=1)

    client = offline_client() if offline else default_client()
    try:
        resolver = build_resolver(Fetcher(cache, client))
        for w in selected:
            rows = verify_wave(w, drafts, resolver)
            payload = wave_payload(w["wave"], rows)
            queue = wave_review_queue(w["wave"], rows)
            wave_dir = out / w["wave"]
            wave_dir.mkdir(parents=True, exist_ok=True)
            (wave_dir / "verification.json").write_text(
                json.dumps(payload, indent=2, sort_keys=True) + "\n"
            )
            (wave_dir / "review_queue.json").write_text(
                json.dumps(queue, indent=2, sort_keys=True) + "\n"
            )
            s = payload["summary"]
            halt = " ⚠ CONTRADICTED (wave halted)" if payload["contradicted"] else ""
            typer.echo(
                f"[boarddistill] {w['wave']}: {len(rows)} rows · "
                + " ".join(f"{k}={v}" for k, v in sorted(s.items()))
                + halt
            )
            if payload["contradicted"]:
                typer.echo(f"  contradicted: {payload['contradicted']}", err=True)
    finally:
        client.close()


@app.command("b5-graph")
def b5_graph_cmd(
    waves_json: Annotated[Path, typer.Option("--waves", help="B5-T1 waves.json.")] = Path(
        "outputs/b5/waves.json"
    ),
    targets: Annotated[Path, typer.Option("--targets", help="MVP targets.json.")] = Path(
        "outputs/b1/targets.json"
    ),
    import_json: Annotated[Path, typer.Option("--import", help="imported_duties.json.")] = Path(
        "outputs/import/imported_duties.json"
    ),
    cache: Annotated[Path, typer.Option("--cache", help="Source cache directory.")] = Path(
        "data/sources"
    ),
    graph_out: Annotated[
        Path, typer.Option("--graph-out", help="Corpus graph output path.")
    ] = Path("data/graph/us-gsib_v3.json"),
    out: Annotated[Path, typer.Option("--out", help="B5 output directory.")] = Path("outputs/b5"),
) -> None:
    """B5-T2: build the corpus-wide instrument graph (v3) + verification summary (offline)."""
    import json

    from adapters.b5_graph import (
        all_corpus_rows,
        corpus_graph_document,
        corpus_verification_summary,
    )
    from adapters.resolvers import build_resolver
    from adapters.retrieval import Fetcher, offline_client

    waves_doc = json.loads(waves_json.read_text())
    mvp_targets = json.loads(targets.read_text())["targets"]
    drafts = {d["duty_id"]: d for d in json.loads(import_json.read_text())["duties"]}

    resolver = build_resolver(Fetcher(cache, offline_client()))
    rows = all_corpus_rows(mvp_targets, waves_doc, drafts, resolver)

    graph_doc = corpus_graph_document(rows)
    graph_out.parent.mkdir(parents=True, exist_ok=True)
    graph_out.write_text(json.dumps(graph_doc, indent=2, sort_keys=True) + "\n")

    summary = corpus_verification_summary(rows, waves_doc)
    out.mkdir(parents=True, exist_ok=True)
    (out / "verification_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n"
    )

    cov = graph_doc["coverage"]
    t = summary["totals"]
    typer.echo("[boarddistill] B5-T2 corpus graph + verification summary:")
    typer.echo(
        f"  instruments: {cov['instruments']} (concept: {cov['concept_nodes']}, unknown-agency: "
        f"{cov['unknown_agency_instruments']}) · verified duties: {cov['verified_duties']} · "
        f"baseline answered: {cov['baseline_answered']}"
    )
    typer.echo(
        f"  corpus funnel: {t['verified']} verified / {t['unverified']} unverified / "
        f"{t['contradicted']} contradicted of {t['rows']} rows"
    )
    if cov["unknown_agency_instruments"]:
        typer.echo(
            f"  ⚠ unknown-agency instruments: {graph_doc['_unknown_agency_instruments']}", err=True
        )


@app.command("b5-distill")
def b5_distill(
    wave: Annotated[str, typer.Option("--wave", help="Wave slug, or 'all'.")] = "all",
    waves_json: Annotated[Path, typer.Option("--waves", help="B5-T1 waves.json.")] = Path(
        "outputs/b5/waves.json"
    ),
    import_json: Annotated[Path, typer.Option("--import", help="imported_duties.json.")] = Path(
        "outputs/import/imported_duties.json"
    ),
    cache: Annotated[Path, typer.Option("--cache", help="LLM response cache directory.")] = Path(
        "data/llm_cache"
    ),
    out: Annotated[Path, typer.Option("--out", help="B5 output directory.")] = Path("outputs/b5"),
    max_calls: Annotated[int, typer.Option("--max-calls", help="Per-wave LLM call ceiling.")] = 60,
    live: Annotated[
        bool, typer.Option("--live", help="Populate the cache via live calls (needs API key).")
    ] = False,
) -> None:
    """B5-T3: LLM-distill a wave's verified rows against their pinned excerpts."""
    import json

    from adapters.distill import distill_all, distilled_document
    from distillcore.llm import Budget, LlmHarness

    waves_doc = json.loads(waves_json.read_text())
    drafts = {d["duty_id"]: d for d in json.loads(import_json.read_text())["duties"]}
    selected = [w for w in waves_doc["waves"] if wave in (w["wave"], "all")]

    for w in selected:
        verif = json.loads((out / w["wave"] / "verification.json").read_text())
        harness = LlmHarness(
            cache_root=cache,
            live=live,
            budget=Budget(max_calls=max_calls, max_output_tokens=400_000),
        )
        rows = distill_all(harness, verif, drafts, {})
        doc = distilled_document(rows)
        (out / w["wave"] / "as_built_distilled.json").write_text(
            json.dumps(doc, indent=2, sort_keys=True) + "\n"
        )
        c = doc["counts"]
        typer.echo(
            f"[boarddistill] {w['wave']} distill: {c['distilled']} rows · anchor-clean "
            f"{c['anchor_clean']} · anchor-fail {c['anchor_failures']} · "
            f"budget {harness.budget.summary()}"
        )
        if c["anchor_failures"]:
            typer.echo(f"  ⚠ anchor failures: {doc['anchor_failure_rows']}", err=True)


@app.command("b5-diagnose")
def b5_diagnose(
    wave: Annotated[str, typer.Option("--wave", help="Wave slug, or 'all'.")] = "all",
    waves_json: Annotated[Path, typer.Option("--waves", help="B5-T1 waves.json.")] = Path(
        "outputs/b5/waves.json"
    ),
    cache: Annotated[Path, typer.Option("--cache", help="LLM response cache directory.")] = Path(
        "data/llm_cache"
    ),
    out: Annotated[Path, typer.Option("--out", help="B5 output directory.")] = Path("outputs/b5"),
    max_calls: Annotated[int, typer.Option("--max-calls", help="Per-wave LLM call ceiling.")] = 20,
    live: Annotated[
        bool, typer.Option("--live", help="Populate the cache via live calls (needs API key).")
    ] = False,
) -> None:
    """B5-T3: LLM diagnostics + deterministic mirror pairs per wave; mechanical classify."""
    import json

    from adapters.b5_diagnose import run_wave_diagnose, wave_excerpts
    from distillcore.llm import Budget, LlmHarness

    waves_doc = json.loads(waves_json.read_text())
    selected = [w for w in waves_doc["waves"] if wave in (w["wave"], "all")]

    for w in selected:
        wave_dir = out / w["wave"]
        verif = json.loads((wave_dir / "verification.json").read_text())
        distilled = json.loads((wave_dir / "as_built_distilled.json").read_text())
        harness = LlmHarness(
            cache_root=cache,
            live=live,
            budget=Budget(max_calls=max_calls, max_output_tokens=400_000),
        )
        doc = run_wave_diagnose(harness, w["wave"], w, distilled, wave_excerpts(verif))
        (wave_dir / "findings.json").write_text(json.dumps(doc, indent=2, sort_keys=True) + "\n")
        c = doc["counts"]
        fam = doc["duplication_families"]
        typer.echo(
            f"[boarddistill] {w['wave']} diagnose: {c['diagnostic_findings']} findings · "
            f"mirror {fam['mirror_pair']['count']} · restatement {fam['restatement']['count']} · "
            f"anchor-fail {c['anchor_failures']} · budget {harness.budget.summary()}"
        )
        if c["anchor_failures"]:
            typer.echo(f"  ⚠ diagnostic anchor failures: {doc['anchor_failures']}", err=True)


@app.command("b5-redistill")
def b5_redistill(
    import_json: Annotated[
        Path, typer.Option("--import", help="imported_duties.json (draft specs).")
    ] = Path("outputs/import/imported_duties.json"),
    retags: Annotated[Path, typer.Option("--retags", help="b2 retags.json.")] = Path(
        "outputs/b2/retags.json"
    ),
    distilled: Annotated[
        Path, typer.Option("--distilled", help="MVP as_built_distilled.json to merge into.")
    ] = Path("outputs/b4/as_built_distilled.json"),
    cache: Annotated[Path, typer.Option("--cache", help="LLM response cache directory.")] = Path(
        "data/llm_cache"
    ),
    out: Annotated[Path, typer.Option("--out", help="B5 output directory.")] = Path("outputs/b5"),
    live: Annotated[
        bool, typer.Option("--live", help="Populate the cache via live calls (needs API key).")
    ] = False,
) -> None:
    """B5-T0(a): re-distill the ten B4 re-pinned rows against their corrected excerpts."""
    import json

    from adapters.redistill import merge_into_distilled, redistill_all, redistill_document
    from distillcore.llm import LlmHarness

    drafts = {d["duty_id"]: d for d in json.loads(import_json.read_text())["duties"]}
    retag_ledger = {r["duty_id"]: r for r in json.loads(retags.read_text())["retags"]}

    harness = LlmHarness(cache_root=cache, live=live)
    rows = redistill_all(harness, drafts, retag_ledger)

    out.mkdir(parents=True, exist_ok=True)
    doc = redistill_document(rows)
    (out / "redistill.json").write_text(json.dumps(doc, indent=2, sort_keys=True) + "\n")

    if distilled.exists():
        merged = merge_into_distilled(json.loads(distilled.read_text()), rows)
        distilled.write_text(json.dumps(merged, indent=2, sort_keys=True) + "\n")

    c = doc["counts"]
    typer.echo("[boarddistill] B5-T0(a) re-distill (ten re-pinned rows):")
    typer.echo(
        f"  rows: {c['rows']} · anchor-clean: {c['anchor_clean']} · object-resolved: "
        f"{c['object_resolved']} · anchor-failures: {c['anchor_failures']} · "
        f"verb-vs-retag conflicts: {c['verb_retag_conflicts']} · budget: {harness.budget.summary()}"
    )
    if c["anchor_failures"]:
        typer.echo(f"  ⚠ anchor failures: {', '.join(doc['anchor_failure_rows'])}", err=True)
        raise typer.Exit(code=1)


@app.command("b5-retry-residuals")
def b5_retry_residuals(
    import_json: Annotated[Path, typer.Option("--import", help="imported_duties.json.")] = Path(
        "outputs/import/imported_duties.json"
    ),
    cache: Annotated[Path, typer.Option("--cache", help="Source cache directory.")] = Path(
        "data/sources"
    ),
    out: Annotated[Path, typer.Option("--out", help="B5 output directory.")] = Path("outputs/b5"),
) -> None:
    """B5-T0(c): retry the three B2 residuals (s:GOV-15, s:CAP-10, s:BCG-14)."""
    import json

    from adapters.retry_residuals import run_retries

    doc = run_retries(json.loads(import_json.read_text()), cache)
    out.mkdir(parents=True, exist_ok=True)
    (out / "residual_retries.json").write_text(json.dumps(doc, indent=2, sort_keys=True) + "\n")

    c = doc["counts"]
    typer.echo("[boarddistill] B5-T0(c) residual retries:")
    typer.echo(
        f"  retried: {c['retried']} · resolved: {c['resolved']} "
        f"({', '.join(doc['resolved_rows']) or '—'}) · re-documented: {c['re_documented']} "
        f"({', '.join(doc['re_documented_rows'])})"
    )


@app.command("b3-intended")
def b3_intended(
    decompositions: Annotated[
        Path, typer.Option("--decompositions", help="b0_decompositions.json.")
    ] = Path("../b0_decompositions.json"),
    import_json: Annotated[
        Path, typer.Option("--import", help="imported_duties.json (draft specs).")
    ] = Path("outputs/import/imported_duties.json"),
    cache: Annotated[Path, typer.Option("--cache", help="LLM response cache directory.")] = Path(
        "data/llm_cache"
    ),
    out: Annotated[Path, typer.Option("--out", help="B3 output directory.")] = Path("outputs/b3"),
    live: Annotated[
        bool, typer.Option("--live", help="Populate the cache via live calls (needs API key).")
    ] = False,
) -> None:
    """B3-T3: express the B0 decompositions as intended DutySpecs + Operation records.

    Operations are scaffolded from b0 (operands verbatim); the LLM drafts only the
    illustrative (NG2) consolidated duty language. Replay by default; ``--live`` populates."""
    import json

    from adapters.intended import build_all, intended_document
    from distillcore.llm import LlmHarness

    decs = json.loads(decompositions.read_text())["decompositions"]
    imported = json.loads(import_json.read_text())
    drafts = {d["duty_id"]: d for d in imported["duties"]}

    harness = LlmHarness(cache_root=cache, live=live)
    results = build_all(harness, decs, drafts)

    out.mkdir(parents=True, exist_ok=True)
    doc = intended_document(results)
    (out / "intended.json").write_text(json.dumps(doc, indent=2, sort_keys=True) + "\n")

    c = doc["counts"]
    typer.echo("[boarddistill] B3-T3 intended layer:")
    typer.echo(
        f"  decompositions: {c['decompositions']} · operations: {c['operations']} · "
        f"operand-coverage-ok: {c['operand_coverage_ok']}/{c['decompositions']} · "
        f"unresolved operand refs: {c['unresolved_operand_refs']} · "
        f"budget: {harness.budget.summary()}"
    )


@app.command("b3-diagnose")
def b3_diagnose(
    decompositions: Annotated[
        Path, typer.Option("--decompositions", help="b0_decompositions.json.")
    ] = Path("../b0_decompositions.json"),
    import_json: Annotated[
        Path, typer.Option("--import", help="imported_duties.json (draft specs).")
    ] = Path("outputs/import/imported_duties.json"),
    intended: Annotated[Path, typer.Option("--intended", help="B3-T3 intended.json.")] = Path(
        "outputs/b3/intended.json"
    ),
    distilled: Annotated[
        Path, typer.Option("--distilled", help="B3-T2 as_built_distilled.json.")
    ] = Path("outputs/b3/as_built_distilled.json"),
    verification: Annotated[
        Path, typer.Option("--verification", help="b2 verification.json.")
    ] = Path("outputs/b2/verification.json"),
    graph: Annotated[Path, typer.Option("--graph", help="Instrument graph json.")] = Path(
        "data/graph/us-gsib_v1.json"
    ),
    cache: Annotated[Path, typer.Option("--cache", help="LLM response cache directory.")] = Path(
        "data/llm_cache"
    ),
    out: Annotated[Path, typer.Option("--out", help="B3 output directory.")] = Path("outputs/b3"),
    live: Annotated[
        bool, typer.Option("--live", help="Populate the cache via live calls (needs API key).")
    ] = False,
) -> None:
    """B3-T4: consolidation findings (mechanical classify) + LLM diagnostics per MVP cluster."""
    import json

    from adapters.diagnose import diagnose_document, run_diagnose
    from distillcore.llm import LlmHarness

    decs = json.loads(decompositions.read_text())["decompositions"]
    drafts = {d["duty_id"]: d for d in json.loads(import_json.read_text())["duties"]}
    intended_doc = json.loads(intended.read_text())
    distilled_doc = json.loads(distilled.read_text())
    graph_doc = json.loads(graph.read_text())
    verif = json.loads(verification.read_text())

    records = {r["claim_id"]: r for r in verif["records"]}
    spans = {s["id"]: s for s in verif["spans"]}
    excerpts: dict[str, str] = {}
    cluster_of: dict[str, str] = {}
    for row in verif["rows"]:
        cluster_of[row["duty_id"]] = row.get("cluster", "")
        rec = records.get(f"claim-{row['duty_id']}")
        if rec and rec["checked_span_ids"]:
            span = spans.get(rec["checked_span_ids"][0])
            if span:
                excerpts[row["duty_id"]] = span["quote"]

    harness = LlmHarness(cache_root=cache, live=live)
    result = run_diagnose(
        harness, decs, drafts, intended_doc, graph_doc, distilled_doc, excerpts, cluster_of
    )
    out.mkdir(parents=True, exist_ok=True)
    doc = diagnose_document(result)
    (out / "findings.json").write_text(json.dumps(doc, indent=2, sort_keys=True) + "\n")

    c = doc["counts"]
    typer.echo("[boarddistill] B3-T4 diagnose + classify:")
    typer.echo(
        f"  consolidation findings: {c['consolidation_findings']} · diagnostics: "
        f"{c['diagnostic_findings']} · in-review: {c['in_review']} · effect classes: "
        f"{c['effect_classes']} · budget: {harness.budget.summary()}"
    )
    dv = doc["duplicate_divergence"]["counts"]
    typer.echo(
        f"  duplicate divergence — agreed: {dv['agreed']} · b0-only: {dv['b0_only']} · "
        f"llm-only: {dv['llm_only']}"
    )
    if c["anchor_failures"]:
        typer.echo(f"  ⚠ diagnostic anchor failures: {c['anchor_failures']}", err=True)


@app.command("b3-package")
def b3_package(
    distilled: Annotated[
        Path, typer.Option("--distilled", help="B3-T2 as_built_distilled.json.")
    ] = Path("outputs/b3/as_built_distilled.json"),
    intended: Annotated[Path, typer.Option("--intended", help="B3-T3 intended.json.")] = Path(
        "outputs/b3/intended.json"
    ),
    findings: Annotated[Path, typer.Option("--findings", help="B3-T4 findings.json.")] = Path(
        "outputs/b3/findings.json"
    ),
    verification: Annotated[
        Path, typer.Option("--verification", help="b2 verification.json.")
    ] = Path("outputs/b2/verification.json"),
    graph: Annotated[Path, typer.Option("--graph", help="Instrument graph json.")] = Path(
        "data/graph/us-gsib_v1.json"
    ),
    out: Annotated[Path, typer.Option("--out", help="B3 output directory.")] = Path("outputs/b3"),
) -> None:
    """B3-T5: render the three per-cluster consolidation packages (deterministic)."""
    import json

    from adapters.b3_package import build_packages

    packages = build_packages(
        json.loads(distilled.read_text()),
        json.loads(intended.read_text()),
        json.loads(findings.read_text()),
        json.loads(verification.read_text()),
        json.loads(graph.read_text()),
    )
    typer.echo("[boarddistill] B3-T5 consolidation packages:")
    for slug, md in packages.items():
        pkg_dir = out / slug
        pkg_dir.mkdir(parents=True, exist_ok=True)
        (pkg_dir / "package.md").write_text(md)
        final = md.count("| final |")
        typer.echo(f"  {slug}/package.md · {len(md.splitlines())} lines · findings final: {final}")


@app.command("b3-eval")
def b3_eval_cmd(
    decompositions: Annotated[
        Path, typer.Option("--decompositions", help="b0_decompositions.json.")
    ] = Path("../b0_decompositions.json"),
    import_json: Annotated[Path, typer.Option("--import", help="imported_duties.json.")] = Path(
        "outputs/import/imported_duties.json"
    ),
    distilled: Annotated[
        Path, typer.Option("--distilled", help="B3-T2 as_built_distilled.json.")
    ] = Path("outputs/b3/as_built_distilled.json"),
    findings: Annotated[Path, typer.Option("--findings", help="B3-T4 findings.json.")] = Path(
        "outputs/b3/findings.json"
    ),
    verification: Annotated[
        Path, typer.Option("--verification", help="b2 verification.json.")
    ] = Path("outputs/b2/verification.json"),
    cache: Annotated[Path, typer.Option("--cache", help="LLM response cache directory.")] = Path(
        "data/llm_cache"
    ),
    out: Annotated[Path, typer.Option("--out", help="B3 output directory.")] = Path("outputs/b3"),
    samples: Annotated[int, typer.Option("--samples", help="Stability samples per stage.")] = 3,
    live: Annotated[
        bool, typer.Option("--live", help="Draw live stability samples (needs API key).")
    ] = False,
) -> None:
    """B3-T6: eval — B0 agreement, stability, citation integrity, baseline comparison."""
    import json

    from adapters.b3_eval import (
        agreement_report,
        baseline_comparison,
        citation_integrity,
        eval_report_md,
        stability_diagnose,
        stability_distill,
    )
    from adapters.diagnose import DiagnosticSet, _cluster_duties, diagnose_cluster
    from adapters.distill import _prompt_for, build_targets
    from distillcore.llm import LlmHarness

    decs = json.loads(decompositions.read_text())["decompositions"]
    drafts = {d["duty_id"]: d for d in json.loads(import_json.read_text())["duties"]}
    distilled_doc = json.loads(distilled.read_text())
    findings_doc = json.loads(findings.read_text())
    verif = json.loads(verification.read_text())

    records = {r["claim_id"]: r for r in verif["records"]}
    spans = {s["id"]: s for s in verif["spans"]}
    excerpts: dict[str, str] = {}
    cluster_of: dict[str, str] = {}
    for row in verif["rows"]:
        cluster_of[row["duty_id"]] = row.get("cluster", "")
        rec = records.get(f"claim-{row['duty_id']}")
        if rec and rec["checked_span_ids"]:
            span = spans.get(rec["checked_span_ids"][0])
            if span:
                excerpts[row["duty_id"]] = span["quote"]

    agreement = agreement_report(decs, findings_doc)
    integrity = citation_integrity(distilled_doc, findings_doc, excerpts)
    baseline = baseline_comparison(drafts, cluster_of, excerpts, "Audit committee & independence")

    stability: list[dict[str, object]] = []
    harness = LlmHarness(cache_root=cache, live=live)
    targets = build_targets(verif, drafts)
    _AUD = "Audit committee & independence"
    aud_target = next((t for t in targets if cluster_of.get(t.duty_id) == _AUD), None)
    try:
        if aud_target is not None:
            stability.append(stability_distill(harness, _prompt_for(aud_target), samples))
        dd = {**distilled_doc, "_cluster_of": cluster_of}
        aud_duties = _cluster_duties(dd, "Audit committee & independence", excerpts)
        if aud_duties:
            _, corpus = diagnose_cluster(harness, "Audit committee & independence", aud_duties)
            # Rebuild the diagnose prompt for sampling (diagnose_cluster returns the corpus).
            from distillcore.llm import load_template, render
            from profiles.lex_balanus.enums import NormativeKind

            block = "\n\n".join(
                f"{d['duty_id']} · {d['verb']} · {d['object']}\n<<<\n{d['excerpt']}\n>>>"
                for d in aud_duties
            )
            prompt = render(
                load_template("diagnose"),
                {
                    "cluster": "Audit committee & independence",
                    "normative_kinds": ", ".join(m.value for m in NormativeKind),
                    "duties": block,
                },
            )
            stability.append(stability_diagnose(harness, prompt, DiagnosticSet, samples))
    except Exception as exc:  # replay miss when samples aren't cached yet
        typer.echo(f"  (stability skipped: {exc})", err=True)

    out.mkdir(parents=True, exist_ok=True)
    md = eval_report_md(agreement, stability, integrity, baseline)
    (out / "eval_report.md").write_text(md)

    typer.echo("[boarddistill] B3-T6 eval:")
    typer.echo(
        f"  effect-class agreement vs B0: {agreement['effect_class_agreement']} · "
        f"hallucinated-citation rate: {integrity['hallucinated_citation_rate']} "
        f"(gate {integrity['release_gate']}) · stability stages: {len(stability)} · "
        f"budget: {harness.budget.summary()}"
    )


@app.command("b2-graph")
def b2_graph(
    targets: Annotated[
        Path, typer.Option("--targets", help="targets.json from b1-targets.")
    ] = Path("outputs/b1/targets.json"),
    cache: Annotated[Path, typer.Option("--cache", help="Source cache directory.")] = Path(
        "data/sources"
    ),
    out: Annotated[Path, typer.Option("--out", help="Graph output path.")] = Path(
        "data/graph/us-gsib_v1.json"
    ),
) -> None:
    """B2-T6: build instrument-graph v1 from the (cache-replayed) verification."""
    import json

    from adapters.graph_build import build_instrument_graph, graph_document
    from adapters.resolvers import build_resolver
    from adapters.retrieval import Fetcher, offline_client
    from distillcore.pipeline.verify import verify_targets

    doc = json.loads(targets.read_text())
    resolver = build_resolver(Fetcher(cache, offline_client()))
    rows = verify_targets(doc["targets"], resolver)

    graph = build_instrument_graph(rows)
    document = graph_document(graph, rows)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(document, indent=2, sort_keys=True) + "\n")

    cov = document["coverage"]
    typer.echo(f"[boarddistill] instrument graph -> {out}")
    typer.echo(
        f"  instruments={cov['instruments']} · verified duties={cov['verified_duties']} "
        f"· baseline answered={cov['baseline_answered']}"
    )


@app.command("b2-accept")
def b2_accept(
    verification: Annotated[
        Path, typer.Option("--verification", help="verification.json from verify-live.")
    ] = Path("outputs/b1/verification.json"),
    import_json: Annotated[
        Path, typer.Option("--import", help="imported_duties.json to stamp.")
    ] = Path("outputs/import/imported_duties.json"),
    out: Annotated[Path, typer.Option("--out", help="Output directory for the ledger.")] = Path(
        "outputs/b2"
    ),
) -> None:
    """B2-T0: record reviewer_accepted dispositions for the B1-verified rows."""
    import json

    from adapters.dispositions import accept_verified, ledger, stamp_dispositions

    verif = json.loads(verification.read_text())
    dispositions = accept_verified(verif)

    out.mkdir(parents=True, exist_ok=True)
    (out / "dispositions.json").write_text(
        json.dumps(ledger(dispositions), indent=2, sort_keys=True) + "\n"
    )
    if import_json.exists():
        doc = stamp_dispositions(json.loads(import_json.read_text()), dispositions)
        import_json.write_text(json.dumps(doc, indent=2, sort_keys=True) + "\n")

    verified = sum(1 for r in verif["rows"] if r["status"] == "verified")
    remaining = sum(1 for r in verif["rows"] if r["status"] != "verified")
    typer.echo(f"[boarddistill] B2 accept: {len(dispositions)} rows -> reviewer_accepted")
    typer.echo(f"  cleared: {verified} · still in review queue: {remaining}")


@app.command("b2-retag")
def b2_retag(
    verification: Annotated[
        Path, typer.Option("--verification", help="verification.json from verify-live.")
    ] = Path("outputs/b1/verification.json"),
    import_json: Annotated[
        Path, typer.Option("--import", help="imported_duties.json to retag.")
    ] = Path("outputs/import/imported_duties.json"),
    out: Annotated[Path, typer.Option("--out", help="Output directory.")] = Path("outputs/b2"),
) -> None:
    """B2-T1: actor retag for the approved 6 support-flagged rows."""
    import json

    from adapters.dispositions import ledger
    from adapters.retag import build_retags, combined_ledger, retag_ledger

    verif = json.loads(verification.read_text())
    out.mkdir(parents=True, exist_ok=True)

    if import_json.exists():
        records, doc = build_retags(verif, json.loads(import_json.read_text()))
        import_json.write_text(json.dumps(doc, indent=2, sort_keys=True) + "\n")
    else:
        records, _ = build_retags(verif, {"duties": []})

    (out / "retags.json").write_text(
        json.dumps(retag_ledger(records), indent=2, sort_keys=True) + "\n"
    )
    # refine the disposition ledger: 15 accepted + 6 modified
    (out / "dispositions.json").write_text(
        json.dumps(ledger(combined_ledger(verif)), indent=2, sort_keys=True) + "\n"
    )

    todos = sum(1 for r in records if r.todo_human is not None)
    typer.echo(f"[boarddistill] B2 retag: {len(records)} rows retagged ({todos} TODO(human))")
    for r in records:
        flag = "  [TODO(human)]" if r.todo_human else ""
        typer.echo(f"  {r.duty_id:10} {r.from_actor!r} -> {r.to_actor!r}{flag}")


@app.command("b1-report")
def b1_report(
    verification: Annotated[
        Path, typer.Option("--verification", help="verification.json from verify-live.")
    ] = Path("outputs/b1/verification.json"),
    import_json: Annotated[
        Path, typer.Option("--import", help="imported_duties.json to write statuses back into.")
    ] = Path("outputs/import/imported_duties.json"),
    out: Annotated[Path, typer.Option("--out", help="Output directory.")] = Path("outputs/b1"),
) -> None:
    """B1-T4: write B1_report.md + review_queue.json; set verifier_status on target claims."""
    import json

    from adapters.b1_report import apply_statuses_to_import, build_report, build_review_queue

    verif = json.loads(verification.read_text())
    out.mkdir(parents=True, exist_ok=True)
    (out / "B1_report.md").write_text(build_report(verif))
    queue = build_review_queue(verif)
    (out / "review_queue.json").write_text(json.dumps(queue, indent=2, sort_keys=True) + "\n")

    if import_json.exists():
        doc = apply_statuses_to_import(json.loads(import_json.read_text()), verif)
        import_json.write_text(json.dumps(doc, indent=2, sort_keys=True) + "\n")

    typer.echo(f"[boarddistill] B1 report -> {out / 'B1_report.md'}")
    typer.echo(f"  review queue: {sum(queue['counts'].values())} items {queue['counts']}")


@app.command("realify-fixtures")
def realify_fixtures(
    fixtures: Annotated[Path, typer.Option("--fixtures", help="Fixture corpus root.")] = Path(
        "data/fixtures/us-gsib"
    ),
    cache: Annotated[Path, typer.Option("--cache", help="Source cache directory.")] = Path(
        "data/sources"
    ),
    offline: Annotated[bool, typer.Option("--offline", help="Use cache only; no network.")] = False,
) -> None:
    """B1-T3: swap fixture [FIXTURE] paraphrases for verified verbatim text."""
    from adapters.realify import realify_fixture
    from adapters.resolvers import build_resolver
    from adapters.retrieval import Fetcher, default_client, offline_client

    client = offline_client() if offline else default_client()
    try:
        resolver = build_resolver(Fetcher(cache, client))
        for fixture_dir in sorted(p for p in fixtures.iterdir() if (p / "sources.json").exists()):
            changes = realify_fixture(fixture_dir, resolver)
            realified = sum(1 for c in changes if c.status == "realified")
            typer.echo(f"[boarddistill] {fixture_dir.name}: {realified} span(s) realified")
            for c in changes:
                if c.status in {"realified", "unresolved"}:
                    typer.echo(f"    {c.status:12} {c.span_id:14} {c.citation}")
    finally:
        client.close()


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
