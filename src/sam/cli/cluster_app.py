"""CLI for Cross-Cluster Intelligence.

Commands:
    sam cluster status              — cluster cognitive state
    sam cluster insights list       — list insights
    sam cluster strategies list     — list strategy proposals
    sam cluster strategies vote     — vote on proposal
    sam cluster sync                — force sync
    sam cluster knowledge pull      — pull knowledge
"""

from __future__ import annotations

import asyncio
import json
import structlog
from typing import Optional

import typer

from sam.cluster.knowledge_share import (
    ClusterKnowledgeShare,
)
from sam.cluster.insight_broker import InsightBroker
from sam.cluster.strategy_sync import (
    ClusterStrategySync,
    VOTE_APPROVE,
    VOTE_REJECT,
)
from sam.cluster.cognitive_state import (
    ClusterCognitiveStateManager,
)
from sam.cluster.learning_aggregator import LearningAggregator

logger = structlog.get_logger()


def _run_async(coro):
    """Run a coroutine safely whether an event loop is running or not."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)
    future = asyncio.run_coroutine_threadsafe(coro, loop)
    return future.result()


# ── Global in-memory instances ─────────────────────────────────

_db_knowledge: Optional[ClusterKnowledgeShare] = None
_db_insights: Optional[InsightBroker] = None
_db_strategies: Optional[ClusterStrategySync] = None
_db_cognitive: Optional[ClusterCognitiveStateManager] = None
_db_aggregator: Optional[LearningAggregator] = None


def _get_knowledge() -> ClusterKnowledgeShare:
    global _db_knowledge
    if _db_knowledge is None:
        _db_knowledge = ClusterKnowledgeShare()
    return _db_knowledge


def _get_insights() -> InsightBroker:
    global _db_insights
    if _db_insights is None:
        _db_insights = InsightBroker()
    return _db_insights


def _get_strategies() -> ClusterStrategySync:
    global _db_strategies
    if _db_strategies is None:
        _db_strategies = ClusterStrategySync()
    return _db_strategies


def _get_cognitive() -> ClusterCognitiveStateManager:
    global _db_cognitive
    if _db_cognitive is None:
        _db_cognitive = ClusterCognitiveStateManager()
    return _db_cognitive


def _get_aggregator() -> LearningAggregator:
    global _db_aggregator
    if _db_aggregator is None:
        _db_aggregator = LearningAggregator(
            knowledge_share=_get_knowledge(),
            insight_broker=_get_insights(),
            strategy_sync=_get_strategies(),
        )
    return _db_aggregator


# ── Sub-app ─────────────────────────────────────────────────────

cluster_app = typer.Typer(
    name="cluster",
    help="Cross-cluster intelligence commands",
)


# ── status ──────────────────────────────────────────────────────

@cluster_app.command(name="status")
def cluster_status(
    json_output: bool = typer.Option(False, "--json", "-j", help="JSON output"),
):
    """Display cluster cognitive state."""
    ccm = _get_cognitive()
    state = _run_async(ccm.get_cluster_state())

    if json_output:
        typer.echo(json.dumps(state.to_dict(), indent=2, default=str))
        return

    typer.echo("=== Cluster Status ===")
    typer.echo(f"  Nodes       : {state.node_count}")
    typer.echo(f"  Confidence  : {state.aggregated_confidence:.1f}%")
    typer.echo(f"  Focus       : {state.dominant_focus}")
    typer.echo(f"  Autonomy    : {state.avg_autonomy_level:.2f}")
    typer.echo(f"  Timestamp   : {state.timestamp.isoformat()}")


# ── insights list ───────────────────────────────────────────────

@cluster_app.command(name="insights-list")
def insights_list(
    node_id: str = typer.Option("", "--node", "-n", help="Filter by node ID"),
    insight_type: str = typer.Option("", "--type", "-t", help="Filter by type"),
    limit: int = typer.Option(20, "--limit", "-l", help="Max results"),
    json_output: bool = typer.Option(False, "--json", "-j", help="JSON output"),
):
    """List insights from the cluster."""
    broker = _get_insights()
    node = node_id if node_id else None
    itype = insight_type if insight_type else None
    insights = _run_async(broker.get_insights(
        node_id=node,
        insight_type=itype,
        limit=limit,
    ))

    if json_output:
        typer.echo(json.dumps([i.to_dict() for i in insights], indent=2, default=str))
        return

    if not insights:
        typer.echo("No insights found.")
        return

    typer.echo(f"Cluster Insights ({len(insights)} found):")
    typer.echo("-" * 60)
    for ins in insights:
        typer.echo(f"  [{ins.insight_type}] {ins.id} from {ins.node_id}")
        typer.echo(f"    Confidence: {ins.confidence} | {ins.timestamp.isoformat()}")
    typer.echo("-" * 60)


# ── strategies ──────────────────────────────────────────────────

@cluster_app.command(name="strategies-list")
def strategies_list(
    status: str = typer.Option("", "--status", "-s", help="Filter: PROPOSED|APPROVED|REJECTED"),
    limit: int = typer.Option(20, "--limit", "-l", help="Max results"),
    json_output: bool = typer.Option(False, "--json", "-j", help="JSON output"),
):
    """List strategy proposals."""
    sync = _get_strategies()
    st = status if status else None
    proposals = _run_async(sync.get_proposals(status=st, limit=limit))

    if json_output:
        typer.echo(json.dumps([p.to_dict() for p in proposals], indent=2, default=str))
        return

    if not proposals:
        typer.echo("No strategy proposals found.")
        return

    typer.echo(f"Strategy Proposals ({len(proposals)} found):")
    typer.echo("-" * 60)
    for p in proposals:
        approves = p.approve_count()
        rejects = p.reject_count()
        typer.echo(f"  [{p.status}] {p.id} by {p.proposer_node_id}")
        typer.echo(f"    Votes: {approves} approve, {rejects} reject")
        typer.echo(f"    {p.timestamp.isoformat()}")
    typer.echo("-" * 60)


@cluster_app.command(name="strategies-vote")
def strategies_vote(
    proposal_id: str = typer.Argument(..., help="Proposal ID"),
    node: str = typer.Option("cli", "--node", "-n", help="Voting node ID"),
    approve: bool = typer.Option(False, "--approve", "-a", help="Vote approve"),
    reject: bool = typer.Option(False, "--reject", "-r", help="Vote reject"),
    reason: str = typer.Option("", "--reason", "-m", help="Vote reason"),
):
    """Vote on a strategy proposal."""
    if approve and reject:
        typer.echo("Cannot both --approve and --reject.")
        raise typer.Exit(1)
    if not approve and not reject:
        typer.echo("Specify --approve or --reject.")
        raise typer.Exit(1)

    sync = _get_strategies()
    vote = VOTE_APPROVE if approve else VOTE_REJECT
    try:
        _run_async(sync.vote(proposal_id, node, vote, reason))
        typer.echo(f"Vote '{vote}' cast by {node} on {proposal_id}.")
    except ValueError as e:
        typer.echo(f"Error: {e}")
        raise typer.Exit(1)


# ── sync ────────────────────────────────────────────────────────

@cluster_app.command(name="sync")
def cluster_sync(
    json_output: bool = typer.Option(False, "--json", "-j", help="JSON output"),
):
    """Force cluster knowledge sync/aggregation."""
    agg = _get_aggregator()
    result = _run_async(agg.update_cluster_knowledge())

    if json_output:
        typer.echo(json.dumps(result, indent=2))
        return

    typer.echo("Cluster sync complete.")
    for ktype, count in result.items():
        typer.echo(f"  {ktype}: {count} items")


# ── knowledge pull ──────────────────────────────────────────────

@cluster_app.command(name="knowledge-pull")
def knowledge_pull(
    node_id: str = typer.Argument(..., help="Source node ID"),
    json_output: bool = typer.Option(False, "--json", "-j", help="JSON output"),
):
    """Pull knowledge from a specific node."""
    ks = _get_knowledge()
    items = _run_async(ks.pull(node_id))

    if json_output:
        typer.echo(json.dumps([i.to_dict() for i in items], indent=2, default=str))
        return

    if not items:
        typer.echo(f"No pending knowledge from node {node_id}.")
        return

    typer.echo(f"Pulled {len(items)} items from {node_id}:")
    for item in items:
        typer.echo(f"  [{item.knowledge_type}] {item.id} (conf={item.confidence})")


if __name__ == "__main__":
    cluster_app()
