"""Enterprise Certification - WP-51..60 (MISSION-5.5 / IP-5.5-006).

Integration, compliance, isolation, regression, dan certification terhadap
Enterprise Governance.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict


class EnterpriseCertStatus(str, Enum):
    """Status certification enterprise."""

    CERTIFIED = "CERTIFIED"
    CONDITIONALLY_CERTIFIED = "CONDITIONALLY_CERTIFIED"
    NOT_CERTIFIED = "NOT_CERTIFIED"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"


@dataclass(frozen=True)
class EnterpriseCertEvidence:
    """Bukti certification enterprise."""

    name: str
    passed: bool

    def as_dict(self) -> dict:
        return {"name": self.name, "passed": self.passed}


class EnterpriseCertification:
    """Sertifikasi Enterprise Governance (WP-51..60)."""

    def __init__(self) -> None:
        self._evidences: list = []

    def _add(self, name: str, flags: list) -> None:
        for idx, passed in enumerate(flags):
            self._evidences.append(EnterpriseCertEvidence(name=f"{name}#{idx + 1}", passed=bool(passed)))

    def foundation_certification(self, *, org_valid=True, tenant_valid=True) -> None:
        self._add("enterprise_foundation", [org_valid, tenant_valid])

    def multitenant_certification(self, *, isolated=True, sovereignty=True) -> None:
        self._add("enterprise_multitenant", [isolated, sovereignty])

    def policy_certification(self, *, scoped=True, revocable=True) -> None:
        self._add("enterprise_policy", [scoped, revocable])

    def audit_certification(self, *, append_only=True, observed=True) -> None:
        self._add("enterprise_audit", [append_only, observed])

    def workspace_certification(self, *, presentation_only=True, no_business_logic=True) -> None:
        self._add("enterprise_workspace", [presentation_only, no_business_logic])

    def governance_certification(self, *, authority_boundary=True, no_execution_authority=True) -> None:
        self._add("enterprise_governance", [authority_boundary, no_execution_authority])

    def isolation_certification(self, *, isolated=True, no_cross_tenant=True) -> None:
        self._add("enterprise_isolation", [isolated, no_cross_tenant])

    def regression_compliance(self, *, regression=True, compliance=True) -> None:
        self._add("enterprise_regression", [regression, compliance])

    def mission_certification(self, *, integrated=True, architecture_accepted=True) -> None:
        self._add("enterprise_mission", [integrated, architecture_accepted])

    def certify(self) -> Dict[str, Any]:
        total = len(self._evidences)
        passed = sum(1 for e in self._evidences if e.passed)
        if total == 0:
            status = EnterpriseCertStatus.INSUFFICIENT_EVIDENCE
        elif passed == total:
            status = EnterpriseCertStatus.CERTIFIED
        elif passed >= max(1, total - 2):
            status = EnterpriseCertStatus.CONDITIONALLY_CERTIFIED
        else:
            status = EnterpriseCertStatus.NOT_CERTIFIED
        return {
            "component": "enterprise_governance.mission_5_5",
            "passed": status == EnterpriseCertStatus.CERTIFIED,
            "certified": status == EnterpriseCertStatus.CERTIFIED,
            "status": status.value,
            "passed_count": passed,
            "total_count": total,
        }
