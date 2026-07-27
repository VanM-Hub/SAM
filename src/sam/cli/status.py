"""
sam status — Tampilan lengkap status Runtime dari Coordinator.
"""

import typer
from sam.runtime.coordinator import RuntimeCoordinator
from sam.mission.loader import MissionLoader
from sam.dos.loader import DOSLoader

app = typer.Typer()


@app.callback(invoke_without_command=True)
def status(ctx: typer.Context):
    """Tampilkan status Runtime lengkap."""
    if ctx.invoked_subcommand is not None:
        return

    coord = RuntimeCoordinator()
    state = coord.state

    # Tentukan health label berdasarkan state
    health_map = {
        "ready": "HEALTHY",
        "running": "HEALTHY",
        "initializing": "INITIALIZING",
        "bootstrapping": "INITIALIZING",
        "degraded": "DEGRADED",
        "recovering": "RECOVERING",
        "paused": "PAUSED",
        "updating": "UPDATING",
        "stopping": "STOPPING",
        "shutdown": "SHUTDOWN",
        "crashed": "CRASHED",
        "safe_mode": "SAFE_MODE",
    }
    health = health_map.get(state.value, "UNKNOWN")

    typer.echo("=" * 48)
    typer.echo("  SAM Framework v1.1.0 — Phase 0")
    typer.echo("=" * 48)

    # ── Runtime State ──
    typer.echo(f"\n  [Runtime]")
    typer.echo(f"  State:     {state.value.upper()}")
    typer.echo(f"  Health:    {health}")
    typer.echo(f"  Hosting:   {coord.adapter_name}")
    typer.echo(f"  Bootstrap: {len(coord.bootstrap_manager.steps)} steps")

    # ── Session ──
    session = coord.session_manager.get_current_session()
    if session:
        typer.echo(f"\n  [Session]")
        typer.echo(f"  ID:        {session['id']}")
        typer.echo(f"  State:     {session['state']}")
        typer.echo(f"  Checkpoints: {len(session['checkpoints'])}")
    else:
        typer.echo(f"\n  [Session] None")

    # ── Mission ──
    try:
        mission = MissionLoader().load()
        typer.echo(f"\n  [Mission]")
        typer.echo(f"  Name:      {mission.name} ({mission.id})")
        typer.echo(f"  Priority:  {mission.priority}")
        typer.echo(f"  Min Health: {mission.min_health}")
        for o in mission.objectives:
            typer.echo(f"    \u2514 {o.id}: {o.name}")
    except Exception as e:
        typer.echo(f"\n  [Mission] Not loaded ({e})")

    # ── DOS ──
    try:
        dos = DOSLoader().load()
        typer.echo(f"\n  [DOS]")
        typer.echo(f"  State:     {dos.runtime_state}")
        typer.echo(f"  Plugins:   {dos.plugins_expected} expected")
        typer.echo(f"  Min Health: \u2265{dos.min_health_score}%")
        typer.echo(f"  Guardian:  {dos.guardian_mode}")
    except Exception as e:
        typer.echo(f"\n  [DOS] Not loaded ({e})")

    typer.echo("")
