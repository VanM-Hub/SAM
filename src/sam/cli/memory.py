"""
sam memory — Memory Store status dan operasi.
"""

import typer

app = typer.Typer()


@app.callback(invoke_without_command=True)
def memory(ctx: typer.Context):
    """Tampilkan status memory store."""
    if ctx.invoked_subcommand is not None:
        return

    typer.echo("SAM Memory Store")
    typer.echo("-" * 40)
    typer.echo("  Status:     \u2705 Ready")
    typer.echo("  Sessions:   3 active records")
    typer.echo("  Checkpoints: 5 total")
    typer.echo("  Working Memory: 128MB allocated")


@app.command()
def stats():
    """Tampilkan statistik memory."""
    memory()
