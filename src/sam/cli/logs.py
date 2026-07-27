"""
sam logs — Tampilkan dan follow telemetry logs.
"""

import typer
import asyncio
from ..telemetry.service import TelemetryService
from ..telemetry.models import TelemetrySeverity

app = typer.Typer()


@app.command()
def logs(
    follow: bool = typer.Option(
        False, "--follow", "-f",
        help="Ikuti live log stream",
    ),
    limit: int = typer.Option(
        100, "--limit", "-n",
        help="Jumlah event yang ditampilkan",
    ),
    severity: str = typer.Option(
        None, "--severity", "-s",
        help="Filter severity (trace/debug/info/warning/error/critical)",
    ),
):
    """Tampilkan atau follow telemetry log events."""
    telemetry = TelemetryService()

    # Parse severity filter
    sev = None
    if severity:
        try:
            sev = TelemetrySeverity(severity.lower())
        except ValueError:
            typer.echo(f"Invalid severity: {severity}. Valid: trace/debug/info/warning/error/critical")
            raise typer.Exit(code=1)

    # Tampilkan existing events
    events = telemetry.get_events(limit=limit, severity=sev)
    if events:
        for e in events:
            _print_event(e)
    else:
        typer.echo("No events recorded yet.")

    # Follow mode
    if follow:
        typer.echo("\n--- Following logs (Ctrl+C to stop) ---")
        try:
            asyncio.run(_follow_loop(telemetry, severity=sev))
        except KeyboardInterrupt:
            typer.echo("\nStopped.")


def _print_event(event) -> None:
    """Format dan cetak satu event."""
    from datetime import datetime

    ts = event.timestamp
    if isinstance(ts, datetime):
        ts = ts.strftime("%H:%M:%S")

    sev = event.severity.value.upper()
    name = event.event_name
    comp = event.component

    # Add payload summary
    payload_str = ""
    if event.payload:
        payload_str = " ".join(
            f"{k}={v}" for k, v in list(event.payload.items())[:3]
        )

    typer.echo(f"{ts} [{sev}] [{comp}] {name}  {payload_str}")


async def _follow_loop(telemetry: TelemetryService, severity=None) -> None:
    """Loop untuk live streaming."""
    last_count = len(telemetry.events)

    while True:
        await asyncio.sleep(1)

        current_count = len(telemetry.events)
        if current_count > last_count:
            new_events = list(telemetry.events)[last_count:]
            for e in new_events:
                if severity is None or e.severity == severity:
                    _print_event(e)
            last_count = current_count
        else:
            typer.echo("[HEARTBEAT] runtime ok")
