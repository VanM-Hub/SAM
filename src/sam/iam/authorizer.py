"""IAM Authorizer — RBAC (Role-Based Access Control).

Menutup gap H5 (Program D / MISSION-2D, EA-001-005): authorization untuk user
yang TIDAK ada sebelumnya. Menggunakan pola subject/resource/permission yang
kompatibel dengan model `runtime_kernel.runtime_security.AccessControl`,
sehingga hasil keputusan IAM dapat dipetakan ke lapisan akses existing bila
dintegrasikan (keputusan arsitektur terpisah, di luar scope H5).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, FrozenSet, Iterable, Optional

from sam.iam.principal import Principal, Role


@dataclass(frozen=True)
class Resource:
    """Resource yang menjadi target akses (mis. "api:health", "runtime:mission")."""

    kind: str       # namespace (api, runtime, config, workflow, ...)
    name: str       # nama resource

    def __str__(self) -> str:
        return f"{self.kind}:{self.name}"

    @staticmethod
    def parse(value: str) -> "Resource":
        if ":" not in value:
            raise ValueError(f"resource harus format 'kind:name', dapat: {value}")
        kind, name = value.split(":", 1)
        return Resource(kind=kind, name=name)


@dataclass(frozen=True)
class Permission:
    """Izin (action) pada resource."""

    action: str  # read | write | execute | admin

    def __str__(self) -> str:
        return self.action


@dataclass(frozen=True)
class RoleAssignments:
    """Mapping role -> permission."""

    role_id: str = ""
    permissions: frozenset[str] = frozenset()


@dataclass(frozen=True)
class AccessDecision:
    allowed: bool
    principal_id: str = ""
    resource: str = ""
    action: str = ""
    role_used: str = ""
    reason: str = ""

    @property
    def ok(self) -> bool:
        return self.allowed


class Authorizer:
    """Evaluasi akses (RBAC) berdasarkan role principal.

    Aturan:
    - principal harus punya role yang memuat (action, resource) yang diminta.
    - role 'admin' memiliki wildcard akses (full).
    - resource match: role.permissions berisi "action:kind:name" persis, atau
      "action:kind:*" (wildcard per kind), atau "action:*" (wildcard semua).
    """

    def __init__(self, role_permissions: Optional[Dict[str, frozenset[str]]] = None) -> None:
        # role_id -> set permission string ("action:kind:name")
        self._roles: Dict[str, frozenset[str]] = dict(role_permissions or {})

    def register_role(self, role_id: str, permissions: Iterable[str]) -> None:
        perms = frozenset(p.strip() for p in permissions if p.strip())
        self._roles[role_id] = perms

    def unregister_role(self, role_id: str) -> None:
        self._roles.pop(role_id, None)

    def has_role(self, role_id: str) -> bool:
        return role_id in self._roles

    def role_permissions(self, role_id: str) -> frozenset[str]:
        return self._roles.get(role_id, frozenset())

    def _check_perm_set(self, perms: FrozenSet[str], action: str, res: str) -> bool:
        # res = "kind:name"
        if f"{action}:{res}" in perms:
            return True
        kind, _ = res.split(":", 1)
        if f"{action}:{kind}:*" in perms:
            return True
        if f"{action}:*" in perms:
            return True
        return False

    def authorize(
        self,
        principal: Optional[Principal],
        resource: Resource,
        action: str,
    ) -> AccessDecision:
        res_str = str(resource)
        if principal is None:
            return AccessDecision(False, reason="no principal", resource=res_str, action=action)

        for role_id in principal.roles:
            perms = self._roles.get(role_id, frozenset())
            if role_id == "admin":
                return AccessDecision(True, principal.principal_id, res_str, action, "admin", "admin role")
            if self._check_perm_set(perms, action, res_str):
                return AccessDecision(
                    True, principal.principal_id, res_str, action, role_id, f"role {role_id}",
                )
        return AccessDecision(False, principal.principal_id, res_str, action, reason="no permission")
