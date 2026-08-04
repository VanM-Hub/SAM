"""CLI for Autonomous Runtime & Operational Safety.

Commands:
    sam autonomy status              — current autonomy level
    sam autonomy set <level>         — set autonomy level
    sam autonomy history             — autonomy change history
    sam autonomy guardrails          — list active guardrails
    sam autonomy escalate <issue>    — escalate to human
    sam autonomy degrade             — degrade autonomy
    sam autonomy upgrade             — upgrade autonomy
"""

from __future__ import annotations

import asyncio
import json
import structlog
from typing import Optional

import typer

from sam.autonomy.controller import AutonomyController
from sam.autonomy.models import AutonomyLevel
from sam.autonomy.guardrails import Guardrails
from sam.autonomy.escalation import EscalationManager
from sam.autonomy.degradation import GracefulDegradation

logger = structlog.get_logger()


def _run_async(coro):
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)
    future = asyncio.run_coroutine_threadsafe(coro, loop)
    return future.result()


_db_ctrl: Optional[AutonomyController] = None
_db_guard: Optional[Guardrails] = None
_db_esc: Optional[EscalationManager] = None
_db_degrade: Optional[GracefulDegradation] = None


def _get_ctrl() -> AutonomyController:
    global _db_ctrl
    if _db_ctrl is None:
        _db_ctrl = AutonomyController()
    return _db_ctrl


def _get_guard() -> Guardrails:
    global _db_guard
    if _db_guard is None:
        _db_guard = Guardrails()
    return _db_guard


def _get_esc() -> EscalationManager:
    global _db_esc
    if _db_esc is None:
        _db_esc = EscalationManager()
    return _db_esc


def _get_degrade() -> GracefulDegradation:
    global _db_degrade
    if _db_degrade is None:
        _db_degrade = GracefulDegradation()
    return _db_degrade


autonomy_app = typer.Typer(name="autonomy", help="Autonomy & safety commands")


@autonomy_app.command(name="status")
def autonomy_status(json_output: bool = typer.Option(False, "--json", "-j")):
    ctrl = _get_ctrl()
    level = _run_async(ctrl.get_current_level())
    if json_output:
        typer.echo(json.dumps({"level": level.value, "numeric": level.numeric}))
        return
    typer.echo(f"Current autonomy level: {level.value} (level {level.numeric}/5)")


@autonomy_app.command(name="set")
def autonomy_set(
    level: str = typer.Argument(..., help="observe|recommend|assist|supervise|autonomous"),
    reason: str = typer.Option("CLI override", "--reason", "-r"),
):
    ctrl = _get_ctrl()
    try:
        lvl = AutonomyLevel(level)
    except ValueError:
        typer.echo(f"Invalid level: {level}. Choose: observe, recommend, assist, supervise, autonomous")
        raise typer.Exit(1)
    _run_async(ctrl.set_level(lvl, reason))
    typer.echo(f"Autonomy set to {lvl.value}")


@autonomy_app.command(name="history")
def autonomy_history(
    limit: int = typer.Option(20, "--limit", "-l"),
    json_output: bool = typer.Option(False, "--json", "-j"),
):
    ctrl = _get_ctrl()
    history = _run_async(ctrl.get_autonomy_history(limit=limit))
    if json_output:
        typer.echo(json.dumps(history, indent=2, default=str))
        return
    if not history:
        typer.echo("No autonomy history.")
        return
    typer.echo("Autonomy History:")
    typer.echo("-" * 50)
    for h in history:
        typer.echo(f"  {h['old_level']} -> {h['new_level']}: {h['reason']} ({h['timestamp']})")


@autonomy_app.command(name="guardrails")
def autonomy_guardrails(json_output: bool = typer.Option(False, "--json", "-j")):
    guard = _get_guard()
    rules = _run_async(guard.get_active_guardrails())
    if json_output:
        typer.echo(json.dumps([r.to_dict() for r in rules], indent=2))
        return
    if not rules:
        typer.echo("No active guardrails.")
        return
    typer.echo(f"Active Guardrails ({len(rules)}):")
    typer.echo("-" * 50)
    for r in rules:
        typer.echo(f"  {r.name}: {r.description} ({r.on_violation})")


@autonomy_app.command(name="escalate")
def autonomy_escalate(
    issue: str = typer.Argument(..., help="Issue description"),
    reason: str = typer.Option("", "--reason", "-r"),
):
    esc = _get_esc()
    req = _run_async(esc.escalate(issue, reason))
    typer.echo(f"Escalation created: {req.id}")


@autonomy_app.command(name="degrade")
def autonomy_degrade(reason: str = typer.Option("CLI degrade", "--reason", "-r")):
    ctrl = _get_ctrl()
    deg = _get_degrade()
    current = _run_async(ctrl.get_current_level())
    new_level = _run_async(deg.degrade(current, reason))
    _run_async(ctrl.set_level(new_level, reason))
    typer.echo(f"Degraded to {new_level.value}")


@autonomy_app.command(name="upgrade")
def autonomy_upgrade(reason: str = typer.Option("CLI upgrade", "--reason", "-r")):
    ctrl = _get_ctrl()
    deg = _get_degrade()
    current = _run_async(ctrl.get_current_level())
    new_level = _run_async(deg.upgrade(current, reason))
    _run_async(ctrl.set_level(new_level, reason))
    typer.echo(f"Upgraded to {new_level.value}")
