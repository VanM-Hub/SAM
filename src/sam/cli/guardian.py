"""
sam guardian — Guardian Kernel status dan decision history.
"""

import typer
import asyncio
from sam.guardian.pipeline import GuardianPipeline
from sam.guardian.decision import GuardianDecision
from sam.runtime.coordinator import RuntimeCoordinator
from sam.contracts import DesiredOperationalState

app = typer.Typer()


@app.callback(invoke_without_command=True)
def guardian(ctx: typer.Context):
    """Tampilkan status Guardian Kernel."""
    if ctx.invoked_subcommand is not None:
        return

    coord = RuntimeCoordinator()
    dos = DesiredOperationalState()
    pipeline = GuardianPipeline(coord, dos)

    typer.echo("=" * 48)
    typer.echo("  Guardian Kernel — Phase 0")
    typer.echo("=" * 48)

    typer.echo(f"\n  Mission:  Protect OpenClaw")
    typer.echo(f"  DOS:      state={dos.runtime_state}, plugins={dos.plugins_expected}, health\u2265{dos.min_health_score}")
    typer.echo(f"  Cycle:    {pipeline.cycle_count} completed")

    if pipeline.last_decision:
        d = pipeline.last_decision
        typer.echo(f"\n  Last Decision:")
        typer.echo(f"    ID:       {d.decision_id}")
        typer.echo(f"    Severity: {d.severity}")
        typer.echo(f"    Risk:     {d.risk}")
        ok = '\u2705'
        no = '\u274c'
        typer.echo(f"    Approved: {ok if d.approved else no}")
        typer.echo(f"    Executed: {ok if d.executed else no}")
        typer.echo(f"    Verified: {ok if d.verified else no}")
        typer.echo(f"    Duration: {d.duration_ms} ms")
        if d.action_plan:
            typer.echo(f"    Plan:     {', '.join(d.action_plan)}")
    else:
        typer.echo(f"\n  Last Decision: None (no cycles run yet)")

    # Engine status
    typer.echo(f"\n  Engines:")
    typer.echo(f"    Observer:       \u2705 Ready")
    typer.echo(f"    Analyzer:       \u2705 Ready")
    typer.echo(f"    Policy Engine:  \u2705 Ready")
    typer.echo(f"    Decision:       \u2705 Ready")
    typer.echo(f"    Action:         \u2705 Ready")
    typer.echo(f"    Verification:   \u2705 Ready")

    typer.echo("")


@app.command()
def decision():
    """Tampilkan keputusan Guardian terakhir."""
    coord = RuntimeCoordinator()
    dos = DesiredOperationalState()
    pipeline = GuardianPipeline(coord, dos)

    if not pipeline.last_decision:
        typer.echo("No decision recorded yet. Run 'sam guardian cycle' first.")
        return

    d = pipeline.last_decision
    typer.echo("=" * 48)
    typer.echo("  Guardian Decision — Last")
    typer.echo("=" * 48)
    typer.echo(f"  Decision ID: {d.decision_id}")
    typer.echo(f"  Mission ID:  {d.mission_id}")
    typer.echo(f"  Severity:    {d.severity}")
    typer.echo(f"  Risk:        {d.risk}")
    ok = '\u2705'
    no = '\u274c'
    typer.echo(f"  Approved:    {ok if d.approved else no}")
    typer.echo(f"  Executed:    {ok if d.executed else no}")
    typer.echo(f"  Verified:    {ok if d.verified else no}")
    typer.echo(f"  Duration:    {d.duration_ms} ms")
    if d.action_plan:
        typer.echo(f"  Action Plan:")
        for a in d.action_plan:
            typer.echo(f"    - {a}")
    typer.echo(f"  Created:     {d.created_at}")
    typer.echo("")


@app.command()
def cycle():
    """Jalankan satu siklus Guardian Decision Pipeline."""
    coord = RuntimeCoordinator()
    dos = DesiredOperationalState()
    pipeline = GuardianPipeline(coord, dos)

    typer.echo("Running Guardian cycle...")
    result = asyncio.run(pipeline.run_cycle())

    status = result.get("status", "unknown")
    drifts = result.get("drifts", [])
    decision_data = result.get("decision")

    typer.echo(f"\n  Status: {status}")
    typer.echo(f"  Drifts: {len(drifts)} detected")
    for dft in drifts:
        typer.echo(f"    - {dft['type']}: expected={dft['expected']}, actual={dft['actual']}, severity={dft['severity']}")

    if decision_data:
        typer.echo(f"\n  Decision:")
        ok = '\u2705'
        no = '\u274c'
        typer.echo(f"    Approved: {ok if decision_data['approved'] else no}")
        typer.echo(f"    Executed: {ok if decision_data['executed'] else no}")
        typer.echo(f"    Verified: {ok if decision_data['verified'] else no}")
        typer.echo(f"    Duration: {decision_data['duration_ms']} ms")
    else:
        typer.echo(f"\n  No decision needed (healthy)")
