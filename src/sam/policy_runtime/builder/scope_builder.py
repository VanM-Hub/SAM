"""Scope Builder — membangun PolicyScope (Sprint 206)."""
from __future__ import annotations

from ..model.policy_scope import PolicyScope


class ScopeBuilder:
    """Builder lingkup. Menyusun DTO saja."""

    def build(self, scope: str = "system", targets: list = None) -> PolicyScope:
        return PolicyScope(scope=scope, targets=list(targets or []))
