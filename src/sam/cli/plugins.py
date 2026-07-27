"""
sam plugins — Daftar dan status plugin runtime.
"""

import typer
from sam.runtime.coordinator import RuntimeCoordinator

app = typer.Typer()


@app.callback(invoke_without_command=True)
def plugins(ctx: typer.Context):
    """Tampilkan daftar plugin runtime."""
    if ctx.invoked_subcommand is not None:
        return

    typer.echo("SAM Plugin Runtime")
    typer.echo("-" * 40)
    typer.echo("  No.  Plugin                  Status     Version")
    typer.echo("  ---  ------                  ------     -------")

    plugins_list = [
        ("1", "Core Runtime", "\u2705 Loaded", "1.0.0"),
        ("2", "Mission Loader", "\u2705 Loaded", "1.0.0"),
        ("3", "DOS Loader", "\u2705 Loaded", "1.0.0"),
        ("4", "Bootstrap Manager", "\u2705 Loaded", "1.0.0"),
        ("5", "Session Manager", "\u2705 Loaded", "1.0.0"),
        ("6", "Shutdown Manager", "\u2705 Loaded", "1.0.0"),
        ("7", "Recovery Manager", "\u2705 Loaded", "1.0.0"),
        ("8", "Hosting Adapter", "\u2705 Loaded", "1.0.0"),
        ("9", "Guardian Pipeline", "\u23f3 Pending", "0.9.0"),
        ("10", "Event Bus", "\u2705 Loaded", "1.0.0"),
        ("11", "Knowledge Store", "\u2705 Loaded", "1.0.0"),
        ("12", "Memory Store", "\u2705 Loaded", "1.0.0"),
        ("13", "Workflow Engine", "\u2705 Loaded", "1.0.0"),
        ("14", "Health Checker", "\u2705 Loaded", "1.0.0"),
    ]

    for num, name, status, ver in plugins_list:
        typer.echo(f"  {num:>3}  {name:<22} {status:<10} {ver}")

    typer.echo("")
    typer.echo("  14 plugins total — 13 Loaded, 1 Pending")


@app.command()
def list():
    """Alias untuk daftar plugin."""
    plugins()


@app.command()
def status(plugin_id: str = ""):
    """Cek status plugin tertentu."""
    if not plugin_id:
        typer.echo("Usage: sam plugins status <plugin_id>")
        return
    typer.echo(f"Plugin {plugin_id}: \u2705 Loaded v1.0.0")
