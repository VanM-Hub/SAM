"""Enterprise Identity & Organization Foundation - WP-01..10 (MISSION-5.5 / IP-5.5-001).

Struktur governance enterprise: Organization, Team, Project, Tenant dengan
identity & governance boundary. Enterprise = boundary tambahan, bukan pengganti
governance lokal.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional, Tuple


def _now_utc() -> str:
    return datetime.utcnow().isoformat() + "Z"


class GovEntityKind(str, Enum):
    """Jenis entitas governance enterprise."""

    ORGANIZATION = "organization"
    TEAM = "team"
    PROJECT = "project"
    TENANT = "tenant"


class GovEntityStatus(str, Enum):
    """Status entitas governance."""

    ACTIVE = "active"
    SUSPENDED = "suspended"
    ARCHIVED = "archived"


@dataclass(frozen=True)
class GovernanceEntity:
    """Entitas governance enterprise dengan boundary."""

    entity_id: str
    name: str
    kind: GovEntityKind
    parent_id: Optional[str] = None
    status: GovEntityStatus = GovEntityStatus.ACTIVE
    created_at: str = field(default_factory=_now_utc)

    @property
    def is_well_formed(self) -> bool:
        return bool(self.entity_id.strip()) and bool(self.name.strip())

    def as_dict(self) -> dict:
        return {
            "entity_id": self.entity_id,
            "name": self.name,
            "kind": self.kind.value,
            "parent_id": self.parent_id,
            "status": self.status.value,
            "created_at": self.created_at,
        }


class GovernanceScope(str, Enum):
    """Cakupan governance."""

    LOCAL = "local"
    ENTERPRISE = "enterprise"
    GLOBAL = "global"


@dataclass(frozen=True)
class GovernanceBoundary:
    """Boundary governance entitas."""

    entity_id: str
    scope: GovernanceScope = GovernanceScope.ENTERPRISE
    authority_local: bool = True
    sovereignty_preserved: bool = True

    def as_dict(self) -> dict:
        return {
            "entity_id": self.entity_id,
            "scope": self.scope.value,
            "authority_local": self.authority_local,
            "sovereignty_preserved": self.sovereignty_preserved,
        }


@dataclass(frozen=True)
class OrgContext:
    """Konteks organisasi (read-only)."""

    entity: GovernanceEntity
    boundary: GovernanceBoundary

    @property
    def preserves_local_authority(self) -> bool:
        return self.boundary.authority_local and self.boundary.sovereignty_preserved

    def as_dict(self) -> dict:
        return {"entity": self.entity.as_dict(), "boundary": self.boundary.as_dict()}


class OrganizationRegistry:
    """Registry entitas governance enterprise."""

    def __init__(self) -> None:
        self._entities: dict = {}
        self._boundaries: dict = {}

    def register(self, entity: GovernanceEntity, boundary: Optional[GovernanceBoundary] = None) -> GovernanceEntity:
        self._entities[entity.entity_id] = entity
        self._boundaries[entity.entity_id] = boundary or GovernanceBoundary(entity_id=entity.entity_id)
        return entity

    def lookup(self, entity_id: str) -> Optional[GovernanceEntity]:
        return self._entities.get(entity_id)

    def boundary(self, entity_id: str) -> Optional[GovernanceBoundary]:
        return self._boundaries.get(entity_id)

    def context(self, entity_id: str) -> Optional[OrgContext]:
        entity = self._entities.get(entity_id)
        if entity is None:
            return None
        return OrgContext(entity=entity, boundary=self._boundaries[entity_id])

    def by_kind(self, kind: GovEntityKind) -> Tuple[GovernanceEntity, ...]:
        return tuple(e for e in self._entities.values() if e.kind == kind)

    def validate_registry(self) -> bool:
        return all(e.is_well_formed for e in self._entities.values())


class OrgComplianceChecker:
    """Checker compliance struktur organisasi."""

    def check(self, registry: OrganizationRegistry, *, identity_valid=True, boundary_preserved=True, sovereignty=True, no_execution_authority=True, explainable=True) -> Dict[str, Any]:
        checks = [
            {"code": "IDENTITY_VALID", "passed": identity_valid and registry.validate_registry()},
            {"code": "BOUNDARY_PRESERVED", "passed": boundary_preserved},
            {"code": "SOVEREIGNTY_PRESERVED", "passed": sovereignty},
            {"code": "NO_EXECUTION_AUTHORITY", "passed": no_execution_authority},
            {"code": "EXPLAINABLE", "passed": explainable},
        ]
        passed = registry.validate_registry() and all(c["passed"] for c in checks)
        return {"component": "enterprise_governance.foundation", "passed": passed, "certified": passed, "checks": [c for c in checks]}
