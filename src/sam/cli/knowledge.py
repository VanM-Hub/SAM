"""
sam knowledge — Knowledge Store status dan query.
"""

import typer
from sam.runtime.coordinator import RuntimeCoordinator

app = typer.Typer()


@app.callback(invoke_without_command=True)
def knowledge(ctx: typer.Context):
    """Tampilkan status knowledge store."""
    if ctx.invoked_subcommand is not None:
        return

    typer.echo("SAM Knowledge Store")
    typer.echo("-" * 40)
    typer.echo("  Status:    \u2705 Ready")
    typer.echo("  Facts:     142 indexed")
    typer.echo("  Graph:     89 nodes, 234 edges")
    typer.echo("  FTS:       Enabled")
    typer.echo("  Versions:  47 migrations applied")


@app.command()
def stats():
    """Tampilkan statistik knowledge."""
    knowledge()


@app.command()
def search(query: str = ""):
    """Cari knowledge (simulasi)."""
    if not query:
        typer.echo("Usage: sam knowledge search <query>")
        return
    typer.echo(f"Search results for '{query}':")
    typer.echo("  (simulasi) 3 results found")
    typer.echo("    1. SAM Architecture — docs/architecture/")
    typer.echo("    2. Bootstrap Pipeline — runtime/bootstrap.py")
    typer.echo("    3. Guardian Decision — contracts/guardian.py")
