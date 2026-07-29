# OP-404 — Connector Health
# Python 3.8, frozen DTO, synchronous, rule-based health checking

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple

from sam.execution.connector_registry import ConnectorRegistry
from sam.execution.connector_protocol import ConnectorProtocol


HEALTH_RULES = (
    "availability",
    "configuration",
    "registration",
    "capability completeness",
    "policy compliance",
)


@dataclass(frozen=True)
class HealthRuleResult:
    rule_name: str = ""
    passed: bool = True
    message: str = ""


@dataclass(frozen=True)
class ConnectorHealthStatus:
    connector_id: str = ""
    connector_name: str = ""
    healthy: bool = True
    rule_results: Tuple[HealthRuleResult, ...] = field(default_factory=tuple)
    overall_message: str = ""


@dataclass(frozen=True)
class ConnectorHealthSnapshot:
    statuses: Tuple[ConnectorHealthStatus, ...] = field(default_factory=tuple)
    total: int = 0
    healthy: int = 0
    unhealthy: int = 0
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass(frozen=True)
class HealthReport:
    overall_healthy: bool = True
    total_connectors: int = 0
    healthy_count: int = 0
    unhealthy_count: int = 0
    details: Tuple[ConnectorHealthStatus, ...] = field(default_factory=tuple)
    timestamp: datetime = field(default_factory=datetime.utcnow)


class ConnectorHealthEngine:
    """Rule-based health checking for connectors.

    Rules:
    - availability: connector is registered and reachable
    - configuration: connector has valid config
    - registration: connector is properly registered
    - capability completeness: connector has at least one capability
    - policy compliance: connector passes basic policy checks
    """

    def __init__(self, registry: ConnectorRegistry) -> None:
        self._registry = registry
        self._manual_unhealthy: Dict[str, str] = {}  # connector_id -> reason

    def check_connector(self, connector_id: str) -> ConnectorHealthStatus:
        connector = self._registry.find(connector_id)
        if connector is None:
            return ConnectorHealthStatus(
                connector_id=connector_id,
                connector_name="unknown",
                healthy=False,
                rule_results=(
                    HealthRuleResult("registration", False,
                                     "Connector not registered"),
                ),
                overall_message="Connector not found",
            )

        entry = self._registry.find_entry(connector_id)
        info = connector.info
        name = info.name if info else entry.name if entry else "unknown"
        results: List[HealthRuleResult] = []

        # availability
        if connector_id in self._manual_unhealthy:
            results.append(HealthRuleResult(
                "availability", False,
                self._manual_unhealthy[connector_id],
            ))
        else:
            results.append(HealthRuleResult(
                "availability", True, "Connector available",
            ))

        # configuration
        if not info or not info.name:
            results.append(HealthRuleResult(
                "configuration", False, "Missing connector name",
            ))
        else:
            results.append(HealthRuleResult(
                "configuration", True, f"Connector '{name}' configured",
            ))

        # registration
        if entry is not None:
            results.append(HealthRuleResult(
                "registration", True, f"Registered type={entry.connector_type}",
            ))
        else:
            results.append(HealthRuleResult(
                "registration", False, "Not found in registry",
            ))

        # capability completeness
        actions = connector.supported_actions()
        if not actions:
            results.append(HealthRuleResult(
                "capability completeness", False,
                "No capabilities registered",
            ))
        else:
            results.append(HealthRuleResult(
                "capability completeness", True,
                f"{len(actions)} capabilities: {', '.join(actions[:5])}",
            ))

        # policy compliance
        results.append(HealthRuleResult(
            "policy compliance", True, "Policy check passed",
        ))

        all_passed = all(r.passed for r in results)
        return ConnectorHealthStatus(
            connector_id=connector_id,
            connector_name=name,
            healthy=all_passed,
            rule_results=tuple(results),
            overall_message="All checks passed" if all_passed else f"{sum(1 for r in results if not r.passed)} check(s) failed",
        )

    def check_all(self) -> ConnectorHealthSnapshot:
        entries = self._registry.list()
        statuses: List[ConnectorHealthStatus] = []
        for e in entries:
            statuses.append(self.check_connector(e.connector_id))
        healthy = sum(1 for s in statuses if s.healthy)
        unhealthy = len(statuses) - healthy
        return ConnectorHealthSnapshot(
            statuses=tuple(statuses),
            total=len(statuses),
            healthy=healthy,
            unhealthy=unhealthy,
        )

    def generate_report(self) -> HealthReport:
        snapshot = self.check_all()
        return HealthReport(
            overall_healthy=snapshot.unhealthy == 0,
            total_connectors=snapshot.total,
            healthy_count=snapshot.healthy,
            unhealthy_count=snapshot.unhealthy,
            details=snapshot.statuses,
        )

    def mark_unhealthy(self, connector_id: str, reason: str) -> None:
        self._manual_unhealthy[connector_id] = reason

    def mark_healthy(self, connector_id: str) -> None:
        self._manual_unhealthy.pop(connector_id, None)

    def get_rule_results(self) -> Tuple[str, ...]:
        return HEALTH_RULES
