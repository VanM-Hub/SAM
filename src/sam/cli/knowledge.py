"""
sam knowledge — Knowledge Store, show, search, recommend.
"""

import typer
from ..operations.engine.knowledge import KnowledgeEngine
from ..telemetry.service import TelemetryService

app = typer.Typer()


@app.callback(invoke_without_command=True)
def knowledge(ctx: typer.Context):
    """Tampilkan status knowledge store (default)."""
    if ctx.invoked_subcommand is not None:
        return

    telemetry = TelemetryService()
    engine = KnowledgeEngine(telemetry)
    model = engine.get_knowledge()

    typer.echo("\n\U0001f9e0 Knowledge Summary")
    typer.echo("-" * 50)
    typer.echo("Total entries: {}".format(model.total_entries))
    typer.echo("Recommendations: {}".format(model.recommendation_count))
    typer.echo("Insights: {}".format(model.insight_count))
    typer.echo("---")

    if model.insights:
        typer.echo("\nInsights:")
        for insight in model.insights:
            typer.echo("  \U0001f4a1 {} ({})".format(insight.title, insight.severity))
            typer.echo("     {}...".format(insight.description[:80]))


@app.command()
def stats():
    """Tampilkan statistik knowledge."""
    telemetry = TelemetryService()
    engine = KnowledgeEngine(telemetry)
    model = engine.get_knowledge()

    typer.echo("\n\U0001f4ca Knowledge Stats")
    typer.echo("-" * 50)
    typer.echo("Total: {}".format(model.total_entries))
    typer.echo("Recommendations: {}".format(model.recommendation_count))
    typer.echo("Insights: {}".format(model.insight_count))

    # Count by type
    type_counts = {}
    for e in model.entries:
        type_counts[e.type.value] = type_counts.get(e.type.value, 0) + 1
    for t, c in sorted(type_counts.items()):
        typer.echo("  {}: {}".format(t, c))


@app.command()
def show():
    """Show knowledge summary."""
    telemetry = TelemetryService()
    engine = KnowledgeEngine(telemetry)
    model = engine.get_knowledge()

    typer.echo("\n\U0001f9e0 Knowledge Summary")
    typer.echo("-" * 50)
    typer.echo("Total entries: {}".format(model.total_entries))
    typer.echo("Recommendations: {}".format(model.recommendation_count))
    typer.echo("Insights: {}".format(model.insight_count))
    typer.echo("\nInsights:")
    for insight in model.insights:
        typer.echo("  \U0001f4a1 {} ({})".format(insight.title, insight.severity))
        typer.echo("     {}...".format(insight.description[:80]))


@app.command()
def search(query: str):
    """Search knowledge."""
    telemetry = TelemetryService()
    engine = KnowledgeEngine(telemetry)
    results = engine.search(query)

    if not results:
        typer.echo("No results for '{}'".format(query))
        return

    typer.echo("\n\U0001f50d Search results for '{}':".format(query))
    for entry in results[:10]:
        typer.echo("  \U0001f4cc {}".format(entry.title))
        typer.echo("     {}...".format(entry.content[:100]))


@app.command()
def recommend():
    """Show recommendations."""
    telemetry = TelemetryService()
    engine = KnowledgeEngine(telemetry)
    recs = engine.get_recommendations()

    if not recs:
        typer.echo("No recommendations available.")
        return

    typer.echo("\n\U0001f4a1 Recommendations:")
    for rec in recs:
        typer.echo("  \U0001f4a1 {}".format(rec.title))
        typer.echo("     {}...".format(rec.content[:100]))
