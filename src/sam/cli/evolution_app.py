"""CLI for evolution proposal management.

Commands:
    sam evolution list          — list pending proposals
    sam evolution approve <id>  — approve and apply a proposal
    sam evolution reject <id>   — reject a proposal
    sam evolution show <id>     — show proposal details
"""

from __future__ import annotations

import asyncio
import json
import structlog
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import typer

from sam.evolution.policy import EvolutionPolicy, EvolutionProposal, ProposalStatus, ProposalType
from sam.evolution.params import ParamManager, OptimizableParam
from sam.evolution.optimizer import SelfOptimizer


logger = structlog.get_logger()


def _run_async(coro):
    """Run a coroutine safely whether an event loop is running or not."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)
    # Already inside an event loop (e.g. test or nested call)
    future = asyncio.run_coroutine_threadsafe(coro, loop)
    return future.result()


evolution_app = typer.Typer(
    name="evolution",
    help="Manage evolution proposals (list, approve, reject)",
)


# ── Global policy instance (created lazily) ────────────────────────
# In production this would come from dependency injection.
# For CLI, we create one with defaults.

_db_evolution_policy: Optional[EvolutionPolicy] = None
_db_optimizer: Optional[SelfOptimizer] = None


class _InMemoryDatabase:
    """Minimal in-memory Database mock for CLI."""
    async def execute(self, sql, params=None):
        pass


class _InMemoryParamManager:
    """Minimal in-memory ParamManager for CLI usage (no DB needed)."""
    def __init__(self):
        self._params: Dict[str, "OptimizableParam"] = {}
        self.db = _InMemoryDatabase()
    async def get(self, name: str) -> Optional["OptimizableParam"]:
        return self._params.get(name)
    def list(self) -> List[Any]:
        return list(self._params.values())
    async def register_defaults(self) -> None:
        pass
    async def set(self, name: str, value: Any) -> None:
        # Optimizer calls set with suggested_value directly
        # We need to update the current_value of the existing param
        from sam.evolution.params import OptimizableParam
        param = self._params.get(name)
        if param is not None:
            param.current_value = value
        else:
            self._params[name] = value


class _InMemoryInstitutionalMemory:
    """Minimal in-memory InstitutionalMemory for CLI / tests."""
    def __init__(self):
        self.stored = []
    async def search(self, query):
        return []
    async def store(self, entry):
        self.stored.append(entry)


def _get_evolution_policy() -> EvolutionPolicy:
    global _db_evolution_policy, _db_optimizer
    if _db_evolution_policy is None:
        pm = _InMemoryParamManager()
        _db_evolution_policy = EvolutionPolicy(param_manager=pm)

    if _db_optimizer is None:
        _db_optimizer = SelfOptimizer(
            institutional_memory=_InMemoryInstitutionalMemory(),
            param_manager=pm,
        )

    return _db_evolution_policy


def _get_optimizer() -> Optional[SelfOptimizer]:
    _get_evolution_policy()  # ensure initialized
    return _db_optimizer


def _format_proposal(proposal: "EvolutionProposal") -> str:
    """Format a single proposal for display."""
    lines = [
        f"  ID        : {proposal.id}",
        f"  Type      : {proposal.proposal_type.value}",
        f"  Status    : {proposal.status.value}",
        f"  Desc      : {proposal.description}",
    ]
    if proposal.param_name:
        lines.append(f"  Param     : {proposal.param_name}")
        lines.append(
            f"  Value     : {proposal.current_value} → {proposal.proposed_value}"
        )
    lines.append(f"  Confidence: {proposal.confidence:.2f}")
    lines.append(f"  Improve   : {proposal.expected_improvement:.1f}%")
    lines.append(f"  Risk      : {proposal.risk_level}")
    if proposal.rationale:
        lines.append(f"  Rationale : {proposal.rationale}")
    created = proposal.created_at.strftime("%Y-%m-%d %H:%M:%S UTC")
    lines.append(f"  Created   : {created}")
    return "\n".join(lines)


# ── Commands ───────────────────────────────────────────────────────


@evolution_app.command(name="list")
def evolution_list(
    status: Optional[str] = typer.Option(
        "pending", "--status", "-s",
        help="Filter by status: pending, approved, rejected, all",
    ),
    proposal_type: Optional[str] = typer.Option(
        None, "--type", "-t",
        help="Filter by type: parameter_tune, strategy_shift, template_mutation, architecture_change",
    ),
    limit: int = typer.Option(
        50, "--limit", "-l",
        help="Max proposals to show",
    ),
    json_output: bool = typer.Option(
        False, "--json", "-j",
        help="Output as JSON",
    ),
):
    """List evolution proposals with optional filters."""
    policy = _get_evolution_policy()

    status_filter: Optional[ProposalStatus] = None
    if status and status != "all":
        try:
            status_filter = ProposalStatus(status)
        except ValueError:
            typer.echo(f"❌ Invalid status: {status}. Choose: pending, approved, rejected, all")
            raise typer.Exit(1)

    type_filter: Optional[ProposalType] = None
    if proposal_type:
        try:
            type_filter = ProposalType(proposal_type)
        except ValueError:
            typer.echo(
                f"❌ Invalid type: {proposal_type}. "
                "Choose: parameter_tune, strategy_shift, template_mutation, architecture_change"
            )
            raise typer.Exit(1)

    proposals = policy.get_proposals(
        status=status_filter,
        proposal_type=type_filter,
        limit=limit,
    )

    if not proposals:
        typer.echo("No proposals found matching the given filters.")
        return

    if json_output:
        typer.echo(json.dumps([p.to_dict() for p in proposals], indent=2, default=str))
        return

    typer.echo(f"Evolution Proposals ({len(proposals)} found):")
    typer.echo("-" * 64)
    for idx, proposal in enumerate(proposals, start=1):
        status_label = {
            "pending": "[PENDING]",
            "approved": "[APPROVED]",
            "rejected": "[REJECTED]",
            "rolled_back": "[ROLLED BACK]",
            "superseded": "[SUPERSEDED]",
        }.get(proposal.status.value, "[UNKNOWN]")

        typer.echo(f"\n{status_label} Proposal #{idx}")
        typer.echo(_format_proposal(proposal))
    typer.echo("-" * 64)


@evolution_app.command(name="show")
def evolution_show(
    proposal_id: str = typer.Argument(..., help="Proposal ID to inspect"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output as JSON"),
):
    """Show detailed information for a single proposal."""
    policy = _get_evolution_policy()
    proposal = policy.get_proposal(proposal_id)

    if proposal is None:
        typer.echo(f"❌ Proposal not found: {proposal_id}")
        raise typer.Exit(1)

    if json_output:
        typer.echo(json.dumps(proposal.to_dict(), indent=2, default=str))
        return

    typer.echo(f"📄 Proposal Details")
    typer.echo("─" * 72)
    typer.echo(_format_proposal(proposal))

    # Show related pending count
    pending_count = policy.get_pending_count(proposal.proposal_type)
    typer.echo(f"\n  Other pending ({proposal.proposal_type.value}): {pending_count}")


@evolution_app.command(name="approve")
def evolution_approve(
    proposal_id: str = typer.Argument(
        ..., help="Proposal ID to approve and apply"
    ),
    force: bool = typer.Option(
        False, "--force", "-f",
        help="Force approve even if evaluation fails",
    ),
):
    """Approve a pending proposal and apply it (if PARAMETER_TUNE)."""
    policy = _get_evolution_policy()
    proposal = policy.get_proposal(proposal_id)

    if proposal is None:
        typer.echo(f"Proposal not found: {proposal_id}")
        raise typer.Exit(1)

    if proposal.status == ProposalStatus.APPROVED:
        typer.echo(f"Proposal {proposal_id} is already approved.")
        return

    if proposal.status == ProposalStatus.REJECTED and not force:
        typer.echo(
            f"Proposal {proposal_id} was rejected and --force not set. "
            "Use --force to override."
        )
        raise typer.Exit(1)

    try:
        optimizer = None
        if proposal.proposal_type == ProposalType.PARAMETER_TUNE:
            optimizer = _get_optimizer()

        _run_async(policy.approve(proposal, optimizer=optimizer))
        typer.echo(f"Proposal {proposal_id} approved and applied.")
        typer.echo(_format_proposal(proposal))

    except ValueError as exc:
        typer.echo(f"Failed to approve proposal: {exc}")
        raise typer.Exit(1)
    except Exception as exc:
        typer.echo(f"Unexpected error: {exc}")
        raise typer.Exit(1)


@evolution_app.command(name="reject")
def evolution_reject(
    proposal_id: str = typer.Argument(..., help="Proposal ID to reject"),
):
    """Reject a pending proposal without applying it."""
    policy = _get_evolution_policy()
    proposal = policy.get_proposal(proposal_id)

    if proposal is None:
        typer.echo(f"❌ Proposal not found: {proposal_id}")
        raise typer.Exit(1)

    _run_async(policy.reject(proposal))
    typer.echo(f"Proposal {proposal_id} rejected.")
    typer.echo(_format_proposal(proposal))


if __name__ == "__main__":
    evolution_app()
