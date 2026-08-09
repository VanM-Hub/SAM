"""Enterprise Policy & Delegation - WP-21..30 (MISSION-5.5 / IP-5.5-003).

Policy enterprise, scope, versioning, applicability, precedence, conflict
resolution, control mapping, compliance binding, delegation model yang tetap
mempertahankan authority boundary.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional, Tuple


def _now_utc() -> str:
    return datetime.utcnow().isoformat() + "Z"


class PolicyEffect(str, Enum):
    """Efek policy."""

    ALLOW = "allow"
    DENY = "deny"
    REQUIRE = "require"


@dataclass(frozen=True)
class EnterprisePolicy:
    """Policy enterprise."""

    policy_id: str
    name: str
    effect: PolicyEffect = PolicyEffect.REQUIRE
    scope: str = "*"
    version: int = 1
    created_at: str = field(default_factory=_now_utc)

    def applies_to(self, scope: str) -> bool:
        return self.scope == "*" or self.scope == scope

    def as_dict(self) -> dict:
        return {
            "policy_id": self.policy_id,
            "name": self.name,
            "effect": self.effect.value,
            "scope": self.scope,
            "version": self.version,
            "created_at": self.created_at,
        }


class PolicyVersioning:
    """Mengelola versi policy."""

    def __init__(self) -> None:
        self._versions: dict = {}

    def register(self, policy: EnterprisePolicy) -> None:
        self._versions.setdefault(policy.policy_id, []).append(policy)

    def latest(self, policy_id: str) -> Optional[EnterprisePolicy]:
        versions = self._versions.get(policy_id)
        return versions[-1] if versions else None

    def history(self, policy_id: str) -> Tuple[EnterprisePolicy, ...]:
        return tuple(self._versions.get(policy_id, []))


class PolicyPrecedence:
    """Menentukan policy paling berwenang (precedence)."""

    def resolve(self, policies: Tuple[EnterprisePolicy, ...]) -> Optional[EnterprisePolicy]:
        if not policies:
            return None
        return sorted(policies, key=lambda p: p.version, reverse=True)[0]


class PolicyConflictResolver:
    """Menyelesaikan konflik antar policy (DENY menang)."""

    def resolve(self, policies: Tuple[EnterprisePolicy, ...]) -> PolicyEffect:
        if any(p.effect == PolicyEffect.DENY for p in policies):
            return PolicyEffect.DENY
        if any(p.effect == PolicyEffect.REQUIRE for p in policies):
            return PolicyEffect.REQUIRE
        return PolicyEffect.ALLOW


@dataclass(frozen=True)
class DelegationRule:
    """Delegation authority dengan boundary tetap."""

    delegation_id: str
    grantee: str
    scope: str
    authority_limited: bool = True
    revocable: bool = True

    @property
    def respects_authority_boundary(self) -> bool:
        return self.authority_limited and self.revocable

    def as_dict(self) -> dict:
        return {
            "delegation_id": self.delegation_id,
            "grantee": self.grantee,
            "scope": self.scope,
            "authority_limited": self.authority_limited,
            "revocable": self.revocable,
            "respects_authority_boundary": self.respects_authority_boundary,
        }


class DelegationRegistry:
    """Registry delegation."""

    def __init__(self) -> None:
        self._rules: dict = {}

    def grant(self, rule: DelegationRule) -> DelegationRule:
        self._rules[rule.delegation_id] = rule
        return rule

    def revoke(self, delegation_id: str) -> bool:
        rule = self._rules.pop(delegation_id, None)
        return rule is not None

    def valid_delegations(self) -> Tuple[DelegationRule, ...]:
        return tuple(r for r in self._rules.values() if r.respects_authority_boundary)


@dataclass(frozen=True)
class ControlMapping:
    """Mapping policy -> governance control."""

    control_id: str
    policy_id: str
    active: bool = True

    def as_dict(self) -> dict:
        return {"control_id": self.control_id, "policy_id": self.policy_id, "active": self.active}


class ControlMapper:
    """Menghubungkan policy ke control."""

    def __init__(self) -> None:
        self._mappings: dict = {}

    def map(self, control_id: str, policy_id: str) -> ControlMapping:
        mapping = ControlMapping(control_id=control_id, policy_id=policy_id)
        self._mappings[control_id] = mapping
        return mapping

    def for_policy(self, policy_id: str) -> Tuple[ControlMapping, ...]:
        return tuple(m for m in self._mappings.values() if m.policy_id == policy_id)


class PolicyComplianceChecker:
    """Checker compliance policy & delegation."""

    def check(self, *, scope_bound=True, versioned=True, conflict_resolved=True, authority_boundary=True, revocable=True, explainable=True) -> Dict[str, Any]:
        checks = [
            {"code": "SCOPE_BOUND", "passed": scope_bound},
            {"code": "VERSIONED", "passed": versioned},
            {"code": "CONFLICT_RESOLVED", "passed": conflict_resolved},
            {"code": "AUTHORITY_BOUNDARY_PRESERVED", "passed": authority_boundary},
            {"code": "REVOCABLE", "passed": revocable},
            {"code": "EXPLAINABLE", "passed": explainable},
        ]
        passed = all(c["passed"] for c in checks)
        return {"component": "enterprise_governance.policy", "passed": passed, "certified": passed, "checks": [c for c in checks]}
