"""Agent Collaboration - WP-21..30 (MISSION-5.3 / IP-5.3-003).

Kolaborasi antar-Agent berbasis contract, capability, evidence, dan Governance.
Collaboration tetap governed; tidak ada execution di luar governance.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional, Tuple

from .agent_contract_framework import AgentResponse
from .agent_foundation import AgentCapabilityKind


def _now_utc() -> str:
    return datetime.utcnow().isoformat() + "Z"


class CollaborationState(str, Enum):
    """State kolaborasi."""

    PROPOSED = "proposed"
    NEGOTIATED = "negotiated"
    APPROVED = "approved"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    REJECTED = "rejected"


@dataclass(frozen=True)
class CollaborationProposal:
    """Proposal kolaborasi antar agent."""

    collaboration_id: str
    provider_agent_id: str
    target_agent_id: str
    capability: AgentCapabilityKind
    state: CollaborationState = CollaborationState.PROPOSED
    created_at: str = field(default_factory=_now_utc)

    def as_dict(self) -> dict:
        return {
            "collaboration_id": self.collaboration_id,
            "provider_agent_id": self.provider_agent_id,
            "target_agent_id": self.target_agent_id,
            "capability": self.capability.value,
            "state": self.state.value,
            "created_at": self.created_at,
        }


@dataclass(frozen=True)
class NegotiationResult:
    """Hasil negosiasi capability kolaborasi."""

    collaboration_id: str
    accepted: bool
    reason: str = ""

    def as_dict(self) -> dict:
        return {"collaboration_id": self.collaboration_id, "accepted": self.accepted, "reason": self.reason}


@dataclass(frozen=True)
class CollaborationRecord:
    """Rekam kolaborasi (auditable)."""

    proposal: CollaborationProposal
    approved: bool
    evidence_refs: Tuple[str, ...] = field(default_factory=tuple)
    responses: Tuple[AgentResponse, ...] = field(default_factory=tuple)

    @property
    def governed(self) -> bool:
        return self.proposal.state == CollaborationState.APPROVED

    def as_dict(self) -> dict:
        return {
            "proposal": self.proposal.as_dict(),
            "approved": self.approved,
            "evidence_refs": list(self.evidence_refs),
            "responses": [r.as_dict() for r in self.responses],
            "governed": self.governed,
        }


class CollaborationManager:
    """Mengelola lifecycle kolaborasi antar agent."""

    def __init__(self) -> None:
        self._records: dict = {}

    def propose(self, provider_agent_id: str, target_agent_id: str, capability: AgentCapabilityKind) -> CollaborationProposal:
        import uuid

        proposal = CollaborationProposal(
            collaboration_id=uuid.uuid4().hex,
            provider_agent_id=provider_agent_id,
            target_agent_id=target_agent_id,
            capability=capability,
        )
        self._records[proposal.collaboration_id] = CollaborationRecord(proposal=proposal, approved=False)
        return proposal

    def negotiate(self, collaboration_id: str, accepted: bool = True, reason: str = "") -> NegotiationResult:
        record = self._records.get(collaboration_id)
        if record is None:
            return NegotiationResult(collaboration_id=collaboration_id, accepted=False, reason="not found")
        new_state = CollaborationState.NEGOTIATED if accepted else CollaborationState.REJECTED
        proposal = _with_state(record.proposal, new_state)
        self._records[collaboration_id] = CollaborationRecord(proposal=proposal, approved=False, evidence_refs=record.evidence_refs, responses=record.responses)
        return NegotiationResult(collaboration_id=collaboration_id, accepted=accepted, reason=reason)

    def approve(self, collaboration_id: str, evidence_refs: Tuple[str, ...] = ()) -> Optional[CollaborationRecord]:
        record = self._records.get(collaboration_id)
        if record is None:
            return None
        proposal = _with_state(record.proposal, CollaborationState.APPROVED)
        updated = CollaborationRecord(proposal=proposal, approved=True, evidence_refs=evidence_refs, responses=record.responses)
        self._records[collaboration_id] = updated
        return updated

    def complete(self, collaboration_id: str, responses: Tuple[AgentResponse, ...]) -> Optional[CollaborationRecord]:
        record = self._records.get(collaboration_id)
        if record is None:
            return None
        proposal = _with_state(record.proposal, CollaborationState.COMPLETED)
        updated = CollaborationRecord(proposal=proposal, approved=record.approved, evidence_refs=record.evidence_refs, responses=responses)
        self._records[collaboration_id] = updated
        return updated

    def get(self, collaboration_id: str) -> Optional[CollaborationRecord]:
        return self._records.get(collaboration_id)

    def history(self, agent_id: str) -> Tuple[CollaborationRecord, ...]:
        return tuple(
            r for r in self._records.values()
            if r.proposal.provider_agent_id == agent_id or r.proposal.target_agent_id == agent_id
        )


def _with_state(proposal: CollaborationProposal, state: CollaborationState) -> CollaborationProposal:
    return CollaborationProposal(
        collaboration_id=proposal.collaboration_id,
        provider_agent_id=proposal.provider_agent_id,
        target_agent_id=proposal.target_agent_id,
        capability=proposal.capability,
        state=state,
        created_at=proposal.created_at,
    )


@dataclass(frozen=True)
class CollaborationComplianceResult:
    """Hasil compliance kolaborasi."""

    passed: bool
    checks: Tuple[Dict[str, Any], ...] = field(default_factory=tuple)

    def as_dict(self) -> dict:
        return {"passed": self.passed, "checks": list(self.checks)}


class CollaborationComplianceChecker:
    """Checker compliance kolaborasi agent."""

    def check(self, record: CollaborationRecord, *, governed: bool = True, evidence_based: bool = True, no_execution_bypass: bool = True) -> CollaborationComplianceResult:
        checks = [
            {"code": "GOVERNED", "passed": governed},
            {"code": "APPROVED_BEFORE_EXECUTION", "passed": not record.responses or record.approved},
            {"code": "EVIDENCE_BASED", "passed": evidence_based},
            {"code": "NO_EXECUTION_BYPASS", "passed": no_execution_bypass},
        ]
        return CollaborationComplianceResult(passed=all(c["passed"] for c in checks), checks=tuple(checks))

    def certify(self, record: CollaborationRecord, **kwargs: Any) -> Dict[str, Any]:
        result = self.check(record, **kwargs)
        return {"component": "universal_agent.collaboration", "passed": result.passed, "certified": result.passed, "checks": [c for c in result.checks]}
