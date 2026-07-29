# OP-403 — Connector Policy
# Python 3.8, frozen DTO, synchronous, no execute/network/subprocess

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple

from .connector_capability import Capability, CapabilitySet


MINIMAL_POLICIES = (
    "connector enabled",
    "connector trusted",
    "capability allowed",
    "approval required",
    "guardian required",
    "read only mode",
    "maintenance mode",
    "connector health",
)


@dataclass(frozen=True)
class PolicyViolation:
    policy_name: str = ""
    message: str = ""
    severity: str = "warning"  # warning, error, critical


@dataclass(frozen=True)
class PolicyDecision:
    approved: bool = True
    violations: Tuple[PolicyViolation, ...] = field(default_factory=tuple)
    details: str = ""

    @property
    def has_violations(self) -> bool:
        return len(self.violations) > 0

    @property
    def has_errors(self) -> bool:
        return any(v.severity in ("error", "critical") for v in self.violations)


@dataclass(frozen=True)
class ConnectorPolicy:
    name: str = ""
    enabled: bool = True
    params: Dict[str, Any] = field(default_factory=dict)


class PolicyEvaluator:
    """Evaluates connector operations against configured policies.

    Minimal policies:
    - connector enabled
    - connector trusted
    - capability allowed
    - approval required
    - guardian required
    - read only mode
    - maintenance mode
    - connector health
    """

    def __init__(self) -> None:
        self._policies: Dict[str, ConnectorPolicy] = {
            "connector enabled": ConnectorPolicy(
                name="connector enabled", enabled=True,
                params={"enabled_connectors": []},  # empty = all enabled
            ),
            "connector trusted": ConnectorPolicy(
                name="connector trusted", enabled=True,
                params={"trusted_connectors": []},
            ),
            "capability allowed": ConnectorPolicy(
                name="capability allowed", enabled=True,
                params={"blocked_capabilities": ["execute", "delete"]},
            ),
            "approval required": ConnectorPolicy(
                name="approval required", enabled=True,
                params={"auto_approve_low_risk": True},
            ),
            "guardian required": ConnectorPolicy(
                name="guardian required", enabled=True,
                params={"guardian_risk_threshold": "high"},
            ),
            "read only mode": ConnectorPolicy(
                name="read only mode", enabled=True,
                params={"read_only": False},
            ),
            "maintenance mode": ConnectorPolicy(
                name="maintenance mode", enabled=True,
                params={"maintenance": False},
            ),
            "connector health": ConnectorPolicy(
                name="connector health", enabled=True,
                params={"require_healthy": True},
            ),
        }

    # --- Policy Config ---

    def get_policy(self, name: str) -> Optional[ConnectorPolicy]:
        return self._policies.get(name)

    def set_policy(self, name: str, params: Dict[str, Any]) -> bool:
        p = self._policies.get(name)
        if p is None:
            return False
        merged = dict(p.params)
        merged.update(params)
        self._policies[name] = ConnectorPolicy(
            name=p.name, enabled=p.enabled, params=merged,
        )
        return True

    def enable_policy(self, name: str, enabled: bool) -> bool:
        p = self._policies.get(name)
        if p is None:
            return False
        self._policies[name] = ConnectorPolicy(
            name=p.name, enabled=enabled, params=p.params,
        )
        return True

    def list_policies(self) -> Tuple[ConnectorPolicy, ...]:
        return tuple(self._policies.values())

    # --- Evaluation ---

    def evaluate(
        self,
        connector_name: str = "",
        connector_type: str = "",
        capability: str = "",
        risk_level: str = "low",
        connector_healthy: bool = True,
    ) -> PolicyDecision:
        violations: List[PolicyViolation] = []

        for p in self._policies.values():
            if not p.enabled:
                continue

            v = self._evaluate_single(
                p, connector_name, connector_type,
                capability, risk_level, connector_healthy,
            )
            if v:
                violations.append(v)

        has_blocking = any(v.severity in ("error", "critical") for v in violations)
        return PolicyDecision(
            approved=not has_blocking,
            violations=tuple(violations),
            details=f"Evaluated {len(self._policies)} policies: {len(violations)} violation(s)",
        )

    def _evaluate_single(
        self, policy: ConnectorPolicy,
        connector_name: str, connector_type: str,
        capability: str, risk_level: str,
        connector_healthy: bool,
    ) -> Optional[PolicyViolation]:
        name = policy.name
        params = policy.params

        if name == "connector enabled":
            enabled_list: List[str] = params.get("enabled_connectors", [])
            if enabled_list and connector_type not in enabled_list:
                return PolicyViolation(
                    name, f"Connector type '{connector_type}' not enabled",
                    "error",
                )

        elif name == "connector trusted":
            trusted_list: List[str] = params.get("trusted_connectors", [])
            if trusted_list and connector_type not in trusted_list:
                return PolicyViolation(
                    name, f"Connector type '{connector_type}' not trusted",
                    "error",
                )

        elif name == "capability allowed":
            blocked: List[str] = params.get("blocked_capabilities", [])
            if capability in blocked:
                return PolicyViolation(
                    name, f"Capability '{capability}' is blocked",
                    "error",
                )

        elif name == "approval required":
            auto_low = params.get("auto_approve_low_risk", True)
            if not auto_low and risk_level == "low":
                pass  # Still requires approval
            elif risk_level in ("medium", "high", "critical"):
                return PolicyViolation(
                    name, f"Risk level '{risk_level}' requires approval",
                    "info",
                )

        elif name == "guardian required":
            threshold = params.get("guardian_risk_threshold", "high")
            risk_order = {"low": 0, "medium": 1, "high": 2, "critical": 3}
            if risk_order.get(risk_level, 0) >= risk_order.get(threshold, 2):
                return PolicyViolation(
                    name, f"Risk level '{risk_level}' requires guardian review",
                    "warning",
                )

        elif name == "read only mode":
            if params.get("read_only", False) and capability in (
                    "write", "create", "delete", "execute", "rollback"):
                return PolicyViolation(
                    name, "System is read-only, write operations blocked",
                    "error",
                )

        elif name == "maintenance mode":
            if params.get("maintenance", False):
                return PolicyViolation(
                    name, "System in maintenance mode, operations blocked",
                    "error",
                )

        elif name == "connector health":
            if params.get("require_healthy", True) and not connector_healthy:
                return PolicyViolation(
                    name, f"Connector '{connector_name}' is unhealthy",
                    "error",
                )

        return None

    def evaluate_capability(
        self, capability_set: CapabilitySet, action: str,
        connector_name: str = "", connector_type: str = "",
        connector_healthy: bool = True,
    ) -> PolicyDecision:
        cap = capability_set.get(action)
        risk_level = cap.risk_level if cap else "medium"
        return self.evaluate(
            connector_name=connector_name,
            connector_type=connector_type,
            capability=action,
            risk_level=risk_level,
            connector_healthy=connector_healthy,
        )
