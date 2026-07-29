# OP-422 — Connector Dispatcher
# Python 3.8, frozen DTO, synchronous, no execute

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple
import uuid

from sam.execution.execution_request import ExecutionTarget
from sam.execution.engine.execution_builder import ExecutionPackage
from sam.execution.connector_registry import ConnectorRegistry
from sam.execution.connector_protocol import ConnectorProtocol, BaseConnector
from sam.execution.connectors.connector_runtime import ConnectorRuntime
from sam.execution.connectors.connector_policy import PolicyEvaluator, PolicyDecision
from sam.execution.connectors.mock_connectors import (
    MockFilesystemConnector, MockRESTConnector,
    MockGitConnector, MockShellConnector,
)

from .dispatch_request import (
    DispatchRequest, DispatchTarget, DispatchTask, DispatchBatch,
    DispatchMetadata, DispatchStatus, DispatchPriority, DispatchSummary,
)


@dataclass(frozen=True)
class DispatchSession:
    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    started_at: datetime = field(default_factory=datetime.utcnow)
    dispatch_count: int = 0
    status: str = "active"


@dataclass(frozen=True)
class DispatchContext:
    context_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str = ""
    dispatch_request: Optional[DispatchRequest] = None
    connector_healthy: bool = True
    policy_approved: bool = True
    preview: str = ""
    validated: bool = False


@dataclass(frozen=True)
class DispatchReport:
    report_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    total_requests: int = 0
    successful: int = 0
    failed: int = 0
    previews: Tuple[str, ...] = field(default_factory=tuple)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    errors: Tuple[str, ...] = field(default_factory=tuple)


class ConnectorDispatcher:
    """Dispatches execution packages to connectors.

    Pipeline:
    Execution Package → Connector Selection → Capability Validation
    → Policy Validation → Dispatch Build → Preview Dispatch

    Does NOT execute — builds dispatch request and generates preview.
    """

    def __init__(
        self,
        registry: ConnectorRegistry,
        runtime: ConnectorRuntime,
        policy: PolicyEvaluator,
    ) -> None:
        self._registry = registry
        self._runtime = runtime
        self._policy = policy
        self._sessions: Dict[str, DispatchSession] = {}

    def create_session(self) -> DispatchSession:
        session = DispatchSession()
        self._sessions[session.session_id] = session
        return session

    def get_session(self, session_id: str) -> Optional[DispatchSession]:
        return self._sessions.get(session_id)

    def select_connector(self, connector_type: str) -> Optional[ConnectorProtocol]:
        return self._runtime.select_connector(connector_type)

    def _make_target(self, connector: ConnectorProtocol) -> DispatchTarget:
        return DispatchTarget(
            connector_id=connector.info.connector_id,
            connector_type=connector.info.connector_type,
            healthy=connector.info.healthy,
        )

    def build_dispatch(
        self,
        package: ExecutionPackage,
        session: DispatchSession,
    ) -> DispatchContext:
        """Build a dispatch request from an execution package."""
        if not package.tasks:
            return DispatchContext(session_id=session.session_id,
                                    validated=False)

        tasks: List[DispatchTask] = []
        errors: List[str] = []
        previews: List[str] = []
        connector = None

        for t in package.tasks:
            task = DispatchTask(
                task_id=t.task_id,
                name=t.name,
                action=t.action,
                target=t.target,
                estimated_duration_seconds=t.estimated_duration_seconds,
            )
            tasks.append(task)

            # Try to select connector and preview
            if not connector and t.connector_type:
                connector = self.select_connector(t.connector_type)

            if connector and t.connector_type == connector.info.connector_type:
                target = ExecutionTarget(name=t.target or t.connector_type)
                preview = self._runtime.compile_preview(connector, t.action, target)
                previews.append(preview)
            else:
                previews.append(f"[MOCK] {t.action} on {t.target or t.connector_type}")

        if not connector:
            # Use default mock connector
            connector = MockFilesystemConnector()

        target = self._make_target(connector)
        meta = DispatchMetadata(
            source="execution_engine",
            connector_type=connector.info.connector_type,
            package_id=package.package_id,
        )

        req = DispatchRequest(
            package_id=package.package_id,
            tasks=tuple(tasks),
            target=target,
            metadata=meta,
            requires_approval=package.requires_approval,
        )

        # Policy check
        policy_decision = self._policy.evaluate(
            connector_name=connector.info.name,
            connector_type=connector.info.connector_type,
            capability=tasks[0].action if tasks else "read",
            connector_healthy=connector.info.healthy,
        )

        return DispatchContext(
            session_id=session.session_id,
            dispatch_request=req,
            connector_healthy=connector.info.healthy,
            policy_approved=policy_decision.approved,
            preview="; ".join(previews[:3]),
            validated=policy_decision.approved and connector.info.healthy,
        )

    def build_report(self, contexts: Tuple[DispatchContext, ...]) -> DispatchReport:
        successful = sum(1 for c in contexts if c.validated)
        failed = len(contexts) - successful
        previews = tuple(c.preview for c in contexts if c.preview)
        errors = tuple(
            f"Dispatch {c.context_id[:8]}: not validated"
            for c in contexts if not c.validated
        )
        return DispatchReport(
            total_requests=len(contexts),
            successful=successful,
            failed=failed,
            previews=previews,
            errors=errors,
        )
