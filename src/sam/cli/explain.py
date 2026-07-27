"""
CLI commands for explainability.
"""

import typer
from ..operations.engine.explain import ExplainabilityEngine
from ..telemetry.service import TelemetryService

app = typer.Typer()


@app.command()
def explain(event_id: str):
    """Explain an event."""
    telemetry = TelemetryService()
    engine = ExplainabilityEngine(telemetry)
    explanation = engine.explain_event(event_id)

    if not explanation:
        typer.echo("Event {} not found or cannot be explained.".format(event_id))
        return

    typer.echo("\n\U0001f50d Explanation")
    typer.echo("=" * 60)
    typer.echo("Title: {}".format(explanation.title))
    typer.echo("Severity: {}".format(explanation.severity.value.upper()))
    typer.echo("")
    typer.echo("Why? {}".format(explanation.why))
    if explanation.impact:
        typer.echo("Impact: {}".format(explanation.impact.description))
    if explanation.recommendation:
        typer.echo("Recommendation: {}".format(explanation.recommendation.description))
    typer.echo("")
    typer.echo("Evidence:")
    for ev in explanation.evidence[:3]:
        typer.echo("  \u2022 {}".format(ev.description))
    typer.echo("=" * 60)


@app.command()
def recent(limit: int = 10):
    """Explain recent events."""
    telemetry = TelemetryService()
    engine = ExplainabilityEngine(telemetry)
    explanations = engine.explain_recent(limit=limit)

    if not explanations:
        typer.echo("No recent events to explain.")
        return

    typer.echo("\n\U0001f50d Recent Explanations")
    typer.echo("=" * 60)
    for exp in explanations:
        time_str = exp.timestamp.strftime("%H:%M:%S")
        typer.echo("{} [{}] {}".format(
            time_str, exp.severity.value.upper(), exp.title
        ))
        typer.echo("  Why: {}...".format(exp.why[:80]))
        if exp.recommendation:
            typer.echo("  Recommendation: {}...".format(
                exp.recommendation.description[:60]
            ))
        typer.echo("")
    typer.echo("=" * 60)
