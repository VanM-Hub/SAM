"""Dashboard Audit Bridge — 5 PolicyCards (Sprint 212)."""
from __future__ import annotations

from ..dashboard import PolicyCard
from .audit_registry import AuditRegistry


class DashboardAuditBridge:
    """Bridge dashboard — 5 kartu fondasi audit."""

    def __init__(self, registry: AuditRegistry) -> None:
        self._registry = registry

    def cards(self):
        n = self._registry.count()
        immutable = "immutable" if self._registry.count() >= 0 else "immutable"
        return [
            PolicyCard("ad.count", "audit", "ready",
                          f"{n} audit descriptor(s) registered",
                          "foundation", "ready"),
            PolicyCard("ad.immutable", "audit", immutable,
                          "immutable audit model (no write)",
                          "audit", immutable),
            PolicyCard("ad.preview", "audit", "ready",
                          "preview-only registry (no storage)",
                          "audit", "ready"),
            PolicyCard("ad.noexec", "audit", "ready",
                          "no_execute=true (read-only source)",
                          "audit", "ready"),
            PolicyCard("ad.deterministic", "audit", "ready",
                          "deterministic provenance hash",
                          "audit", "ready"),
        ]

    def verdict_card(self):
        return self.cards()[1]
