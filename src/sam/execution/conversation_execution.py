# OP-396 — Conversation Execution Bridge
# Python 3.8 compatible, frozen dataclass, synchronous only
# Read-only query interface for execution-related information
# Does NOT execute anything

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
from .connector_protocol import ConnectorInfo, ConnectorCapability, ConnectorProtocol
from .connector_registry import ConnectorRegistry, RegistryEntry, CapabilityLookup
from .execution_planner import ExecutionPlanner
from .approval_execution import (
    ExecutionApprovalBridge,
    ApprovalRequest,
    ApprovalResult,
)


# ---------------------------------------------------------------------------
# Query Result DTOs
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ExecutionQueryResult:
    """Standard DTO for execution conversation queries."""
    query_type: str = ""
    data: Any = None
    count: int = 0
    timestamp: datetime = field(default_factory=datetime.utcnow)


# ---------------------------------------------------------------------------
# ConversationExecutionBridge
# ---------------------------------------------------------------------------

class ConversationExecutionBridge:
    """Read-only query bridge for execution-related information.

    Queries:
    - execution status
    - execution readiness
    - connector status
    - connector capability
    - execution preview
    - approval requirement
    - rollback plan
    - estimated duration
    - risk
    - dependency
    """

    def __init__(
        self,
        registry: ConnectorRegistry,
        planner: Optional[ExecutionPlanner] = None,
    ) -> None:
        self._registry = registry
        self._planner = planner or ExecutionPlanner()

    # --- Query Dispatcher ---

    def query(
        self,
        query_type: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> ExecutionQueryResult:
        """Dispatch a query to the appropriate handler."""
        params = params or {}
        handlers = {
            "execution status": self._query_execution_status,
            "execution readiness": self._query_execution_readiness,
            "connector status": self._query_connector_status,
            "connector capability": self._query_connector_capability,
            "execution preview": self._query_execution_preview,
            "approval requirement": self._query_approval_requirement,
            "rollback plan": self._query_rollback_plan,
            "estimated duration": self._query_estimated_duration,
            "risk": self._query_risk,
            "dependency": self._query_dependency,
        }
        handler = handlers.get(query_type.lower())
        if handler is None:
            return ExecutionQueryResult(
                query_type=query_type,
                data={"error": f"Unknown query type: {query_type}"},
                count=0,
            )
        return handler(params)

    # --- Handlers ---

    def _query_execution_status(self, params: Dict[str, Any]) -> ExecutionQueryResult:
        """Query execution status overview."""
        summary = self._registry.health_summary()
        data = {
            "total_connectors": summary["total_connectors"],
            "healthy": summary["healthy"],
            "unhealthy": summary["unhealthy"],
            "by_type": summary["by_type"],
        }
        return ExecutionQueryResult(
            query_type="execution status",
            data=data,
            count=summary["total_connectors"],
        )

    def _query_execution_readiness(self, params: Dict[str, Any]) -> ExecutionQueryResult:
        """Query execution readiness assessment."""
        summary = self._registry.health_summary()
        all_healthy = summary["unhealthy"] == 0
        has_connectors = summary["total_connectors"] > 0

        data = {
            "ready": all_healthy and has_connectors,
            "has_connectors": has_connectors,
            "all_connectors_healthy": all_healthy,
            "total_connectors": summary["total_connectors"],
            "healthy_count": summary["healthy"],
            "unhealthy_count": summary["unhealthy"],
        }
        return ExecutionQueryResult(
            query_type="execution readiness",
            data=data,
            count=1,
        )

    def _query_connector_status(self, params: Dict[str, Any]) -> ExecutionQueryResult:
        """Query connector(s) status."""
        entries = self._registry.list()
        connector_type = params.get("connector_type")

        if connector_type:
            entries = tuple(e for e in entries if e.connector_type == connector_type)

        data = {
            "connectors": [
                {
                    "name": e.name,
                    "type": e.connector_type,
                    "version": e.version,
                    "healthy": e.healthy,
                    "capabilities": e.capability_actions,
                    "priority": e.priority,
                }
                for e in entries
            ],
        }
        return ExecutionQueryResult(
            query_type="connector status",
            data=data,
            count=len(entries),
        )

    def _query_connector_capability(self, params: Dict[str, Any]) -> ExecutionQueryResult:
        """Query connector capabilities."""
        action = params.get("action", "")
        if action:
            lookup = self._registry.capability_lookup(action)
            data = {
                "action": action,
                "available": lookup.total_found > 0,
                "connector_types": lookup.connector_types,
                "connector_ids": lookup.connector_ids,
            }
            return ExecutionQueryResult(
                query_type="connector capability",
                data=data,
                count=lookup.total_found,
            )

        # List all capabilities
        entries = self._registry.list()
        all_actions: Dict[str, List[str]] = {}
        for e in entries:
            for action_name in e.capability_actions:
                all_actions.setdefault(action_name, []).append(e.name)

        data = {
            "total_supported_actions": len(all_actions),
            "capabilities": {
                action_name: {
                    "available_connectors": len(conn_names),
                    "connector_names": conn_names,
                }
                for action_name, conn_names in sorted(all_actions.items())
            },
        }
        return ExecutionQueryResult(
            query_type="connector capability",
            data=data,
            count=len(all_actions),
        )

    def _query_execution_preview(self, params: Dict[str, Any]) -> ExecutionQueryResult:
        """Query execution preview for a request."""
        connector_type = params.get("connector_type", "")
        action = params.get("action", "")

        connectors = self._registry.find_by_type(connector_type)
        if not connectors and connector_type:
            connectors = self._registry.find_by_action(action)

        previews: List[str] = []
        for conn in connectors:
            if action and action not in conn.supported_actions():
                continue
            try:
                req = conn.build_request(
                    action=action or "preview",
                    target=None,  # type: ignore - will preview without target
                )
                previews.append(conn.preview(req))
            except Exception:
                previews.append(f"[{conn.info.name}] Could not generate preview")

        data = {
            "previews": previews,
            "total": len(previews),
        }
        return ExecutionQueryResult(
            query_type="execution preview",
            data=data,
            count=len(previews),
        )

    def _query_approval_requirement(self, params: Dict[str, Any]) -> ExecutionQueryResult:
        """Query approval requirement for execution."""
        risk_level = params.get("risk_level", "low")
        requires_approval = risk_level in ("medium", "high", "critical")

        data = {
            "requires_approval": requires_approval,
            "risk_level": risk_level,
            "approval_required_for_levels": ["medium", "high", "critical"],
            "comment": "All execution requests with risk medium+ require human approval",
        }
        return ExecutionQueryResult(
            query_type="approval requirement",
            data=data,
            count=1,
        )

    def _query_rollback_plan(self, params: Dict[str, Any]) -> ExecutionQueryResult:
        """Query rollback plan information."""
        rollback_available = params.get("rollback_available", False)
        risk_level = params.get("risk_level", "low")
        rollback_required = risk_level in ("high", "critical")

        data = {
            "rollback_available": rollback_available,
            "rollback_required": rollback_required,
            "risk_level": risk_level,
            "note": "Rollback is required for high and critical risk executions",
        }
        return ExecutionQueryResult(
            query_type="rollback plan",
            data=data,
            count=1,
        )

    def _query_estimated_duration(self, params: Dict[str, Any]) -> ExecutionQueryResult:
        """Query estimated duration."""
        request_count = params.get("request_count", 1)
        estimated = request_count * 1  # 1 second per request heuristic

        data = {
            "request_count": request_count,
            "estimated_duration_seconds": estimated,
            "estimated_duration_human": f"{estimated}s",
        }
        return ExecutionQueryResult(
            query_type="estimated duration",
            data=data,
            count=1,
        )

    def _query_risk(self, params: Dict[str, Any]) -> ExecutionQueryResult:
        """Query risk assessment."""
        risk_level = params.get("risk_level", "low")
        score_map = {"low": 0.1, "medium": 0.4, "high": 0.7, "critical": 0.9}

        data = {
            "risk_level": risk_level,
            "risk_score": score_map.get(risk_level, 0.1),
            "requires_approval": risk_level in ("medium", "high", "critical"),
            "requires_guardian": risk_level == "critical",
        }
        return ExecutionQueryResult(
            query_type="risk",
            data=data,
            count=1,
        )

    def _query_dependency(self, params: Dict[str, Any]) -> ExecutionQueryResult:
        """Query dependency information."""
        dependencies = self._planner.get_dependencies()

        data = {
            "total_dependencies": len(dependencies),
            "dependencies": [
                {
                    "from": d.from_request_id[:8] if d.from_request_id else "",
                    "to": d.to_request_id[:8] if d.to_request_id else "",
                    "type": d.dependency_type,
                }
                for d in dependencies
            ],
        }
        return ExecutionQueryResult(
            query_type="dependency",
            data=data,
            count=len(dependencies),
        )
