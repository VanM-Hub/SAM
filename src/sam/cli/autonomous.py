"""
sam autonomous — Kelola tindakan autonomous (status, approve, deny, history).
"""

import typer
import asyncio
from ..autonomous.executor import ActionExecutor
from ..autonomous.models import AutonomousAction, ActionType, AutonomousActionStatus
from ..autonomous.approval import ApprovalManager
from ..runtime.coordinator import RuntimeCoordinator

app = typer.Typer()


@app.command()
def status():
    """Tampilkan status tindakan autonomous."""
    coord = RuntimeCoordinator()
    executor = ActionExecutor(coord)

    pending = executor.get_pending_actions()
    completed = executor.get_actions_by_status(AutonomousActionStatus.COMPLETED)
    failed = executor.get_actions_by_status(AutonomousActionStatus.FAILED)
    denied = executor.get_actions_by_status(AutonomousActionStatus.DENIED)

    typer.echo("Autonomous Operations Status")
    typer.echo("-" * 40)
    typer.echo("  Pending:   {0}".format(len(pending)))
    typer.echo("  Approved:  {0}".format(len(executor.get_actions_by_status(AutonomousActionStatus.APPROVED))))
    typer.echo("  Executing: {0}".format(len(executor.get_actions_by_status(AutonomousActionStatus.EXECUTING))))
    typer.echo("  Completed: {0}".format(len(completed)))
    typer.echo("  Failed:    {0}".format(len(failed)))
    typer.echo("  Denied:    {0}".format(len(denied)))

    if pending:
        typer.echo("\n  ⏳ Pending Actions (awaiting approval):")
        for a in pending:
            typer.echo("    [{0}] {1} on {2} ({3}, {4:.0%} confidence)".format(
                a.id[:8], a.action_type.value, a.target,
                a.risk_level.value, a.confidence,
            ))

    # Pending approvals
    am = ApprovalManager()
    approvals = am.get_pending()
    if approvals:
        typer.echo("\n  🕐 Pending Approvals:")
        for req in approvals:
            typer.echo("    [{0}] Action: {1} — {2}".format(
                req.id[:8], req.action_id[:8], req.reason[:60],
            ))


@app.command()
def approve(
    request_id: str = typer.Argument(..., help="ID permintaan approval"),
):
    """Setujui permintaan approval untuk tindakan autonomous."""
    am = ApprovalManager()
    success = asyncio.run(am.approve(request_id))

    if success:
        typer.echo("✅ Approval granted for request: {0}".format(request_id))
    else:
        typer.echo("❌ Request not found or already processed: {0}".format(request_id))
        raise typer.Exit(code=1)


@app.command()
def deny(
    request_id: str = typer.Argument(..., help="ID permintaan approval"),
):
    """Tolak permintaan approval untuk tindakan autonomous."""
    am = ApprovalManager()
    success = asyncio.run(am.deny(request_id))

    if success:
        typer.echo("❌ Request denied: {0}".format(request_id))
    else:
        typer.echo("❌ Request not found or already processed: {0}".format(request_id))
        raise typer.Exit(code=1)


@app.command()
def history(
    limit: int = typer.Option(20, "--limit", "-n", help="Jumlah riwayat"),
):
    """Lihat riwayat tindakan autonomous."""
    coord = RuntimeCoordinator()
    executor = ActionExecutor(coord)
    actions = executor.get_history(limit=limit)

    if not actions:
        typer.echo("No action history yet.")
        return

    typer.echo("Autonomous Action History:")
    typer.echo("-" * 48)

    for a in reversed(actions):
        status_icon = {
            "completed": "✅",
            "failed": "❌",
            "denied": "🚫",
            "pending": "⏳",
            "approved": "✅",
            "executing": "🔄",
        }.get(a.status.value, "❓")

        typer.echo("  {0} [{1}] {2} → {3} ({4}, {5:.0%})".format(
            status_icon,
            a.id[:8],
            a.action_type.value.upper(),
            a.status.value.upper(),
            a.risk_level.value,
            a.confidence,
        ))
        if a.target:
            typer.echo("       Target: {0}".format(a.target))
        if a.error:
            typer.echo("       Error: {0}".format(a.error))


@app.command()
def execute(
    action_type: str = typer.Argument(..., help="Tipe aksi (restart/recover/resume/isolate/escalate)"),
    target: str = typer.Argument(..., help="Target aksi (worker/plugin/gateway/runtime)"),
    confidence: float = typer.Option(0.8, "--confidence", "-c", help="Confidence score 0.0-1.0"),
):
    """Execute tindakan autonomous secara langsung."""
    try:
        act_type = ActionType(action_type.lower())
    except ValueError:
        typer.echo("Invalid action type. Valid: restart, recover, resume, isolate, escalate")
        raise typer.Exit(code=1)

    action = AutonomousAction(
        action_type=act_type,
        target=target,
        reason="CLI execution: {0} on {1}".format(action_type, target),
        confidence=min(confidence, 1.0),
        steps=["Execute {0} on {1}".format(action_type, target)],
    )

    coord = RuntimeCoordinator()
    executor = ActionExecutor(coord)
    result = asyncio.run(executor.execute(action))

    if result.status.value == "completed":
        typer.echo("✅ {0} on {1}: COMPLETED".format(action_type.upper(), target))
    elif result.status.value == "pending":
        typer.echo("⏳ Action requires approval. ID: {0}".format(result.id))
        typer.echo("   Run: sam autonomous approve <request_id>")
    else:
        typer.echo("❌ {0}: {1}".format(result.status.value.upper(), result.error or "Unknown error"))
