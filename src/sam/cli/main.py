"""
SAM Operations Console CLI — Phase 1
====================================

Entry point: python -m sam.cli.main [command]
"""

import typer
from sam.cli import status, health, session, runtime, plugins
from sam.cli import knowledge, memory, workflow, events, guardian
from sam.cli import service, logs, metrics, openclaw, intelligence
from sam.cli import autonomous
from sam.cli import history as history_cli
from sam.cli import settings as settings_cli
from sam.cli import task as task_cli
from sam.cli import explain as explain_cli
from sam.cli import onboarding as onboarding_cli

app = typer.Typer(
    name="sam",
    help="SAM Framework — Operations Console",
    no_args_is_help=True,
)

# Register commands
app.add_typer(status.app, name="status", help="Tampilkan status Runtime")
app.add_typer(health.app, name="health", help="Tampilkan status kesehatan")
app.add_typer(session.app, name="session", help="Kelola session runtime")
app.add_typer(runtime.app, name="runtime", help="Runtime Container Tree")
app.add_typer(plugins.app, name="plugins", help="Daftar plugin runtime")
app.add_typer(knowledge.app, name="knowledge", help="Knowledge Store")
app.add_typer(memory.app, name="memory", help="Memory Store")
app.add_typer(workflow.app, name="workflow", help="Workflow Engine")
app.add_typer(events.app, name="events", help="Event stream dan history")
app.add_typer(guardian.app, name="guardian", help="Guardian Kernel")
app.add_typer(service.app, name="service", help="Kelola service runtime")
app.add_typer(logs.app, name="logs", help="Tampilkan dan follow telemetry logs")
app.add_typer(metrics.app, name="metrics", help="Tampilkan metrics runtime")
app.add_typer(openclaw.app, name="openclaw", help="OpenClaw integration (discover, status, monitor)")
app.add_typer(intelligence.app, name="intelligence", help="Operational intelligence (incident, rca, recommend)")
app.add_typer(autonomous.app, name="autonomous", help="Autonomous operations (status, approve, deny, history)")
app.add_typer(history_cli.app, name="history", help="View and search history")
app.add_typer(task_cli.app, name="task", help="Task management (list, show, approve, deny)")
app.add_typer(settings_cli.app, name="settings", help="View and manage settings (list, get, set)")
app.add_typer(explain_cli.app, name="explain", help="Explain events (explain, recent)")
app.add_typer(onboarding_cli.app, name="onboarding", help="SAM onboarding (init, doctor, version)")


@app.command()
def web(
    host: str = typer.Option("127.0.0.1", "--host", "-H", help="Bind address"),
    port: int = typer.Option(8080, "--port", "-p", help="Port"),
):
    """Start Operations Console web dashboard."""
    from sam.web.server import run_server
    typer.echo("Starting SAM Operations Console on http://{0}:{1}".format(host, port))
    run_server(host=host, port=port)


def main():
    app()


if __name__ == "__main__":
    main()
