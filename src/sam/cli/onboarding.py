"""SAM CLI - Onboarding commands (E2-G1, WP-E2.2, Program E / MISSION-2E).

Menyediakan command CLI onboarding untuk early adopter:
- `sam onboarding init` : rencana inisialisasi/onboarding project (dry-run).
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
) -> None:
    """Rencana/inisialisasi onboarding project (default dry-run)."""
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
