"""Cluster Strategy Sync — Sprint 30.

Propose, vote, and adopt strategies across cluster nodes.
Consensus-based strategy adoption.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import structlog

logger = structlog.get_logger()


STATUS_PROPOSED = "PROPOSED"
STATUS_APPROVED = "APPROVED"
STATUS_REJECTED = "REJECTED"

VOTE_APPROVE = "approve"
VOTE_REJECT = "reject"
VOTE_ABSTAIN = "abstain"


@dataclass
class StrategyProposal:
    """A strategy proposed by a node for cluster-wide adoption.

    Attributes:
        id: Unique identifier.
        proposer_node_id: Node that proposed this strategy.
        strategy: Dict describing the strategic goal + plan.
        votes: List of {node_id, vote, reason} dicts.
        status: PROPOSED, APPROVED, or REJECTED.
        timestamp: When created.
    """
    id: str = ""
    proposer_node_id: str = ""
    strategy: Dict[str, Any] = field(default_factory=dict)
    votes: List[Dict[str, Any]] = field(default_factory=list)
    status: str = STATUS_PROPOSED
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self) -> None:
        if not self.id:
            object.__setattr__(self, "id", f"sp_{uuid.uuid4().hex[:12]}")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "proposer_node_id": self.proposer_node_id,
            "strategy": self.strategy,
            "votes": self.votes,
            "status": self.status,
            "timestamp": self.timestamp.isoformat(),
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> StrategyProposal:
        return cls(
            id=d.get("id", ""),
            proposer_node_id=d.get("proposer_node_id", ""),
            strategy=d.get("strategy", {}),
            votes=d.get("votes", []),
            status=d.get("status", STATUS_PROPOSED),
            timestamp=_parse_dt(d.get("timestamp")) or datetime.now(timezone.utc),
        )

    def approve_count(self) -> int:
        return sum(1 for v in self.votes if v.get("vote") == VOTE_APPROVE)

    def reject_count(self) -> int:
        return sum(1 for v in self.votes if v.get("vote") == VOTE_REJECT)

    @property
    def has_consensus(self) -> bool:
        """Simple majority: approves > rejects and at least 3 votes."""
        return self.approve_count() > self.reject_count() and len(self.votes) >= 3


def _parse_dt(val: Any) -> Optional[datetime]:
    if val is None or isinstance(val, datetime):
        return val
    try:
        return datetime.fromisoformat(val)
    except (ValueError, TypeError):
        return None


class ClusterStrategySync:
    """Manages strategy proposals, voting, and adoption across the cluster."""

    def __init__(self) -> None:
        self._proposals: Dict[str, StrategyProposal] = {}
        self.logger = logger.bind(component="ClusterStrategySync")

    async def propose_strategy(self, proposal: StrategyProposal) -> None:
        """Propose a new strategy for cluster-wide adoption."""
        proposal.status = STATUS_PROPOSED
        self._proposals[proposal.id] = proposal
        self.logger.info(
            "Strategy proposed",
            id=proposal.id,
            proposer=proposal.proposer_node_id,
        )

    async def vote(
        self,
        proposal_id: str,
        node_id: str,
        vote: str,
        reason: str = "",
    ) -> None:
        """Cast a vote on a proposal.

        If consensus is reached, auto-approves.
        """
        proposal = self._proposals.get(proposal_id)
        if proposal is None:
            raise ValueError(f"Proposal {proposal_id} not found")
        if proposal.status != STATUS_PROPOSED:
            raise ValueError(f"Proposal {proposal_id} is {proposal.status}, not PROPOSED")

        # Check if node already voted
        for existing in proposal.votes:
            if existing["node_id"] == node_id:
                existing["vote"] = vote
                existing["reason"] = reason
                break
        else:
            proposal.votes.append({
                "node_id": node_id,
                "vote": vote,
                "reason": reason,
            })

        # Auto-approve on consensus
        if proposal.has_consensus:
            proposal.status = STATUS_APPROVED
            self.logger.info(
                "Strategy auto-approved via consensus",
                id=proposal_id,
                approves=proposal.approve_count(),
                rejects=proposal.reject_count(),
            )

        self.logger.debug(
            "Vote cast",
            proposal_id=proposal_id,
            node=node_id,
            vote=vote,
        )

    async def get_proposals(
        self,
        status: Optional[str] = None,
        limit: int = 100,
    ) -> List[StrategyProposal]:
        """List proposals, optionally filtered by status."""
        result = list(self._proposals.values())
        if status is not None:
            result = [p for p in result if p.status == status]
        result.sort(key=lambda p: p.timestamp, reverse=True)
        return result[:limit]

    async def adopt_strategy(self, proposal_id: str) -> StrategyProposal:
        """Manually adopt (approve) a strategy proposal."""
        proposal = self._proposals.get(proposal_id)
        if proposal is None:
            raise ValueError(f"Proposal {proposal_id} not found")
        proposal.status = STATUS_APPROVED
        self.logger.info("Strategy adopted", id=proposal_id)
        return proposal

    async def get_by_id(self, proposal_id: str) -> Optional[StrategyProposal]:
        return self._proposals.get(proposal_id)

    async def count(self) -> int:
        return len(self._proposals)

    async def clear(self) -> None:
        self._proposals.clear()
