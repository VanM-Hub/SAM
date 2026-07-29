# OP-408 — Connector Integration Pipeline
# Python 3.8, frozen DTO, synchronous, no external execution

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple
import uuid

from sam.execution.execution_request import (
    ExecutionRequest, ExecutionTarget, ExecutionParameter,
    ExecutionPlan, ExecutionStatus, ExecutionRisk,
)
from sam.execution.connector_registry import ConnectorRegistry
from sam.execution.connector_protocol import ConnectorProtocol
from sam.execution.execution_planner import ExecutionPlanner
from sam.execution.approval_execution import (
    ExecutionApprovalBridge, ApprovalRequest, ApprovalResult,
)
from sam.execution.integration_execution import ExecutionPipelineResult

from .connector_runtime import (
    ConnectorRuntime, ConnectorSession, ConnectorContext, ConnectorHealth,
)
from .connector_capability import CapabilitySet, CapabilityReport, CapabilityMatcher
from .connector_policy import PolicyEvaluator, PolicyDecision
from .connector_health import ConnectorHealthEngine, HealthReport
from .conversation_connector import ConversationConnectorBridge, ConnectorQueryResult
from .dashboard_connector import ConnectorDashboardBuilder, ConnectorDashboard


@dataclass(frozen=True)
class ConnectorPipelineResult:
    pipeline_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    session: Optional[ConnectorSession] = None
    context: Optional[ConnectorContext] = None
    capability_check: Tuple[str, ...] = field(default_factory=tuple)
    policy_decision: Optional[PolicyDecision] = None
    execution_request: Optional[ExecutionRequest] = None
    execution_plan: Optional[ExecutionPlan] = None
    approval_result: Optional[ApprovalResult] = None
    conversation_summary: Optional[ConnectorQueryResult] = None
    dashboard: Optional[ConnectorDashboard] = None
    pipeline_complete: bool = False
    error: str = ""
    timestamp: datetime = field(default_factory=datetime.utcnow)


class ConnectorIntegrationPipeline:
    """Integration pipeline: Planner → Connector Runtime → Guardian → Conversation → Dashboard.

    Pipeline:
    Execution Planner → Connector Runtime → Guardian → Conversation → Dashboard

    No external execution — all preview + approval.
    """

    def __init__(
        self,
        registry: ConnectorRegistry,
        runtime: ConnectorRuntime,
        planner: Optional[ExecutionPlanner] = None,
        approval_bridge: Optional[ExecutionApprovalBridge] = None,
        policy_evaluator: Optional[PolicyEvaluator] = None,
        health_engine: Optional[ConnectorHealthEngine] = None,
        conversation_bridge: Optional[ConversationConnectorBridge] = None,
        dashboard_builder: Optional[ConnectorDashboardBuilder] = None,
    ) -> None:
        self._registry = registry
        self._runtime = runtime
        self._planner = planner or ExecutionPlanner()
        self._approval_bridge = approval_bridge or ExecutionApprovalBridge()
        self._policy = policy_evaluator or PolicyEvaluator()
        self._health = health_engine or ConnectorHealthEngine(registry)
        self._conversation = conversation_bridge or ConversationConnectorBridge(
            registry, runtime, self._policy, self._health,
        )
        self._dashboard_builder = dashboard_builder or ConnectorDashboardBuilder()

    # --- Pipeline Steps ---

    def select_and_validate(
        self, connector_type: str, action: str,
        target_name: str = "",
    ) -> Tuple[Optional[ConnectorProtocol], ConnectorContext, Tuple[str, ...]]:
        """Step 1: Select connector, create context, validate capability."""
        connector = self._runtime.select_connector(connector_type)
        if connector is None:
            return (None, ConnectorContext(), ("No connector found",))

        target = ExecutionTarget(name=target_name or connector_type)
        session = self._runtime.create_session(connector.info.connector_id)

        errors = self._runtime.validate_capability(connector, action)
        if errors:
            return (connector, ConnectorContext(), errors)

        preview = self._runtime.compile_preview(connector, action, target)
        context = self._runtime.create_context(
            session, connector_type, action, target,
            preview=preview,
        )
        return (connector, context, ())

    def check_policy(
        self, connector: ConnectorProtocol, context: ConnectorContext,
        action: str, risk_level: str = "medium",
    ) -> PolicyDecision:
        """Step 2: Check connector policy."""
        return self._policy.evaluate(
            connector_name=connector.info.name,
            connector_type=connector.info.connector_type,
            capability=action,
            risk_level=risk_level,
            connector_healthy=connector.info.healthy,
        )

    def create_and_plan_request(
        self, connector: ConnectorProtocol, context: ConnectorContext,
    ) -> Tuple[ExecutionRequest, ExecutionPlan]:
        """Step 3: Create execution request and plan."""
        req = connector.build_request(
            action=context.capability,
            target=context.target or ExecutionTarget(name="unknown"),
        )
        plan = self._planner.plan((req,),
                                  description=f"{connector.info.name} {context.capability}")
        return (req, plan)

    def approve_request(self, plan: ExecutionPlan,
                        approve: bool = True) -> ApprovalResult:
        """Step 4: Create and execute approval."""
        ar = self._approval_bridge.create_approval_request(plan)
        if approve:
            return self._approval_bridge.approve(ar)
        return self._approval_bridge.reject(ar, reason="Rejected by pipeline")

    # --- Full Pipeline ---

    def run(
        self,
        connector_type: str,
        action: str,
        target_name: str = "",
        risk_level: str = "medium",
        approve: bool = True,
    ) -> ConnectorPipelineResult:
        """Run the full connector integration pipeline.

        Planner → Connector Runtime → Guardian → Conversation → Dashboard
        """
        try:
            # Step 1: Select & validate
            connector, context, errors = self.select_and_validate(
                connector_type, action, target_name,
            )
            if errors:
                return ConnectorPipelineResult(
                    pipeline_complete=False,
                    error="; ".join(errors),
                )

            # Step 2: Policy check
            policy_decision = self.check_policy(
                connector, context, action, risk_level,
            )
            if not policy_decision.approved:
                # Still continue, just note the violations
                pass

            # Step 3: Create & plan request
            req, plan = self.create_and_plan_request(connector, context)

            # Step 4: Approval
            approval_result = self.approve_request(plan, approve)

            # Step 5: Conversation summary
            conv = self._conversation.query("connector status")

            # Step 6: Dashboard
            dash = self._dashboard_builder.build(
                self._registry, self._runtime,
                self._policy, self._health,
            )

            return ConnectorPipelineResult(
                session=self._runtime.get_session(
                    context.session_id if context else ""
                ),
                context=context,
                capability_check=errors,
                policy_decision=policy_decision,
                execution_request=req,
                execution_plan=plan,
                approval_result=approval_result,
                conversation_summary=conv,
                dashboard=dash,
                pipeline_complete=True,
            )

        except Exception as e:
            return ConnectorPipelineResult(
                pipeline_complete=False,
                error=str(e),
            )
