# OP-406 — Conversation Connector Bridge
# Python 3.8, frozen DTO, synchronous, read-only queries

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple

from sam.execution.connector_registry import ConnectorRegistry
from sam.execution.execution_request import ExecutionTarget
from sam.execution.connector_protocol import ConnectorProtocol

from .connector_runtime import ConnectorRuntime, ConnectorContext, ConnectorHealth
from .connector_capability import CapabilitySet, CapabilityReport, CapabilityMatcher
from .connector_policy import PolicyEvaluator, PolicyDecision
from .connector_health import ConnectorHealthEngine, HealthReport


@dataclass(frozen=True)
class ConnectorQueryResult:
    query_type: str = ""
    data: Any = None
    count: int = 0
    timestamp: datetime = field(default_factory=datetime.utcnow)


class ConversationConnectorBridge:
    """Read-only query bridge for connector operations.

    Query types:
    - connector list
    - connector detail
    - connector capability
    - connector health
    - connector policy
    - execution preview
    - connector status
    - trusted connectors
    - maintenance
    - diagnostic
    """

    def __init__(
        self,
        registry: ConnectorRegistry,
        runtime: ConnectorRuntime,
        policy_evaluator: PolicyEvaluator,
        health_engine: ConnectorHealthEngine,
    ) -> None:
        self._registry = registry
        self._runtime = runtime
        self._policy = policy_evaluator
        self._health = health_engine

    def query(self, query_type: str,
              params: Optional[Dict[str, Any]] = None) -> ConnectorQueryResult:
        params = params or {}
        handlers = {
            "connector list": self._query_list,
            "connector detail": self._query_detail,
            "connector capability": self._query_capability,
            "connector health": self._query_health,
            "connector policy": self._query_policy,
            "execution preview": self._query_preview,
            "connector status": self._query_status,
            "trusted connectors": self._query_trusted,
            "maintenance": self._query_maintenance,
            "diagnostic": self._query_diagnostic,
        }
        handler = handlers.get(query_type.lower())
        if handler is None:
            return ConnectorQueryResult(
                query_type=query_type,
                data={"error": f"Unknown query type: {query_type}"},
                count=0,
            )
        return handler(params)

    def _query_list(self, params: Dict[str, Any]) -> ConnectorQueryResult:
        entries = self._registry.list()
        data = {
            "connectors": [
                {
                    "name": e.name,
                    "type": e.connector_type,
                    "version": e.version,
                    "capabilities": len(e.capability_actions),
                    "healthy": e.healthy,
                    "priority": e.priority,
                }
                for e in entries
            ]
        }
        return ConnectorQueryResult(
            query_type="connector list", data=data, count=len(entries),
        )

    def _query_detail(self, params: Dict[str, Any]) -> ConnectorQueryResult:
        connector_id = params.get("connector_id", "")
        connector = self._registry.find(connector_id) if connector_id else None
        if connector is None:
            return ConnectorQueryResult(
                query_type="connector detail",
                data={"error": "Connector not found"},
                count=0,
            )
        info = connector.info
        data = {
            "name": info.name,
            "type": info.connector_type,
            "version": info.version,
            "description": info.description,
            "capabilities": [cap.action for cap in info.capabilities],
            "healthy": info.healthy,
        }
        return ConnectorQueryResult(
            query_type="connector detail", data=data, count=1,
        )

    def _query_capability(self, params: Dict[str, Any]) -> ConnectorQueryResult:
        connector_type = params.get("connector_type", "")
        if connector_type:
            connectors = self._registry.find_by_type(connector_type)
            all_caps: List[str] = []
            for conn in connectors:
                all_caps.extend(conn.supported_actions())
            all_caps = list(dict.fromkeys(all_caps))  # unique
            report = CapabilityReport(
                total=len(all_caps), names=tuple(all_caps),
            )
        else:
            cs = CapabilitySet.all_builtin()
            report = CapabilityReport.from_set(cs)

        data = {
            "capabilities": report.names,
            "total": report.total,
            "low_risk": report.low_risk,
            "medium_risk": report.medium_risk,
            "high_risk": report.high_risk,
        }
        return ConnectorQueryResult(
            query_type="connector capability", data=data, count=report.total,
        )

    def _query_health(self, params: Dict[str, Any]) -> ConnectorQueryResult:
        report = self._health.generate_report()
        data = {
            "overall_healthy": report.overall_healthy,
            "total": report.total_connectors,
            "healthy": report.healthy_count,
            "unhealthy": report.unhealthy_count,
            "details": [
                {
                    "name": d.connector_name,
                    "healthy": d.healthy,
                    "message": d.overall_message,
                }
                for d in report.details
            ],
        }
        return ConnectorQueryResult(
            query_type="connector health", data=data, count=report.total_connectors,
        )

    def _query_policy(self, params: Dict[str, Any]) -> ConnectorQueryResult:
        policies = self._policy.list_policies()
        data = {
            "policies": [
                {"name": p.name, "enabled": p.enabled, "params": p.params}
                for p in policies
            ],
            "total": len(policies),
        }
        return ConnectorQueryResult(
            query_type="connector policy", data=data, count=len(policies),
        )

    def _query_preview(self, params: Dict[str, Any]) -> ConnectorQueryResult:
        connector_type = params.get("connector_type", "")
        action = params.get("action", "read")
        target_name = params.get("target", "unknown")

        connectors = self._registry.find_by_type(connector_type) if connector_type else []
        if not connectors:
            return ConnectorQueryResult(
                query_type="execution preview",
                data={"error": f"No connector found for type '{connector_type}'"},
                count=0,
            )

        conn = connectors[0]
        target = ExecutionTarget(name=target_name)
        preview = self._runtime.compile_preview(conn, action, target)

        data = {
            "connector": conn.info.name,
            "action": action,
            "target": target_name,
            "preview": preview,
        }
        return ConnectorQueryResult(
            query_type="execution preview", data=data, count=1,
        )

    def _query_status(self, params: Dict[str, Any]) -> ConnectorQueryResult:
        snapshot = self._runtime.snapshot()
        data = {
            "total_sessions": snapshot.total_sessions,
            "active_sessions": snapshot.active_sessions,
            "total_connectors": snapshot.total_connectors,
            "healthy_connectors": snapshot.healthy_connectors,
            "last_error": snapshot.last_error,
        }
        return ConnectorQueryResult(
            query_type="connector status", data=data, count=1,
        )

    def _query_trusted(self, params: Dict[str, Any]) -> ConnectorQueryResult:
        entries = self._registry.list()
        trusted = [
            {"name": e.name, "type": e.connector_type}
            for e in entries if e.healthy
        ]
        return ConnectorQueryResult(
            query_type="trusted connectors", data={"trusted": trusted},
            count=len(trusted),
        )

    def _query_maintenance(self, params: Dict[str, Any]) -> ConnectorQueryResult:
        mp = self._policy.get_policy("maintenance mode")
        rop = self._policy.get_policy("read only mode")
        in_maintenance = mp.params.get("maintenance", False) if mp else False
        read_only = rop.params.get("read_only", False) if rop else False

        data = {
            "maintenance_mode": in_maintenance,
            "read_only_mode": read_only,
            "operations_blocked": in_maintenance,
            "write_operations_blocked": read_only or in_maintenance,
        }
        return ConnectorQueryResult(
            query_type="maintenance", data=data, count=1,
        )

    def _query_diagnostic(self, params: Dict[str, Any]) -> ConnectorQueryResult:
        snapshot = self._runtime.snapshot()
        health_report = self._health.generate_report()

        data = {
            "runtime": {
                "sessions": snapshot.total_sessions,
                "active": snapshot.active_sessions,
                "connectors": snapshot.total_connectors,
                "healthy": snapshot.healthy_connectors,
                "last_error": snapshot.last_error,
            },
            "health": {
                "overall_healthy": health_report.overall_healthy,
                "healthy": health_report.healthy_count,
                "unhealthy": health_report.unhealthy_count,
            },
            "policies": len(self._policy.list_policies()),
        }
        return ConnectorQueryResult(
            query_type="diagnostic", data=data, count=1,
        )
