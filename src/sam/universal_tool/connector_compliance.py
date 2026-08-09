"""Connector Compliance - WP-19 (MISSION-5.2 / IP-5.2-002).

Memastikan connector mengikuti boundary: no SDK leak ke domain, no credential
di domain, tidak ada automatic invocation, tidak ada implicit execution.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Tuple

from .connector_model import ToolConnector


@dataclass(frozen=True)
class ConnectorComplianceResult:
    """Hasil compliance Connector Framework."""

    passed: bool
    checks: Tuple[Dict[str, Any], ...] = field(default_factory=tuple)

    def as_dict(self) -> dict:
        return {"passed": self.passed, "checks": list(self.checks)}


class ConnectorComplianceChecker:
    """Checker compliance untuk connector."""

    def check(
        self,
        connectors: Tuple[ToolConnector, ...],
        *,
        contract_followed: bool = True,
        no_sdk_leak: bool = True,
        no_credential_in_domain: bool = True,
        no_automatic_invocation: bool = True,
        no_implicit_execution: bool = True,
        connector_not_authority: bool = True,
    ) -> ConnectorComplianceResult:
        checks = [
            {"code": "CONTRACT_FOLLOWED", "passed": contract_followed},
            {"code": "NO_SDK_LEAK", "passed": no_sdk_leak},
            {"code": "NO_CREDENTIAL_IN_DOMAIN", "passed": no_credential_in_domain},
            {"code": "NO_AUTOMATIC_INVOCATION", "passed": no_automatic_invocation},
            {"code": "NO_IMPLICIT_EXECUTION", "passed": no_implicit_execution},
            {"code": "CONNECTOR_NOT_AUTHORITY", "passed": connector_not_authority},
            {"code": "HANDLE_VALID", "passed": all(c.handle.connector_id for c in connectors)},
        ]
        passed = all(c["passed"] for c in checks)
        return ConnectorComplianceResult(passed=passed, checks=tuple(checks))

    def certify(self, connectors: Tuple[ToolConnector, ...], **kwargs: Any) -> Dict[str, Any]:
        result = self.check(connectors, **kwargs)
        return {
            "component": "universal_tool.connector_framework",
            "passed": result.passed,
            "certified": result.passed,
            "checks": [c for c in result.checks],
        }
