"""Evolution Policy — Sprint 28 Fase 2.

Defines the EvolutionPolicy class that governs how parameter changes,
template mutations, and architectural modifications are evaluated,
approved, or rejected. Integration layer between SelfOptimizer
and governance/confidence systems.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Set

import structlog

from sam.evolution.params import ParamManager
from sam.evolution.optimizer import SelfOptimizer, OptimizationSuggestion


logger = structlog.get_logger()


# ── Policy Proposal Types ──────────────────────────────────────────


class ProposalType(str, Enum):
    """Category of evolution proposal."""

    PARAMETER_TUNE = "parameter_tune"
    """Adjust an optimizable parameter within bounds."""

    TEMPLATE_MUTATION = "template_mutation"
    """Mutate an execution graph template."""

    ARCHITECTURE_CHANGE = "architecture_change"
    """Propose an architectural modification."""

    STRATEGY_SHIFT = "strategy_shift"
    """Change in optimization strategy or goal."""


class ProposalStatus(str, Enum):
    """Lifecycle status of a proposal."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    ROLLED_BACK = "rolled_back"
    SUPERSEDED = "superseded"


@dataclass
class EvolutionProposal:
    """A single proposal to change system behaviour.

    Attributes:
        id: Unique proposal identifier.
        proposal_type: Category of change.
        description: Human-readable summary.
        param_name: Affected parameter (if PARAMETER_TUNE).
        current_value: Current value before change.
        proposed_value: Proposed new value.
        expected_improvement: Expected % improvement.
        confidence: Confidence in the proposal (0.0–1.0).
        evidence: Supporting evidence identifiers.
        status: Current lifecycle status.
        rationale: Why this change is being proposed.
        risk_level: Estimated risk (low/medium/high).
        created_at: When the proposal was created.
        evaluated_at: When it was evaluated.
    """

    id: str
    proposal_type: ProposalType
    description: str
    param_name: Optional[str] = None
    current_value: Any = None
    proposed_value: Any = None
    expected_improvement: float = 0.0
    confidence: float = 0.0
    evidence: List[str] = field(default_factory=list)
    status: ProposalStatus = ProposalStatus.PENDING
    rationale: str = ""
    risk_level: str = "medium"
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    evaluated_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "proposal_type": self.proposal_type.value,
            "description": self.description,
            "param_name": self.param_name,
            "current_value": self.current_value,
            "proposed_value": self.proposed_value,
            "expected_improvement": self.expected_improvement,
            "confidence": self.confidence,
            "evidence": self.evidence,
            "status": self.status.value,
            "rationale": self.rationale,
            "risk_level": self.risk_level,
            "created_at": self.created_at.isoformat(),
            "evaluated_at": self.evaluated_at.isoformat() if self.evaluated_at else None,
        }


# ── Policy Rules ───────────────────────────────────────────────────


@dataclass
class PolicyRule:
    """A single rule that guides evolution policy decisions.

    Attributes:
        name: Rule name.
        description: What this rule checks.
        max_risk: Maximum allowed risk level: low=1, medium=2, high=3.
        min_confidence: Minimum confidence required (0.0–1.0).
        min_improvement: Minimum expected improvement %.
        allow_rollback: Whether rollback is allowed for this type.
        max_concurrent_proposals: Max pending proposals of this type.
    """

    name: str
    description: str
    max_risk: int = 3
    min_confidence: float = 0.0
    min_improvement: float = 0.0
    allow_rollback: bool = True
    max_concurrent_proposals: int = 10


# ── Evolution Policy ───────────────────────────────────────────────


_RISK_MAP: Dict[str, int] = {
    "low": 1,
    "medium": 2,
    "high": 3,
}

_DEFAULT_POLICY_RULES: Dict[ProposalType, PolicyRule] = {
    ProposalType.PARAMETER_TUNE: PolicyRule(
        name="parameter_tune_rule",
        description="Parameter tuning: bounded changes with moderate confidence",
        max_risk=2,  # medium max
        min_confidence=0.3,
        min_improvement=1.0,
        allow_rollback=True,
        max_concurrent_proposals=10,
    ),
    ProposalType.TEMPLATE_MUTATION: PolicyRule(
        name="template_mutation_rule",
        description="Template changes: higher bar for approval",
        max_risk=2,
        min_confidence=0.5,
        min_improvement=5.0,
        allow_rollback=True,
        max_concurrent_proposals=5,
    ),
    ProposalType.ARCHITECTURE_CHANGE: PolicyRule(
        name="architecture_change_rule",
        description="Architecture changes: strictest gate",
        max_risk=1,  # low only
        min_confidence=0.7,
        min_improvement=15.0,
        allow_rollback=False,
        max_concurrent_proposals=2,
    ),
    ProposalType.STRATEGY_SHIFT: PolicyRule(
        name="strategy_shift_rule",
        description="Strategy shifts: moderate gate",
        max_risk=2,
        min_confidence=0.6,
        min_improvement=10.0,
        allow_rollback=True,
        max_concurrent_proposals=3,
    ),
}


