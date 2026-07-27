"""
sam metrics — Tampilkan runtime metrics terkini.
"""

import typer
from ..telemetry.service import TelemetryService

app = typer.Typer()


@app.command()
def metrics():
    """Tampilkan metrics runtime (CPU, memory, uptime, health)."""
    telemetry = TelemetryService()
    m = telemetry.get_metrics()

    if m is None:
        typer.echo("No metrics collected yet.")
        typer.echo("Start the coordinator first: sam status")
        raise typer.Exit(code=0)

    cpu = m.cpu_percent
    memory_mb = m.memory_mb
    uptime = m.uptime_seconds
    health = m.health_score
    workflows = m.workflow_count
    plugins = m.plugin_count

    # Color coding berdasarkan health score
    health_str = _format_health(health)

    typer.echo(f"CPU Usage:      {cpu:.1f}%")
    typer.echo(f"Memory Usage:   {memory_mb:.0f} MB")
    typer.echo(f"Uptime:         {_format_uptime(uptime)}")
    typer.echo(f"Workflows:      {workflows}")
    typer.echo(f"Plugins:        {plugins}")
    typer.echo(f"Health Score:   {health:.1f}  {health_str}")


def _format_uptime(seconds: float) -> str:
    """Format detik ke HH:MM:SS."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def _format_health(score: float) -> str:
    """Return health status."""
    if score >= 95:
        return "✅ HEALTHY"
    elif score >= 70:
        return "⚠️  DEGRADED"
    else:
        return "❌ CRITICAL"
