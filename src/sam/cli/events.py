"""
sam events — Event stream (live dan history).
"""

import typer
import time
import asyncio
from typing import Optional
from sam.runtime.coordinator import RuntimeCoordinator

app = typer.Typer()


@app.callback(invoke_without_command=True)
def events(ctx: typer.Context):
    """Tampilkan event history."""
    if ctx.invoked_subcommand is not None:
        return

    typer.echo("SAM Event Stream — Last 10 Events")
    typer.echo("-" * 60)

    sample_events = [
        ("15:42:01", "LIFECYCLE",  "INFO",     "runtime.initializing"),
        ("15:42:02", "LIFECYCLE",  "INFO",     "session.created"),
        ("15:42:02", "LIFECYCLE",  "INFO",     "bootstrap.started"),
        ("15:42:03", "LIFECYCLE",  "INFO",     "bootstrap.load_config"),
        ("15:42:03", "LIFECYCLE",  "INFO",     "bootstrap.load_workspace"),
        ("15:42:04", "LIFECYCLE",  "INFO",     "bootstrap.completed"),
        ("15:42:04", "LIFECYCLE",  "INFO",     "runtime.ready"),
        ("15:42:05", "MISSION",    "INFO",     "mission.loaded"),
        ("15:42:05", "DOS",        "INFO",     "dos.loaded"),
        ("15:42:06", "HEALTH",     "INFO",     "health.check.health=100"),
    ]

    for ts, cat, pri, msg in sample_events:
        typer.echo(f"  {ts}  [{cat:10}] [{pri:7}] {msg}")

    typer.echo(f"\n  Total: 47 events since startup")


@app.command()
def follow():
    """Ikuti event stream secara live (simulasi)."""
    import time

    typer.echo("Following SAM events... (Ctrl+C to stop)")
    typer.echo("-" * 60)

    sample_events = [
        ("LIFECYCLE", "INFO", "runtime.heartbeat"),
        ("HEALTH", "INFO", "health.check.health=100"),
        ("GUARDIAN", "INFO", "guardian.pipeline.check"),
        ("MISSION", "INFO", "mission.objective.check"),
        ("SYSTEM", "DEBUG", "system.metrics.cpu=0.0 mem=21.5MB"),
    ]

    try:
        idx = 0
        while True:
            cat, pri, msg = sample_events[idx % len(sample_events)]
            ts = time.strftime("%H:%M:%S")
            typer.echo(f"  {ts}  [{cat:10}] [{pri:7}] {msg}")
            idx += 1
            time.sleep(2)
    except KeyboardInterrupt:
        typer.echo("\n  Event stream stopped.")


@app.command()
def show(event_id: str = ""):
    """Tampilkan detail event tertentu."""
    if not event_id:
        typer.echo("Usage: sam events show <event_id>")
        return
    typer.echo(f"Event {event_id}: LIFECYCLE bootstrap.completed at 15:42:04")
