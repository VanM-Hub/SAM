"""
CLI commands for settings.
"""

import typer
from ..operations.engine.settings import SettingsEngine

app = typer.Typer()


@app.command()
def list():
    """List all settings."""
    engine = SettingsEngine()
    model = engine.get_settings()

    typer.echo("\n\u2699\ufe0f Settings")
    typer.echo("=" * 50)

    for section in model.sections:
        typer.echo("\n[{}] {}".format(section.category.value.upper(), section.name))
        typer.echo("-" * 30)
        for item in section.items:
            typer.echo("  {}: {}".format(item.key, item.value))

    typer.echo("=" * 50)


@app.command()
def get(key: str):
    """Get a setting value."""
    engine = SettingsEngine()
    model = engine.get_settings()

    for section in model.sections:
        for item in section.items:
            if item.key == key:
                typer.echo(item.value)
                return

    typer.echo("Setting '{}' not found.".format(key), err=True)


@app.command()
def set(key: str, value: str):
    """Set a setting value."""
    engine = SettingsEngine()
    # Konversi value ke tipe yang sesuai
    if value.lower() in ["true", "false"]:
        value = value.lower() == "true"
    elif value.isdigit():
        value = int(value)
    elif value.replace(".", "").isdigit():
        value = float(value)

    success = engine.update_setting(key, value)
    if success:
        typer.echo("\u2705 {} = {}".format(key, value))
    else:
        typer.echo("\u274c Failed to update {}".format(key))
