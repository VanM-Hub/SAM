# OP-398 — Execution Integration Pipeline
# Python 3.8 compatible, frozen dataclass, synchronous only
# Integrates: Guardian → Decision → ExecutionPlanner → ApprovalBridge → Conversation → Dashboard
# No connector is called — pure DTO pipeline

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple
import uuid

from .execution_request import (
    ExecutionRequest,
    ExecutionPlan,
    ExecutionResult,
    ExecutionStatus,
    ExecutionRisk,
    ExecutionTarget,
    ExecutionParameter,
)
from .connector_protocol import (
    ConnectorProtocol,
    ConnectorInfo,
    ConnectorCapability,
    BaseConnector,
)
from .connector_registry import (
    ConnectorRegistry,
    RegistryEntry,
    CapabilityLookup,
)
from .execution_planner import ExecutionPlanner, DependencyEdge
from .approval_execution import (
    ExecutionApprovalBridge,
    ApprovalRequest,
    ApprovalResult,
    ApprovalItem,
)
from .conversation_execution import (
    ConversationExecutionBridge,
    ExecutionQueryResult,
)
from .dashboard_execution import (
    ExecutionDashboardBuilder,
    ExecutionDashboard,
    ConnectorCard,
    ExecutionCard,
    ApprovalCard,
    CapabilityCard,
    HealthCard,
    QueueCard,
)


# ---------------------------------------------------------------------------
# Integration DTOs
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ExecutionPipelineResult:
    """Complete result of running the execution integration pipeline."""
    pipeline_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    requests: Tuple[ExecutionRequest, ...] = field(default_factory=tuple)
    plan: Optional[ExecutionPlan] = None
    approval_request: Optional[ApprovalRequest] = None
    approval_result: Optional[ApprovalResult] = None
    conversation_summary: Optional[ExecutionQueryResult] = None
    dashboard: Optional[ExecutionDashboard] = None
    pipeline_complete: bool = False
    timestamp: datetime = field(default_factory=datetime.utcnow)
    error: str = ""


# ---------------------------------------------------------------------------
# ExecutionPipeline
# ---------------------------------------------------------------------------

class ExecutionPipeline:
    """Synchronous pipeline that connects Guardian → Decision → Execution.

    Pipeline:
    Guardian → Decision → ExecutionPlanner → ApprovalBridge → Conversation → Dashboard

    NO connectors are called — this is purely a DTO pipeline.
    """

    def __init__(
        self,
        registry: ConnectorRegistry,
        planner: Optional[ExecutionPlanner] = None,
        approval_bridge: Optional[ExecutionApprovalBridge] = None,
        conversation_bridge: Optional[ConversationExecutionBridge] = None,
        dashboard_builder: Optional[ExecutionDashboardBuilder] = None,
    ) -> None:
        self.registry = registry
        self.planner = planner or ExecutionPlanner()
        self.approval_bridge = approval_bridge or ExecutionApprovalBridge()
        self.conversation_bridge = conversation_bridge or ConversationExecutionBridge(registry, planner)
        self.dashboard_builder = dashboard_builder or ExecutionDashboardBuilder()

    # --- Pipeline Steps ---

    def create_request(
        self,
        connector_type: str,
        action: str,
        target: ExecutionTarget,
        parameters: Optional[Tuple[ExecutionParameter, ...]] = None,
        risk_level: str = "low",
        description: str = "",
        requires_approval: bool = True,
    ) -> ExecutionRequest:
        """Step 1: Create an execution request (simulates Guardian Decision)."""
        risk_score_map = {"low": 0.1, "medium": 0.4, "high": 0.7, "critical": 0.9}
        score = risk_score_map.get(risk_level, 0.1)

        return ExecutionRequest(
            connector_type=connector_type,
            action=action,
            target=target,
            parameters=parameters or (),
            risk=ExecutionRisk(
                level=risk_level,
                score=score,
                factors=(f"Risk level: {risk_level}",),
                requires_approval=requires_approval or risk_level in ("medium", "high", "critical"),
                requires_guardian=risk_level == "critical",
            ),
            description=description,
            requires_approval=requires_approval or risk_level in ("medium", "high", "critical"),
        )

    def plan_requests(self, requests: Tuple[ExecutionRequest, ...]) -> ExecutionPlan:
        """Step 2: Plan execution (planner)."""
        return self.planner.plan(requests)

    def request_approval(self, plan: ExecutionPlan) -> ApprovalRequest:
        """Step 3: Create approval request (approval bridge)."""
        return self.approval_bridge.create_approval_request(plan)

    def approve_plan(self, approval_request: ApprovalRequest) -> ApprovalResult:
        """Step 4: Simulate approval (approval bridge — no auto-submit)."""
        return self.approval_bridge.approve(approval_request)

    def reject_plan(
        self, approval_request: ApprovalRequest, reason: str = ""
    ) -> ApprovalResult:
        """Step 4b: Reject plan."""
        return self.approval_bridge.reject(approval_request, reason=reason)

    def get_conversation_summary(self) -> ExecutionQueryResult:
        """Step 5: Get conversation summary."""
        return self.conversation_bridge.query("execution status")

    def get_dashboard(self) -> ExecutionDashboard:
        """Step 6: Build dashboard."""
        return self.dashboard_builder.build(self.registry)

    # --- Full Pipeline ---

    def run(
        self,
        requests: Tuple[ExecutionRequest, ...],
        approve: bool = True,
    ) -> ExecutionPipelineResult:
        """Run the full execution integration pipeline.

        Guardian → Decision → ExecutionPlanner → ApprovalBridge → Conversation → Dashboard
        """
        try:
            # Step 1: Accept requests
            # (simulates Guardian+Decision producing execution requests)

            # Step 2: Plan
            plan = self.plan_requests(requests)

            # Step 3: Approval
            approval_request = self.request_approval(plan)
            if approve:
                approval_result = self.approve_plan(approval_request)
            else:
                approval_result = self.reject_plan(approval_request)

            # Step 4: Conversation summary
            conv_summary = self.get_conversation_summary()

            # Step 5: Dashboard
            dashboard = self.get_dashboard()

            return ExecutionPipelineResult(
                requests=requests,
                plan=plan,
                approval_request=approval_request,
                approval_result=approval_result,
                conversation_summary=conv_summary,
                dashboard=dashboard,
                pipeline_complete=True,
            )

        except Exception as e:
            return ExecutionPipelineResult(
                requests=requests,
                pipeline_complete=False,
                error=str(e),
            )

    def has_support_for(self, action: str) -> bool:
        """Check if any registered connector supports an action."""
        lookup = self.registry.capability_lookup(action)
        return lookup.total_found > 0

    @property
    def is_operational(self) -> bool:
        """Check if the execution pipeline is operational."""
        summary = self.registry.health_summary()
        return summary["total_connectors"] > 0 and summary["unhealthy"] == 0
