"""SAM CLI - Onboarding commands (E2-G1, WP-E2.2, Program E / MISSION-2E).

Menyediakan command CLI onboarding untuk early adopter:
- `sam onboarding init` : rencana inisialisasi/onboarding project (dry-run).
- `sam onboarding init --scaffold <name>` : buat starter project SAM baru (WP-E2.4).
- `sam onboarding doctor` : diagnosa kesehatan instalasi & environment.
- `sam onboarding version` : tampilkan versi package.

Implementasi logic murni berada di `sam.devx.onboarding`; handler di sini
hanya menampilkan ke terminal via Typer (keep it thin).
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer

from sam.devx.onboarding import doctor, init_plan, version_string
from sam.devx.scaffold import scaffold_project


app = typer.Typer(
    name="sam",
    help="SAM onboarding: init, doctor, version",
    no_args_is_help=True,
)


@app.command("version")
def version_cmd() -> None:
    """Tampilkan versi package SAM."""
    typer.echo("SAM v{0}".format(version_string()))


@app.command("doctor")
def doctor_cmd(
    path: Optional[Path] = typer.Option(
        None, "--path", "-p", help="Project root (default: auto-detect)"
    ),
    json: bool = typer.Option(False, "--json", help="Output JSON"),
) -> None:
    """Diagnosa kesehatan instalasi SAM & environment."""
    report = doctor(project_root=path)
    if json:
        import json as _json

        typer.echo(
            _json.dumps(
                {
                    "version": report.version,
                    "all_ok": report.all_ok,
                    "blocking_issues": report.blocking_issues,
                    "dependencies": [
                        {
                            "name": c.name,
                            "passed": c.passed,
                            "status": str(getattr(c, "status", "")),
                        }
                        for c in report.dependency_checks
                    ],
                    "environment": [
                        {"component": c.component, "passed": c.passed}
                        for c in report.environment_checks
                    ],
                },
                indent=2,
            )
        )
        return
    typer.echo(report.summary())
    for issue in report.blocking_issues:
        typer.echo("  ! {0}".format(issue))
    if not report.blocking_issues:
        typer.echo("  (tidak ada masalah blocking)")


@app.command("init")
def init_cmd(
    path: Optional[Path] = typer.Option(
        None, "--path", "-p", help="Project root (default: auto-detect)"
    ),
    apply: bool = typer.Option(False, "--apply", help="Jalankan bootstrap aplikasi"),
    scaffold: Optional[str] = typer.Option(
        None, "--scaffold", help="Buat starter project SAM baru dengan nama ini (WP-E2.4)"
    ),
    scaffold_dir: Optional[Path] = typer.Option(
        None, "--scaffold-dir", help="Direktori tujuan scaffold (default: ./<scaffold>)"
    ),
) -> None:
    """Rencana/inisialisasi onboarding project (default dry-run)."""
    if scaffold is not None:
        _run_scaffold(scaffold, scaffold_dir, apply=apply)
        return

    plan = init_plan(project_root=path)
    typer.echo("SAM Init - project: {0}".format(plan.project_root))
    typer.echo("  Struktur repo : {0}".format("OK" if plan.structure_ok else "BELUM LENGKAP"))
    typer.echo("  Bootstrap (dry-run) : {0}".format("OK" if plan.bootstrap_report_ok else "GAGAL"))
    typer.echo("  Fase bootstrap : {0}".format(", ".join(plan.phases)))
    for note in plan.notes:
        typer.echo("  ! {0}".format(note))
    typer.echo("  Next steps:")
    for step in plan.next_steps:
        typer.echo("    - {0}".format(step))
    if apply:
        typer.echo("  (mode --apply: jalankan BootstrapInstaller aplikasi penuh)")


def _run_scaffold(name: str, target: Optional[Path], *, apply: bool = False) -> None:
    """Handler `sam onboarding init --scaffold <name>`.

    `apply=False` (default): dry-run - hanya menampilkan rencana file.
    `apply=True`: menulis file scaffold ke target dir.
    """
    try:
        result = scaffold_project(name, target_dir=target, apply=apply)
    except ValueError as exc:
        typer.echo("  ! scaffold_error: {0}".format(exc))
        raise typer.Exit(code=2)

    mode = "--apply (menulis)" if apply else "dry-run"
    typer.echo("SAM Scaffold - project: {0} ({1})".format(result.name, mode))
    typer.echo("  Tujuan  : {0}".format(result.target_dir))
    typer.echo("  Valid   : {0}".format("OK" if result.validated else "GAGAL"))
    if apply:
        created = result.created
        if created:
            typer.echo("  Dibuat ({0} file):".format(len(created)))
            for rel in created:
                typer.echo("    + {0}".format(rel))
        if result.skipped:
            typer.echo("  Dilewati (sudah ada, {0}):".format(len(result.skipped)))
            for rel in result.skipped:
                typer.echo("    = {0}".format(rel))
    else:
        typer.echo("  Akan dibuat ({0} file):".format(len(result.created)))
        for rel in result.created:
            typer.echo("    - {0}".format(rel))
        typer.echo("  Next: ulangi dengan --scaffold <nama> --apply untuk menulis file.")
