"""Scope Builder — builder scope audit (Sprint 214)."""
from __future__ import annotations

from ..model.audit_scope import AuditScope


class ScopeBuilder:
    """Builder scope audit — membentuk DTO saja, tidak menyimpan."""

    def build(self, scope: str = "system") -> AuditScope:
        return AuditScope(scope=scope)
