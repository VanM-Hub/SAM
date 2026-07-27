"""
sam service — Kelola service runtime (install, start, stop, status).
"""

import typer
import asyncio
from sam.service.manager import ServiceManager

app = typer.Typer()


@app.command()
def install():
    """Install SAM sebagai system service."""
    manager = ServiceManager()
    success = asyncio.run(manager.install())
    if success:
        typer.echo(f"Service installed on {manager.os}.")
    else:
        typer.echo(f"Service installation not supported on {manager.os}.")
        raise typer.Exit(code=1)


@app.command()
def start():
    """Start SAM system service."""
    manager = ServiceManager()
    success = asyncio.run(manager.start())
    if success:
        typer.echo(f"Service started on {manager.os}.")
    else:
        typer.echo("Failed to start service.")
        raise typer.Exit(code=1)


@app.command()
def stop():
    """Stop SAM system service."""
    manager = ServiceManager()
    success = asyncio.run(manager.stop())
    if success:
        typer.echo(f"Service stopped on {manager.os}.")
    else:
        typer.echo("Failed to stop service.")
        raise typer.Exit(code=1)


@app.command()
def status():
    """Get SAM service status."""
    manager = ServiceManager()
    status = asyncio.run(manager.status())
    typer.echo(f"Service status ({manager.os}): {status}")