class EvolutionPolicy:
    """Governs the evolution lifecycle of system parameters and behaviour.

    Evaluates proposals against policy rules and system confidence,
    approves or rejects them, and integrates with SelfOptimizer for
    applying approved parameter changes.

    Usage:
        policy = EvolutionPolicy(param_manager, confidence_calculator)
        proposal = await policy.create_proposal(...)
        ok = await policy.evaluate(proposal)
        if ok:
            await policy.approve(proposal)
    """

    def __init__(
        self,
        param_manager: ParamManager,
        confidence_calculator: Optional[Any] = None,
    ) -> None:
        self._param_manager = param_manager
        self._confidence_calculator = confidence_calculator
        self._rules: Dict[ProposalType, PolicyRule] = dict(_DEFAULT_POLICY_RULES)
        self._proposals: Dict[str, EvolutionProposal] = {}
        self._logger = logger.bind(component="EvolutionPolicy")

    # ── Proposal Lifecycle ────────────────────────────────────────

    async def create_proposal(
        self,
        proposal_type: ProposalType,
        description: str,
        param_name: Optional[str] = None,
        current_value: Any = None,
        proposed_value: Any = None,
        expected_improvement: float = 0.0,
        confidence: float = 0.0,
        evidence: Optional[List[str]] = None,
        rationale: str = "",
        risk_level: str = "medium",
    ) -> EvolutionProposal:
        """Create a new evolution proposal.

        Integrates with SelfOptimizer by deriving proposal data
        from optimization suggestions.
        """
        proposal = EvolutionProposal(
            id=f"prop_{uuid.uuid4().hex[:12]}",
            proposal_type=proposal_type,
            description=description,
            param_name=param_name,
            current_value=current_value,
            proposed_value=proposed_value,
            expected_improvement=expected_improvement,
            confidence=confidence,
            evidence=evidence or [],
            rationale=rationale,
            risk_level=risk_level,
        )
        self._proposals[proposal.id] = proposal
        self._logger.info(
            "Proposal created",
            proposal_id=proposal.id,
            proposal_type=proposal_type.value,
        )
        return proposal

    async def from_suggestion(
        self,
        suggestion: OptimizationSuggestion,
        proposal_type: ProposalType = ProposalType.PARAMETER_TUNE,
        rationale: str = "",
        risk_level: str = "medium",
    ) -> EvolutionProposal:
        """Create an EvolutionProposal from an OptimizationSuggestion.

        This is the primary integration point with SelfOptimizer.
        """
        return await self.create_proposal(
            proposal_type=proposal_type,
            description=f"Auto-optimize {suggestion.param_name}: "
                        f"{suggestion.current_value} → {suggestion.suggested_value}",
            param_name=suggestion.param_name,
            current_value=suggestion.current_value,
            proposed_value=suggestion.suggested_value,
            expected_improvement=suggestion.expected_improvement,
            confidence=suggestion.confidence,
            evidence=suggestion.evidence,
            rationale=rationale or f"Auto-generated from {proposal_type.value} analysis",
            risk_level=risk_level,
        )

    async def evaluate(self, proposal: EvolutionProposal) -> bool:
        """Evaluate a proposal against policy rules and return True if it passes.

        Checks:
        1. Risk level within allowed bounds for proposal type.
        2. Confidence meets minimum threshold.
        3. Expected improvement meets minimum threshold.
        4. Concurrent proposal limit not exceeded.
        5. Operational confidence (if calculator available) is sufficient.
        """
        rule = self._rules.get(proposal.proposal_type)
        if rule is None:
            self._logger.warning(
                "No policy rule for type",
                proposal_id=proposal.id,
                proposal_type=proposal.proposal_type.value,
            )
            proposal.status = ProposalStatus.REJECTED
            proposal.evaluated_at = datetime.now(timezone.utc)
            return False

        failures: List[str] = []

        # 1. Risk check
        risk_val = _RISK_MAP.get(proposal.risk_level, 3)
        if risk_val > rule.max_risk:
            failures.append(
                f"Risk level '{proposal.risk_level}' ({risk_val}) "
                f"exceeds max allowed ({rule.max_risk}) for {proposal.proposal_type.value}"
            )

        # 2. Confidence check
        if proposal.confidence < rule.min_confidence:
            failures.append(
                f"Confidence {proposal.confidence:.2f} below minimum "
                f"{rule.min_confidence:.2f} for {proposal.proposal_type.value}"
            )

        # 3. Improvement check
        if proposal.expected_improvement < rule.min_improvement:
            failures.append(
                f"Expected improvement {proposal.expected_improvement:.1f}% "
                f"below minimum {rule.min_improvement:.1f}% for {proposal.proposal_type.value}"
            )

        # 4. Concurrent proposal limit
        pending_count = sum(
            1 for p in self._proposals.values()
            if p.proposal_type == proposal.proposal_type
            and p.status == ProposalStatus.PENDING
            and p.id != proposal.id
        )
        if pending_count >= rule.max_concurrent_proposals:
            failures.append(
                f"Too many pending {proposal.proposal_type.value} proposals "
                f"({pending_count} >= {rule.max_concurrent_proposals})"
            )

        # 5. Operational confidence check (if calculator available)
        if self._confidence_calculator is not None:
            try:
                conf_score = self._confidence_calculator.get_current_score()
                if conf_score is not None and conf_score < 30:
                    failures.append(
                        f"Operational confidence too low ({conf_score}/100) "
                        f"to approve new proposals"
                    )
            except Exception as exc:
                self._logger.warning(
                    "Confidence check failed",
                    proposal_id=proposal.id,
                    error=str(exc),
                )

        proposal.evaluated_at = datetime.now(timezone.utc)

        if not failures:
            proposal.status = ProposalStatus.APPROVED
            self._logger.info(
                "Proposal approved",
                proposal_id=proposal.id,
                proposal_type=proposal.proposal_type.value,
            )
            return True

        proposal.status = ProposalStatus.REJECTED
        self._logger.info(
            "Proposal rejected",
            proposal_id=proposal.id,
            reasons=failures,
        )
        return False

    async def approve(
        self,
        proposal: EvolutionProposal,
        optimizer: Optional[SelfOptimizer] = None,
    ) -> None:
        """Approve and apply the proposal.

        For PARAMETER_TUNE proposals, applies the change via SelfOptimizer.
        Does NOT call ParamManager directly — always goes through SelfOptimizer.
        """
        if proposal.status != ProposalStatus.APPROVED:
            # Auto-evaluate if not yet evaluated
            ok = await self.evaluate(proposal)
            if not ok:
                raise ValueError(
                    f"Cannot approve proposal {proposal.id}: "
                    f"failed policy evaluation"
                )

        proposal.status = ProposalStatus.APPROVED
        proposal.evaluated_at = datetime.now(timezone.utc)

        if proposal.proposal_type == ProposalType.PARAMETER_TUNE:
            if optimizer is None:
                raise ValueError(
                    "SelfOptimizer required to apply PARAMETER_TUNE proposal"
                )
            if proposal.param_name is None:
                raise ValueError("PARAMETER_TUNE proposal must specify param_name")

            # Always through SelfOptimizer, not ParamManager directly
            suggestion = OptimizationSuggestion(
                param_name=proposal.param_name,
                current_value=proposal.current_value,
                suggested_value=proposal.proposed_value,
                expected_improvement=proposal.expected_improvement,
                confidence=proposal.confidence,
                evidence=proposal.evidence,
            )
            history_id = await optimizer.apply_suggestion(suggestion)
            self._logger.info(
                "Proposal applied via optimizer",
                proposal_id=proposal.id,
                history_id=history_id,
                param_name=proposal.param_name,
            )
        else:
            self._logger.info(
                "Proposal approved (non-parameter, no automated apply)",
                proposal_id=proposal.id,
                proposal_type=proposal.proposal_type.value,
            )

    async def reject(self, proposal: EvolutionProposal) -> None:
        """Reject a proposal without applying it."""
        proposal.status = ProposalStatus.REJECTED
        proposal.evaluated_at = datetime.now(timezone.utc)
        self._logger.info(
            "Proposal rejected",
            proposal_id=proposal.id,
            proposal_type=proposal.proposal_type.value,
        )

    # ── Policy Rules Management ───────────────────────────────────

    def get_rule(self, proposal_type: ProposalType) -> Optional[PolicyRule]:
        """Get the policy rule for a proposal type."""
        return self._rules.get(proposal_type)

    def set_rule(self, proposal_type: ProposalType, rule: PolicyRule) -> None:
        """Override the policy rule for a proposal type."""
        self._rules[proposal_type] = rule
        self._logger.info(
            "Policy rule updated",
            proposal_type=proposal_type.value,
            rule_name=rule.name,
        )

    def get_rules(self) -> Dict[ProposalType, PolicyRule]:
        """Return all current policy rules."""
        return dict(self._rules)

    # ── Proposal Queries ──────────────────────────────────────────

    def get_proposal(self, proposal_id: str) -> Optional[EvolutionProposal]:
        """Get a proposal by ID."""
        return self._proposals.get(proposal_id)

    def get_proposals(
        self,
        status: Optional[ProposalStatus] = None,
        proposal_type: Optional[ProposalType] = None,
        limit: int = 50,
    ) -> List[EvolutionProposal]:
        """List proposals with optional filters."""
        results = list(self._proposals.values())

        if status is not None:
            results = [p for p in results if p.status == status]
        if proposal_type is not None:
            results = [p for p in results if p.proposal_type == proposal_type]

        results.sort(key=lambda p: p.created_at, reverse=True)
        return results[:limit]

    def get_pending_count(self, proposal_type: Optional[ProposalType] = None) -> int:
        """Count pending proposals, optionally filtered by type."""
        if proposal_type:
            return sum(
                1 for p in self._proposals.values()
                if p.status == ProposalStatus.PENDING
                and p.proposal_type == proposal_type
            )
        return sum(
            1 for p in self._proposals.values()
            if p.status == ProposalStatus.PENDING
        )


__all__ = [
    "ProposalType",
    "ProposalStatus",
    "EvolutionProposal",
    "PolicyRule",
    "EvolutionPolicy",
]
