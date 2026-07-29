# OP-397 — Execution Dashboard
# Python 3.8 compatible, frozen dataclass, synchronous only
# Dashboard DTOs for Execution Connectors — presentation layer only

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple

from .execution_request import (
    ExecutionRequest,
    ExecutionPlan,
    ExecutionResult,
    ExecutionStatus,
    ExecutionRisk,
)
from .connector_protocol import ConnectorInfo, ConnectorCapability
from .connector_registry import ConnectorRegistry, RegistryEntry
from .approval_execution import ApprovalRequest, ApprovalResult


# ---------------------------------------------------------------------------
# Dashboard DTOs
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ConnectorCard:
    """Dashboard card showing connector overview."""
    total_connectors: int = 0
    healthy: int = 0
    unhealthy: int = 0
    by_type: Dict[str, int] = field(default_factory=dict)
    top_connectors: Tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class ExecutionCard:
    """Dashboard card showing execution status overview."""
    total_requests: int = 0
    pending: int = 0
    planned: int = 0
    awaiting_approval: int = 0
    approved: int = 0
    rejected: int = 0
    executing: int = 0
    completed: int = 0
    failed: int = 0
    rolled_back: int = 0
    avg_risk_score: float = 0.0


@dataclass(frozen=True)
class ApprovalCard:
    """Dashboard card showing approval queue overview."""
    pending_approvals: int = 0
    requires_human: bool = True
    aggregated_risk: str = "low"
    descriptions: Tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class CapabilityCard:
    """Dashboard card showing available capabilities."""
    total_capabilities: int = 0
    total_actions: int = 0
    capabilities: Tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class HealthCard:
    """Dashboard card showing execution subsystem health."""
    registry_healthy: bool = True
    connectors_healthy: bool = True
    planner_available: bool = True
    approval_bridge_available: bool = True
    overall_healthy: bool = True
    details: str = ""


@dataclass(frozen=True)
class QueueCard:
    """Dashboard card showing execution queue status."""
    total_in_queue: int = 0
    waiting_approval: int = 0
    waiting_execution: int = 0
    estimated_wait_seconds: int = 0


@dataclass(frozen=True)
class ExecutionDashboard:
    """Complete dashboard DTO for Execution Connectors."""
    connectors: ConnectorCard = field(default_factory=ConnectorCard)
    execution: ExecutionCard = field(default_factory=ExecutionCard)
    approval: ApprovalCard = field(default_factory=ApprovalCard)
    capability: CapabilityCard = field(default_factory=CapabilityCard)
    health: HealthCard = field(default_factory=HealthCard)
    queue: QueueCard = field(default_factory=QueueCard)
    timestamp: datetime = field(default_factory=datetime.utcnow)


# ---------------------------------------------------------------------------
# Dashboard Builder
# ---------------------------------------------------------------------------

class ExecutionDashboardBuilder:
    """Builds dashboard DTOs from execution components.

    Pure composition — no business logic.
    """

    @staticmethod
    def build(registry: ConnectorRegistry) -> ExecutionDashboard:
        """Build a complete execution dashboard."""
        summary = registry.health_summary()
        entries = registry.list()

        # Connector card
        top = tuple(
            e.name for e in sorted(entries, key=lambda x: x.priority, reverse=True)[:5]
        )
        connector_card = ConnectorCard(
            total_connectors=summary["total_connectors"],
            healthy=summary["healthy"],
            unhealthy=summary["unhealthy"],
            by_type=summary["by_type"],
            top_connectors=top,
        )

        # Capabilities card
        all_caps: Dict[str, bool] = {}
        for e in entries:
            for a in e.capability_actions:
                all_caps[a] = True
        capability_card = CapabilityCard(
            total_capabilities=len(entries),
            total_actions=len(all_caps),
            capabilities=tuple(sorted(all_caps.keys())),
        )

        # Health card
        all_healthy = summary["unhealthy"] == 0
        health_card = HealthCard(
            registry_healthy=True,
            connectors_healthy=all_healthy,
            planner_available=True,
            approval_bridge_available=True,
            overall_healthy=all_healthy,
            details=f"{summary['healthy']}/{summary['total_connectors']} connectors healthy",
        )

        # Approval card
        approval_card = ApprovalCard(
            pending_approvals=0,
            requires_human=True,
            aggregated_risk="low",
            descriptions=tuple(
                f"{e.name}: {', '.join(e.capability_actions[:3])}"
                for e in entries[:3]
            ),
        )

        # Execution card
        execution_card = ExecutionCard(
            total_requests=0,
            avg_risk_score=0.0,
        )

        # Queue card
        queue_card = QueueCard()

        return ExecutionDashboard(
            connectors=connector_card,
            execution=execution_card,
            approval=approval_card,
            capability=capability_card,
            health=health_card,
            queue=queue_card,
        )
