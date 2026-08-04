"""CLI for Knowledge Federation.

Commands:
    sam federation status              — federation status
    sam federation clusters            — list peer clusters
"""

from __future__ import annotations

import asyncio
import json
import structlog
from typing import Optional

import typer

from sam.federation.manager import FederationManager
from sam.federation.trust import TrustManager

logger = structlog.get_logger()


def _run_async(coro):
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)
    future = asyncio.run_coroutine_threadsafe(coro, loop)
    return future.result()


_db_fed: Optional[FederationManager] = None
_db_trust: Optional[TrustManager] = None


def _get_fed() -> FederationManager:
    global _db_fed
    if _db_fed is None:
        _db_fed = FederationManager()
    return _db_fed


def _get_trust() -> TrustManager:
    global _db_trust
    if _db_trust is None:
        _db_trust = TrustManager()
    return _db_trust


federation_app = typer.Typer(
    name="federation",
    help="Knowledge federation commands",
)


@federation_app.command(name="status")
def federation_status(
    json_output: bool = typer.Option(False, "--json", "-j", help="JSON output"),
):
    """Display federation status."""
    fed = _get_fed()
    local_id = _run_async(fed.get_local_cluster_id())
    cluster_count = _run_async(fed.count())

    if json_output:
        typer.echo(json.dumps({
            "local_cluster_id": local_id,
            "peer_count": cluster_count,
        }, indent=2))
        return

    typer.echo("=== Federation Status ===")
    typer.echo(f"  Local cluster: {local_id}")
    typer.echo(f"  Peers         : {cluster_count}")


@federation_app.command(name="clusters")
def federation_clusters(
    status: str = typer.Option("", "--status", "-s", help="Filter by status"),
    json_output: bool = typer.Option(False, "--json", "-j", help="JSON output"),
):
    """List peer clusters."""
    fed = _get_fed()
    st = status if status else None
    clusters = _run_async(fed.list_clusters(status=st))

    if json_output:
        typer.echo(json.dumps([c.to_dict() for c in clusters], indent=2, default=str))
        return

    if not clusters:
        typer.echo("No peer clusters registered.")
        return

    typer.echo(f"Peer Clusters ({len(clusters)} found):")
    typer.echo("-" * 50)
    for c in clusters:
        typer.echo(f"  {c.id}: {c.name} ({c.status}, trust={c.trust_score:.2f})")
