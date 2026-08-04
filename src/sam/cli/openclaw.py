"""
sam openclaw — Kelola integrasi OpenClaw (discover, status, monitor).
"""

import typer
import asyncio
import time
from ..openclaw.discovery import OpenClawDiscovery
from ..openclaw.health import OpenClawHealthCollector

app = typer.Typer()


@app.command()
def discover():
    """Temukan OpenClaw workspace."""
    discovery = OpenClawDiscovery()
    workspaces = asyncio.run(discovery.discover())

    if not workspaces:
        typer.echo("❌ No OpenClaw workspace found.")
        typer.echo("   Checked: known locations, current directory, config env")
        raise typer.Exit(code=0)

    typer.echo("OpenClaw Workspaces Found:")
    typer.echo("-" * 48)
    for ws in workspaces:
        version = ws.version or "unknown"
        typer.echo(f"  ✅ {ws.path}")
        typer.echo(f"     Version: {version}")


@app.command()
def status(workspace: str = typer.Option(None, "--workspace", "-w", help="Path workspace OpenClaw")):
    """Tampilkan status health OpenClaw."""
    # Discover if no workspace specified
    if not workspace:
        discovery = OpenClawDiscovery()
        workspaces = asyncio.run(discovery.discover())
        if not workspaces:
            typer.echo("❌ OpenClaw not found. Specify --workspace or run discover first.")
            raise typer.Exit(code=1)
        workspace = workspaces[0].path

    collector = OpenClawHealthCollector()
    health = asyncio.run(collector.collect(workspace))

    # Runtime status
    runtime_str = health.runtime.value.upper()
    icon = "✅" if health.runtime.value == "healthy" else "⚠️" if health.runtime.value == "degraded" else "❌"
    typer.echo(f"\n  {icon} OpenClaw Runtime: {runtime_str}")
    typer.echo(f"     Workspace: {health.workspace}")
    typer.echo(f"     Timestamp: {health.timestamp.isoformat()}")

    # Components
    typer.echo("\n  Components:")
    for comp in health.components:
        comp_icon = "✅" if comp.status.value == "healthy" else "⚠️" if comp.status.value == "degraded" else "❌"
        msg = f"  {comp_icon} {comp.name}: {comp.status.value.upper()}"
        if comp.message:
            msg += f"  ({comp.message})"
        typer.echo(msg)

    # Issues
    issues = asyncio.run(collector.detect_issues(health))
    if issues:
        typer.echo("\n  ⚠️  Issues Detected:")
        for issue in issues:
            typer.echo(f"     • {issue}")
    else:
        typer.echo("\n  ✅ No issues detected.")


@app.command()
def monitor(
    interval: int = typer.Option(5, "--interval", "-i", help="Interval monitoring dalam detik"),
    workspace: str = typer.Option(None, "--workspace", "-w", help="Path workspace OpenClaw"),
):
    """Monitor OpenClaw secara periodik."""
    if not workspace:
        discovery = OpenClawDiscovery()
        workspaces = asyncio.run(discovery.discover())
        if not workspaces:
            typer.echo("❌ OpenClaw not found.")
            raise typer.Exit(code=1)
        workspace = workspaces[0].path

    collector = OpenClawHealthCollector()
    typer.echo(f"Monitoring OpenClaw at: {workspace}")
    typer.echo(f"Interval: {interval}s (Ctrl+C to stop)")
    typer.echo("-" * 48)

    try:
        cycle = 0
        while True:
            cycle += 1
            health = asyncio.run(collector.collect(workspace))
            issues = asyncio.run(collector.detect_issues(health))

            status_line = f"[{cycle:04d}] Runtime: {health.runtime.value.upper():<10}"
            status_line += f" | Components: {len(health.components)}"
            status_line += f" | Issues: {len(issues)}"

            if issues:
                typer.echo(f"⚠️  {status_line}")
                for issue in issues:
                    typer.echo(f"     • {issue}")
            else:
                typer.echo(f"  ✅ {status_line}")

            time.sleep(interval)

    except KeyboardInterrupt:
        typer.echo("\nMonitoring stopped.")
