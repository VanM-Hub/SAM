"""
sam session — Lihat session aktif dan histori.
"""

import typer
from sam.runtime.session import SessionManager

app = typer.Typer()


@app.callback(invoke_without_command=True)
def session(ctx: typer.Context):
    """Tampilkan session aktif saat ini."""
    if ctx.invoked_subcommand is not None:
        return

    sm = SessionManager("./workspace")
    current = sm.get_current_session()

    typer.echo("=" * 48)
    typer.echo("  SAM Session Manager — Phase 0")
    typer.echo("=" * 48)

    if current:
        typer.echo(f"\n  Active Session:")
        typer.echo(f"    ID:         {current['id']}")
        typer.echo(f"    State:      {current['state']}")
        typer.echo(f"    Workspace:  {current['workspace']}")
        typer.echo(f"    Started:    {current['started_at']}")
        typer.echo(f"    Last Activity: {current['last_activity']}")
        typer.echo(f"    Checkpoints:   {len(current['checkpoints'])}")
    else:
        typer.echo("\n  No active session")

    # History
    history = sm.get_session_history()
    typer.echo(f"\n  History: {len(history)} session(s)")
    for s in history[:5]:  # max 5 latest
        cp_count = len(s.get("checkpoints", []))
        typer.echo(f"    [{s['state']:10}] {s['id']} — {s.get('started_at', '?')} ({cp_count} cp)")
    if len(history) > 5:
        typer.echo(f"    ... and {len(history) - 5} more")

    typer.echo("")


@app.command()
def history():
    """Tampilkan histori semua session."""
    sm = SessionManager("./workspace")
    sessions = sm.get_session_history()

    typer.echo("Session History:")
    typer.echo("-" * 60)
    for s in sessions:
        cp_count = len(s.get("checkpoints", []))
        typer.echo(f"  {s['id']:8} | {s['state']:10} | {s.get('workspace', '?')} | started={s.get('started_at', '?')} | {cp_count} cp")
    typer.echo(f"\nTotal: {len(sessions)} session(s)")


@app.command()
def show(session_id: str):
    """Tampilkan detail session tertentu."""
    sm = SessionManager("./workspace")
    s = sm.get_session_by_id(session_id)
    if not s:
        typer.echo(f"Session not found: {session_id}")
        raise typer.Exit(code=1)

    typer.echo(f"Session: {s['id']}")
    typer.echo(f"  State:      {s['state']}")
    typer.echo(f"  Workspace:  {s.get('workspace', '?')}")
    typer.echo(f"  Started:    {s.get('started_at', '?')}")
    typer.echo(f"  Last Activity: {s.get('last_activity', '?')}")
    typer.echo(f"  Checkpoints:  {len(s.get('checkpoints', []))}")
    for i, cp in enumerate(s.get("checkpoints", [])):
        typer.echo(f"    [{i}] {cp}")
