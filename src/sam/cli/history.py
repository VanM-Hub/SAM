"""
CLI commands for history.
"""

import typer
from ..operations.engine.history import HistoryEngine
from ..telemetry.service import TelemetryService

app = typer.Typer()


@app.command()
def show(limit: int = 50):
    """Show recent history."""
    telemetry = TelemetryService()
    engine = HistoryEngine(telemetry)
    entries = engine.get_timeline(limit=limit)

    if not entries:
        typer.echo("No history found.")
        return

    typer.echo("\n\U0001f4dc History")
    typer.echo("-" * 60)

    for entry in entries[:limit]:
        time_str = entry.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        typer.echo("{}  [{}] {}".format(
            time_str, entry.severity.value.upper(), entry.title
        ))

    typer.echo("-" * 60)
    typer.echo("Total: {}".format(len(entries)))


@app.command()
def search(query: str, limit: int = 50):
    """Search history."""
    telemetry = TelemetryService()
    engine = HistoryEngine(telemetry)
    entries = engine.search(query, limit=limit)

    if not entries:
        typer.echo("No history found for '{}'.".format(query))
        return

    typer.echo("\n\U0001f50d Results for '{}'".format(query))
    typer.echo("-" * 60)

    for entry in entries:
        time_str = entry.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        typer.echo("{}  {}".format(time_str, entry.title))

    typer.echo("-" * 60)
    typer.echo("Found: {}".format(len(entries)))
