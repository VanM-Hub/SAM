# OP-401 — Connector Runtime
# Python 3.8, frozen DTO, synchronous, no execute/network/subprocess
# Pipeline: Registry → Select Connector → Capability Validation → Permission Validation → Execution Preview → Guardian Check → Conversation DTO

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple
import uuid

from sam.execution.execution_request import (
    ExecutionRequest, ExecutionTarget, ExecutionParameter,
    ExecutionPlan, ExecutionStatus, ExecutionRisk,
)
from sam.execution.connector_protocol import ConnectorProtocol, ConnectorInfo, BaseConnector
from sam.execution.connector_registry import ConnectorRegistry


@dataclass(frozen=True)
class ConnectorSession:
    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    connector_id: str = ""
    started_at: datetime = field(default_factory=datetime.utcnow)
    request_count: int = 0
    status: str = "active"  # active, completed, failed


@dataclass(frozen=True)
class ConnectorContext:
    context_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str = ""
    connector_type: str = ""
    capability: str = ""
    target: Optional[ExecutionTarget] = None
    risk_assessment: Optional[ExecutionRisk] = None
    policy_decision: str = "pending"
    guardian_approved: bool = False
    preview: str = ""


@dataclass(frozen=True)
class ConnectorHealth:
    healthy: bool = True
    uptime_seconds: int = 0
    last_check: datetime = field(default_factory=datetime.utcnow)
    message: str = ""


@dataclass(frozen=True)
class ConnectorRuntimeSnapshot:
    snapshot_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    total_sessions: int = 0
    active_sessions: int = 0
    total_connectors: int = 0
    healthy_connectors: int = 0
    last_error: str = ""
    timestamp: datetime = field(default_factory=datetime.utcnow)


class ConnectorRuntime:
    """Runtime for selecting, validating, and previewing connector operations.

    Pipeline: Registry → Select Connector → Capability Validation
             → Permission Validation → Execution Preview → Guardian Check → Conversation DTO

    Does NOT execute anything — preview only.
    """

    def __init__(self, registry: ConnectorRegistry) -> None:
        self._registry = registry
        self._sessions: Dict[str, ConnectorSession] = {}
        self._healthy: Dict[str, bool] = {}
        self._errors: List[str] = []

    # --- Session Management ---

    def create_session(self, connector_id: str) -> ConnectorSession:
        session = ConnectorSession(connector_id=connector_id)
        self._sessions[session.session_id] = session
        self._healthy[connector_id] = True
        return session

    def get_session(self, session_id: str) -> Optional[ConnectorSession]:
        return self._sessions.get(session_id)

    def close_session(self, session_id: str) -> bool:
        session = self._sessions.pop(session_id, None)
        if session:
            self._sessions[session_id] = ConnectorSession(
                session_id=session.session_id,
                connector_id=session.connector_id,
                started_at=session.started_at,
                request_count=session.request_count,
                status="completed",
            )
            return True
        return False

    # --- Runtime Pipeline ---

    def select_connector(self, connector_type: str) -> Optional[ConnectorProtocol]:
        connectors = self._registry.find_by_type(connector_type)
        return connectors[0] if connectors else None

    def validate_capability(
        self, connector: ConnectorProtocol, action: str
    ) -> Tuple[str, ...]:
        errors: List[str] = []
        if action and action not in connector.supported_actions():
            errors.append(f"Action '{action}' not supported by {connector.info.name}")
        return tuple(errors)

    def create_context(
        self,
        session: ConnectorSession,
        connector_type: str,
        capability: str,
        target: Optional[ExecutionTarget] = None,
        risk: Optional[ExecutionRisk] = None,
        preview: str = "",
    ) -> ConnectorContext:
        return ConnectorContext(
            session_id=session.session_id,
            connector_type=connector_type,
            capability=capability,
            target=target,
            risk_assessment=risk,
            preview=preview,
        )

    def compile_preview(self, connector: ConnectorProtocol, action: str,
                        target: ExecutionTarget) -> str:
        req = connector.build_request(action, target)
        return connector.preview(req)

    def mark_guardian_approval(self, context: ConnectorContext,
                               approved: bool) -> ConnectorContext:
        return ConnectorContext(
            context_id=context.context_id,
            session_id=context.session_id,
            connector_type=context.connector_type,
            capability=context.capability,
            target=context.target,
            risk_assessment=context.risk_assessment,
            policy_decision="approved" if approved else "denied",
            guardian_approved=approved,
            preview=context.preview,
        )

    def to_conversation_dto(self, context: ConnectorContext) -> Dict[str, Any]:
        return {
            "connector_type": context.connector_type,
            "capability": context.capability,
            "preview": context.preview,
            "guardian_approved": context.guardian_approved,
            "policy_decision": context.policy_decision,
            "target": context.target.name if context.target else "unknown",
        }

    # --- Health & Snapshot ---

    def get_connector_health(self, connector_id: str) -> ConnectorHealth:
        healthy = self._healthy.get(connector_id, True)
        return ConnectorHealth(
            healthy=healthy,
            message="Healthy" if healthy else "Unhealthy",
        )

    def set_connector_health(self, connector_id: str, healthy: bool,
                             message: str = "") -> None:
        self._healthy[connector_id] = healthy
        if not healthy:
            self._errors.append(f"[{connector_id}] {message or 'Unhealthy'}")

    def snapshot(self) -> ConnectorRuntimeSnapshot:
        active = sum(1 for s in self._sessions.values() if s.status == "active")
        total_connectors = self._registry.count
        healthy_count = sum(
            1 for v in self._healthy.values() if v
        ) if self._healthy else total_connectors
        last_err = self._errors[-1] if self._errors else ""

        return ConnectorRuntimeSnapshot(
            total_sessions=len(self._sessions),
            active_sessions=active,
            total_connectors=total_connectors,
            healthy_connectors=healthy_count,
            last_error=last_err,
        )

    def clear_errors(self) -> None:
        self._errors.clear()
