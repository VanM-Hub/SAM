"""
CLI commands for task management.
"""

import typer
from ..telemetry.service import TelemetryService
from ..operations.engine.task import TaskEngine

app = typer.Typer()


@app.command()
def list():
    """List all tasks."""
    telemetry = TelemetryService()
    engine = TaskEngine(telemetry)
    tasks = engine.get_tasks()

    if not tasks:
        typer.echo("No tasks found.")
        return

    typer.echo("\n\U0001f4cb Task List")
    typer.echo("-" * 50)

    for task in tasks:
        if task.is_active:
            status_icon = "\U0001f504"
        elif task.status == TaskStatus.COMPLETED:
            status_icon = "\u2705"
        else:
            status_icon = "\u274c"
        approval = " \u26a0\ufe0f" if task.needs_approval else ""
        typer.echo("{} {} [{}]{}".format(
            status_icon, task.name, task.progress_text, approval
        ))

    active_count = len([t for t in tasks if t.is_active])
    approval_count = len([t for t in tasks if t.needs_approval])
    typer.echo("-" * 50)
    typer.echo("Total: {} | Active: {} | Pending approval: {}".format(
        len(tasks), active_count, approval_count
    ))


@app.command()
def show(task_id: str):
    """Show task details."""
    telemetry = TelemetryService()
    engine = TaskEngine(telemetry)
    task = engine.get_task(task_id)

    if not task:
        typer.echo("Task {} not found.".format(task_id))
        return

    typer.echo("\n\U0001f4cb Task: {}".format(task.name))
    typer.echo("Status: {}".format(task.status.value.upper()))
    typer.echo("Progress: {}".format(task.progress_text))
    typer.echo("Created: {}".format(task.created_at))
    typer.echo("Description: {}".format(task.description or "-"))
    typer.echo("\nSteps:")
    for step in task.steps:
        icon = "\u2705" if step.status == TaskStatus.COMPLETED else "\u23f3"
        typer.echo("  {} {}".format(icon, step.name))

    if task.needs_approval:
        typer.echo("\n\u26a0\ufe0f Approval required")


@app.command()
def approve(task_id: str):
    """Approve a task (placeholder)."""
    typer.echo("Approving task: {} (TODO: connect to ApprovalManager)".format(task_id))


@app.command()
def deny(task_id: str):
    """Deny a task (placeholder)."""
    typer.echo("Denying task: {} (TODO: connect to ApprovalManager)".format(task_id))
