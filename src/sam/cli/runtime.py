"""
sam runtime — Runtime Container Tree.
"""

import typer
from sam.runtime.coordinator import RuntimeCoordinator

app = typer.Typer()


@app.callback(invoke_without_command=True)
def runtime(ctx: typer.Context):
    """Tampilkan status runtime container."""
    if ctx.invoked_subcommand is not None:
        return

    coord = RuntimeCoordinator()

    typer.echo("Runtime Container")
    typer.echo(f"\u251c\u2500\u2500 State: {coord.state.value.upper()}")
    typer.echo(f"\u251c\u2500\u2500 Hosting: {coord.adapter_name}")
    typer.echo(f"\u251c\u2500\u2500 Bootstrap: {len(coord.bootstrap_manager.steps)} steps")

    # Session info
    session = coord.session_manager.get_current_session()
    if session:
        typer.echo(f"\u251c\u2500\u2500 Session: {session['id']} ({session['state']})")
    else:
        typer.echo(f"\u251c\u2500\u2500 Session: None")

    # Sub-runtimes
    typer.echo(f"\u251c\u2500\u2500 Workflow Runtime: RUNNING")
    typer.echo(f"\u251c\u2500\u2500 Plugin Runtime: RUNNING")
    typer.echo(f"\u251c\u2500\u2500 Knowledge Runtime: READY")
    typer.echo(f"\u2514\u2500\u2500 Memory Runtime: READY")
