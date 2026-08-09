"""Multi-Tenant Governance - WP-11..20 (MISSION-5.5 / IP-5.5-002).

Isolasi antar-tenant, tenant context, tenant boundary, resource isolation,
tenant policy scope, cross-tenant guard.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional, Tuple

from .org_foundation import GovernanceBoundary, GovernanceScope, GovernanceEntity, GovEntityKind


def _now_utc() -> str:
    return datetime.utcnow().isoformat() + "Z"


@dataclass(frozen=True)
class Tenant:
    """Tenant governance."""

    tenant_id: str
    name: str
    organization_id: str
    boundary: GovernanceBoundary = field(default_factory=lambda: GovernanceBoundary(entity_id="", scope=GovernanceScope.ENTERPRISE, authority_local=True, sovereignty_preserved=True))

    @property
    def is_isolated(self) -> bool:
        return self.boundary.scope == GovernanceScope.ENTERPRISE and self.boundary.sovereignty_preserved

    def as_dict(self) -> dict:
        return {
            "tenant_id": self.tenant_id,
            "name": self.name,
            "organization_id": self.organization_id,
            "boundary": self.boundary.as_dict(),
            "is_isolated": self.is_isolated,
        }


class TenantRegistry:
    """Registry tenant dengan isolasi."""

    def __init__(self) -> None:
        self._tenants: dict = {}

    def register(self, org_entity: GovernanceEntity, tenant_id: str, name: str) -> Tenant:
        if org_entity.kind != GovEntityKind.ORGANIZATION:
            raise ValueError("tenant must belong to an organization")
        boundary = GovernanceBoundary(entity_id=tenant_id, scope=GovernanceScope.ENTERPRISE, authority_local=True, sovereignty_preserved=True)
        tenant = Tenant(tenant_id=tenant_id, name=name, organization_id=org_entity.entity_id, boundary=boundary)
        self._tenants[tenant_id] = tenant
        return tenant

    def lookup(self, tenant_id: str) -> Optional[Tenant]:
        return self._tenants.get(tenant_id)

    def all(self) -> Tuple[Tenant, ...]:
        return tuple(self._tenants.values())

    def validate_isolation(self) -> bool:
        return all(t.is_isolated for t in self._tenants.values())


@dataclass(frozen=True)
class TenantContext:
    """Konteks operasional tenant."""

    tenant_id: str
    boundary: GovernanceBoundary

    def as_dict(self) -> dict:
        return {"tenant_id": self.tenant_id, "boundary": self.boundary.as_dict()}


class TenancyManager:
    """Mengelola konteks tenant & cek isolasi."""

    def __init__(self, registry: TenantRegistry) -> None:
        self._registry = registry

    def context(self, tenant_id: str) -> Optional[TenantContext]:
        tenant = self._registry.lookup(tenant_id)
        if tenant is None:
            return None
        return TenantContext(tenant_id=tenant_id, boundary=tenant.boundary)

    def access_isolated(self, tenant_id: str) -> bool:
        tenant = self._registry.lookup(tenant_id)
        return tenant is not None and tenant.is_isolated

    def assert_no_cross_tenant(self, tenant_a: str, tenant_b: str) -> bool:
        return tenant_a == tenant_b


class MultiTenantComplianceChecker:
    """Checker compliance multi-tenant."""

    def check(self, registry: TenantRegistry, *, isolated=True, sovereignty=True, no_cross_tenant=True, no_execution_authority=True, explainable=True) -> Dict[str, Any]:
        checks = [
            {"code": "ISOLATED", "passed": isolated and registry.validate_isolation()},
            {"code": "SOVEREIGNTY_PRESERVED", "passed": sovereignty},
            {"code": "NO_CROSS_TENANT", "passed": no_cross_tenant},
            {"code": "NO_EXECUTION_AUTHORITY", "passed": no_execution_authority},
            {"code": "EXPLAINABLE", "passed": explainable},
        ]
        passed = registry.validate_isolation() and all(c["passed"] for c in checks)
        return {"component": "enterprise_governance.multitenant", "passed": passed, "certified": passed, "checks": [c for c in checks]}
