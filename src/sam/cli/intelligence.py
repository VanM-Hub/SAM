"""
sam intelligence — Deteksi insiden, RCA, dan rekomendasi.
"""

import typer
import asyncio
from ..intelligence.detector import IncidentDetector
from ..intelligence.rca import RootCauseAnalyzer
from ..intelligence.recommender import Recommender
from ..intelligence.knowledge import KnowledgeLookup
from ..intelligence.models import Incident, IncidentSeverity

app = typer.Typer()


def _format_severity(severity) -> str:
    """Format severity dengan icon."""
    icons = {
        "critical": "💀",
        "high": "🔴",
        "medium": "🟡",
        "low": "🟢",
    }
    return "{0} {1}".format(icons.get(severity.value, "❓"), severity.value.upper())


@app.command()
def incident(
    workspace: str = typer.Option("./workspace", "--workspace", "-w", help="Path workspace"),
    log_lines: int = typer.Option(200, "--lines", "-n", help="Baris log yang dianalisis"),
):
    """Deteksi insiden dari log dan health OpenClaw."""
    detector = IncidentDetector(workspace)
    incidents = asyncio.run(detector.detect(log_lines=log_lines))

    if not incidents:
        typer.echo("✅ No incidents detected.")
        return

    typer.echo("Detected Incidents:")
    typer.echo("-" * 48)

    for inc in incidents:
        sev_str = _format_severity(inc.severity)
        typer.echo("\n  {0} [{1}]".format(sev_str, inc.source))
        typer.echo("     ID: {0}".format(inc.id))
        typer.echo("     Title: {0}".format(inc.title))
        if inc.description:
            desc = inc.description[:120]
            typer.echo("     Detail: {0}".format(desc + ("..." if len(inc.description) > 120 else "")))
        typer.echo("     Evidence: {0} items".format(len(inc.evidence)))

    typer.echo("\n{0} incident(s) found.".format(len(incidents)))


@app.command()
def rca(
    incident_id: str = typer.Argument(..., help="ID insiden untuk dianalisis"),
    title: str = typer.Option("Unknown incident", "--title", "-t", help="Judul insiden"),
    description: str = typer.Option("", "--desc", "-d", help="Deskripsi insiden"),
    severity: str = typer.Option("medium", "--severity", "-s", help="Severity (critical/high/medium/low)"),
):
    """Analisis root cause untuk insiden tertentu."""
    # Parse severity
    try:
        sev = IncidentSeverity(severity.lower())
    except ValueError:
        typer.echo("Invalid severity. Valid: critical, high, medium, low")
        raise typer.Exit(code=1)

    incident = Incident(
        id=incident_id,
        title=title,
        description=description,
        severity=sev,
        source="cli",
    )

    analyzer = RootCauseAnalyzer()
    causes = asyncio.run(analyzer.analyze(incident))

    if not causes:
        typer.echo("No root causes identified.")
        return

    typer.echo("Root Cause Analysis for incident: {0}".format(incident_id))
    typer.echo("-" * 48)

    for i, cause in enumerate(causes, 1):
        conf_pct = cause.confidence * 100
        bar = "█" * int(conf_pct // 10) + "░" * (10 - int(conf_pct // 10))
        typer.echo("\n  #{0} (confidence: {1:.0f}%)".format(i, conf_pct))
        typer.echo("     {0}".format(bar))
        typer.echo("     Cause: {0}".format(cause.cause))
        if cause.recommendation:
            typer.echo("     Recommendation: {0}".format(cause.recommendation))
        if cause.evidence:
            for ev in cause.evidence[:2]:
                typer.echo("     Evidence: {0}".format(ev[:100]))

    typer.echo("\nTop cause: #{0} — {1}".format(1, causes[0].cause[:60]))


@app.command()
def recommend(
    incident_id: str = typer.Argument(..., help="ID insiden"),
    title: str = typer.Option("Sample incident", "--title", "-t", help="Judul insiden"),
    description: str = typer.Option("", "--desc", "-d", help="Deskripsi"),
    severity: str = typer.Option("medium", "--severity", "-s", help="Severity"),
):
    """Dapatkan rekomendasi perbaikan untuk insiden."""
    try:
        sev = IncidentSeverity(severity.lower())
    except ValueError:
        typer.echo("Invalid severity.")
        raise typer.Exit(code=1)

    incident = Incident(
        id=incident_id,
        title=title,
        description=description,
        severity=sev,
        source="cli",
    )

    analyzer = RootCauseAnalyzer()
    recommender_engine = Recommender()

    causes = asyncio.run(analyzer.analyze(incident))
    recommendations = asyncio.run(recommender_engine.recommend(incident, causes))

    if not recommendations:
        typer.echo("No recommendations available.")
        return

    typer.echo("Recommendations for incident: {0}".format(incident_id))
    typer.echo("-" * 48)

    for i, rec in enumerate(recommendations, 1):
        risk_icon = "🔴" if rec.risk == "high" else "🟡" if rec.risk == "medium" else "🟢"
        typer.echo(
            "\n  {0} #{1} (confidence: {2:.0f}%, risk: {3})".format(
                risk_icon, i, rec.confidence * 100, rec.risk.upper()
            )
        )
        typer.echo("     {0}".format(rec.title))
        if rec.description:
            typer.echo("     {0}".format(rec.description[:100]))
        typer.echo("     Steps:")
        for j, step in enumerate(rec.steps, 1):
            typer.echo("       {0}. {1}".format(j, step))


@app.command()
def knowledge(
    query: str = typer.Argument(..., help="Kata kunci pencarian"),
):
    """Cari knowledge terkait insiden."""
    lookup = KnowledgeLookup()
    results = asyncio.run(lookup.search(query))

    if not results:
        typer.echo("No knowledge found for: {0}".format(query))
        return

    typer.echo("Knowledge entries for: {0}".format(query))
    typer.echo("-" * 48)

    for entry in results:
        conf_pct = entry.get("confidence", 0) * 100
        typer.echo("\n  [{0}] (confidence: {1:.0f}%)".format(entry.get("id", "??"), conf_pct))
        typer.echo("     {0}".format(entry.get("fact", "No fact")))
        tags = entry.get("tags", [])
        if tags:
            typer.echo("     Tags: {0}".format(", ".join(tags)))
