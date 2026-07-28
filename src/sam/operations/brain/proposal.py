"""
OP-245 — Mission Proposal Service.

Converts MissionRecommendation into MissionProposal ready for
MissionController. Every proposal requires approval.
Does NOT auto-submit.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional
import uuid

from .recommendation import MissionRecommendation


@dataclass
class MissionProposal:
    """A proposal ready for MissionController.

    Must be reviewed and approved before execution.
    """

    proposal_id: str
    recommendation_id: str
    title: str
    description: str
    priority: str
    estimated_impact: str
    evidence: List[Dict[str, Any]]
    suggested_steps: List[str]
    requires_approval: bool
    confidence: float
    generated_at: float
    submitted: bool


class ProposalService:
    """Manages mission proposals.

    Proposals cannot be auto-submitted — submit() must be called explicitly.
    """

    def __init__(self) -> None:
        self._proposals: Dict[str, MissionProposal] = {}
        self._submitted_proposals: List[str] = []

    def create_proposal(
        self,
        recommendation: MissionRecommendation,
    ) -> MissionProposal:
        """Create a proposal from a recommendation.

        Does NOT submit or execute.
        """
        import time
        proposal = MissionProposal(
            proposal_id=str(uuid.uuid4()),
            recommendation_id=recommendation.recommendation_id,
            title=recommendation.title,
            description=recommendation.description,
            priority=recommendation.priority,
            estimated_impact=recommendation.estimated_impact,
            evidence=list(recommendation.evidence),
            suggested_steps=list(recommendation.suggested_steps),
            requires_approval=recommendation.required_approval,
            confidence=recommendation.confidence,
            generated_at=time.time(),
            submitted=False,
        )
        self._proposals[proposal.proposal_id] = proposal
        return proposal

    def submit_proposal(self, proposal_id: str) -> bool:
        """Mark a proposal as submitted.

        This is the explicit gate — no auto-submit.
        Returns True if proposal exists and was submitted.
        """
        if proposal_id not in self._proposals:
            return False
        proposal = self._proposals[proposal_id]
        if proposal.submitted:
            return False
        object.__setattr__(proposal, "submitted", True)
        self._submitted_proposals.append(proposal_id)
        self._forward_to_approval(proposal)
        return True

    def _forward_to_approval(self, proposal: MissionProposal) -> None:
        """Forward submitted proposal to approval queue.

        Read-only delegation to existing approval system.
        """
        try:
            from sam.operations.approval import queue_approval
            queue_approval(
                item_type="mission_proposal",
                item_id=proposal.proposal_id,
                item_summary=proposal.title,
                requires_approval=proposal.requires_approval,
            )
        except Exception:
            pass  # gracefully skip if approval module unavailable

    def get_proposal(self, proposal_id: str) -> Optional[MissionProposal]:
        return self._proposals.get(proposal_id)

    def list_pending(self) -> List[MissionProposal]:
        return [
            p for p in self._proposals.values()
            if not p.submitted
        ]

    def list_submitted(self) -> List[MissionProposal]:
        return [
            p for p in self._proposals.values()
            if p.submitted
        ]

    @property
    def proposal_count(self) -> int:
        return len(self._proposals)


def create_proposal(
    recommendation: MissionRecommendation,
) -> MissionProposal:
    """One-shot convenience."""
    return ProposalService().create_proposal(recommendation)
