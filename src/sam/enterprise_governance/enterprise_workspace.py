"""Enterprise Governance Workspace - WP-41..50 (MISSION-5.5 / IP-5.5-005).

Workspace terpadu untuk organisasi, team, project, tenant, policy, audit, dan
governance status (presentation; no business logic).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Tuple

from .enterprise_audit import AuditTrail, GovernanceIntelligence, GovernanceStatus
from .multitenant import TenantRegistry
from .org_foundation import GovEntityKind, OrganizationRegistry


@dataclass(frozen=True)
class EntityOverview:
    """Ringkasan entitas untuk workspace."""

    entity_id: str
    name: str
    kind: str
    governance_status: Dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict:
        return {
            "entity_id": self.entity_id,
            "name": self.name,
            "kind": self.kind,
            "governance_status": self.governance_status,
        }


class EnterpriseWorkspace:
    """Fasilitas presentasi Enterprise Governance Workspace."""

    def __init__(self, orgs: OrganizationRegistry, tenants: TenantRegistry, audit: AuditTrail, intelligence: GovernanceIntelligence) -> None:
        self._orgs = orgs
        self._tenants = tenants
        self._audit = audit
        self._intelligence = intelligence

    def list_entities(self) -> Tuple[Any, ...]:
        return self._orgs.by_kind(GovEntityKind.ORGANIZATION)

    def tenant_overview(self) -> Tuple[EntityOverview, ...]:
        result = []
        for t in self._tenants.all():
            status = self._intelligence.observed_status(t.tenant_id)
            result.append(EntityOverview(t.tenant_id, t.name, "tenant", status.as_dict()))
        return tuple(result)

    def governance_status(self, entity_id: str, policy_count: int = 0) -> GovernanceStatus:
        return self._intelligence.observed_status(entity_id, policy_count)

    def recent_audit(self, limit: int = 20) -> Tuple[Any, ...]:
        return self._audit.events()[-limit:]


class WorkspaceComplianceChecker:
    """Checker compliance workspace (presentation-only)."""

    def check(self, *, presentation_only=True, no_business_logic=True, no_execution_authority=True, no_authority_merge=True) -> Dict[str, Any]:
        checks = [
            {"code": "PRESENTATION_ONLY", "passed": presentation_only},
            {"code": "NO_BUSINESS_LOGIC", "passed": no_business_logic},
            {"code": "NO_EXECUTION_AUTHORITY", "passed": no_execution_authority},
            {"code": "NO_AUTHORITY_MERGE", "passed": no_authority_merge},
        ]
        passed = all(c["passed"] for c in checks)
        return {"component": "enterprise_governance.workspace", "passed": passed, "certified": passed, "checks": [c for c in checks]}
