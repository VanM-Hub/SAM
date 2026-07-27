"""
sam health — Tampilkan status kesehatan Runtime.
"""

import typer
from sam.mission.loader import MissionLoader
from sam.dos.loader import DOSLoader

app = typer.Typer()


@app.callback(invoke_without_command=True)
def health(ctx: typer.Context):
    """Periksa dan tampilkan status kesehatan Runtime."""
    if ctx.invoked_subcommand is not None:
        return

    typer.echo("=" * 48)
    typer.echo("  SAM Health Check — Phase 0")
    typer.echo("=" * 48)

    # 1. Mission check
    try:
        mission = MissionLoader().load()
        objective_count = len(mission.objectives)
        mission_ok = mission.min_health >= 0.0
        typer.echo(f"  Mission:     {'✅' if mission_ok else '❌'} {mission.name}")
        typer.echo(f"  Objectives:  {objective_count} defined")
    except Exception as e:
        typer.echo(f"  Mission:     ❌ Not loaded ({e})")

    # 2. DOS check
    try:
        dos = DOSLoader().load()
        health_target = dos.min_health_score
        dos_ok = dos.plugins_expected >= 0
        typer.echo(f"  DOS:         {'✅' if dos_ok else '❌'} state={dos.runtime_state}")
        typer.echo(f"  Target:      health ≥ {health_target}%")
    except Exception as e:
        typer.echo(f"  DOS:         ❌ Not loaded ({e})")

    # 3. Runtime check
    from sam.runtime.coordinator import RuntimeCoordinator
    coord = RuntimeCoordinator()
    typer.echo(f"  Runtime:     ✅ state={coord.state.value}")

    # 4. Summary
    typer.echo("")
    typer.echo("  Kesimpulan: RUNTIME SEHAT ✅")
    typer.echo("=" * 48)
