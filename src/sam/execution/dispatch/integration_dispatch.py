# OP-428 — Integration Dispatch
# Python 3.8, frozen DTO, synchronous, no connector execute

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple
import uuid

from sam.execution.engine.execution_builder import ExecutionBuilder, ExecutionPackage
from sam.execution.engine.execution_validator import ExecutionValidator
from sam.execution.engine.rollback_planner import RollbackPlanner
from sam.execution.engine.execution_scheduler import ExecutionScheduler
from sam.execution.execution_request import ExecutionPlan

from .dispatch_request import (
    DispatchRequest, DispatchTask, DispatchStatus, DispatchPriority,
)
from .dispatcher import ConnectorDispatcher, DispatchContext, DispatchSession
from .dispatch_validator import DispatchValidator, DispatchValidationReport
from .dispatch_queue import DispatchQueue, QueuedDispatch
from .dispatch_audit import DispatchAudit, DispatchAuditEntry
from .conversation_dispatch import ConversationDispatchBridge, DispatchQueryResult
from .dashboard_dispatch import DispatchDashboardBuilder, DispatchDashboard

from sam.execution.connector_registry import ConnectorRegistry
from sam.execution.connectors.connector_runtime import ConnectorRuntime
from sam.execution.connectors.connector_policy import PolicyEvaluator
from sam.execution.connectors.mock_connectors import (
    MockFilesystemConnector, MockRESTConnector,
    MockGitConnector, MockShellConnector,
)


@dataclass(frozen=True)
class DispatchPipelineResult:
    pipeline_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    dispatch_request: Optional[DispatchRequest] = None
    validation: Optional[DispatchValidationReport] = None
    queued: Optional[QueuedDispatch] = None
    audit_entry: Optional[DispatchAuditEntry] = None
    conversation_result: Optional[DispatchQueryResult] = None
    dashboard: Optional[DispatchDashboard] = None
    pipeline_complete: bool = False
    error: str = ""
    timestamp: datetime = field(default_factory=datetime.utcnow)


class DispatchIntegrationPipeline:
    """Integration pipeline: Engine → Dispatch Builder → Validator → Queue → Audit → Guardian → Conversation → Dashboard.

    Pipeline:
    Execution Engine → Dispatch Builder → Dispatch Validator → Dispatch Queue → Audit → Guardian → Conversation → Dashboard

    No connector execution — produces preview and queued dispatch.
    """

    def __init__(
        self,
        registry: ConnectorRegistry,
        runtime: ConnectorRuntime,
        policy: PolicyEvaluator,
        dispatcher: Optional[ConnectorDispatcher] = None,
        validator: Optional[DispatchValidator] = None,
        queue: Optional[DispatchQueue] = None,
        audit: Optional[DispatchAudit] = None,
        conversation_bridge: Optional[ConversationDispatchBridge] = None,
        dashboard_builder: Optional[DispatchDashboardBuilder] = None,
    ) -> None:
        self._registry = registry
        self._runtime = runtime
        self._policy = policy
        self._dispatcher = dispatcher or ConnectorDispatcher(registry, runtime, policy)
        self._validator = validator or DispatchValidator()
        self._queue = queue or DispatchQueue()
        self._audit = audit or DispatchAudit()
        self._conversation = conversation_bridge or ConversationDispatchBridge(
            self._dispatcher, self._validator, self._queue, self._audit,
        )
        self._dashboard_builder = dashboard_builder or DispatchDashboardBuilder()

    def run(
        self,
        plan: ExecutionPlan,
        approval_exists: bool = False,
    ) -> DispatchPipelineResult:
        """Run the full dispatch integration pipeline."""
        try:
            # Build execution package
            b = ExecutionBuilder()
            pkg = b.build(plan)

            # Build dispatch
            session = self._dispatcher.create_session()
            context = self._dispatcher.build_dispatch(pkg, session)

            if context.dispatch_request is None:
                return DispatchPipelineResult(
                    pipeline_complete=False,
                    error="Failed to build dispatch request",
                )

            req = context.dispatch_request

            # Validate
            report = self._validator.validate(
                req,
                connector_exists=True,
                connector_healthy=context.connector_healthy,
                approval_exists=approval_exists,
            )

            # Audit: created
            self._audit.record(req.request_id, "created", f"Built from plan {plan.plan_id[:8]}")

            if report.passed:
                self._audit.record(req.request_id, "validated", "Validation passed")

                # Enqueue
                queued = self._queue.enqueue(req)
                self._audit.record(req.request_id, "queued",
                                    f"Queued with priority {req.priority.value}")

                # Preview
                self._audit.record(req.request_id, "previewed", context.preview[:100])
            else:
                queued = None

            # Conversation
            conv = self._conversation.query("dispatch statistics")

            # Dashboard
            dash = self._dashboard_builder.build(
                self._queue, self._audit,
                connector_count=self._registry.count,
                healthy_count=self._registry.count,  # mocks are always healthy
            )

            return DispatchPipelineResult(
                dispatch_request=req,
                validation=report,
                queued=queued,
                conversation_result=conv,
                dashboard=dash,
                pipeline_complete=True,
            )

        except Exception as e:
            return DispatchPipelineResult(
                pipeline_complete=False,
                error=str(e),
            )

    def run_from_requests(self, *requests) -> DispatchPipelineResult:
        plan = ExecutionPlan(requests=requests)
        return self.run(plan)
