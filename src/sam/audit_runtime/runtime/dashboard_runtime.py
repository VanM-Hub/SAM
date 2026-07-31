"""Dashboard Runtime Bridge — 5 PolicyCards (Sprint 215)."""
from __future__ import annotations

from ..dashboard import PolicyCard
from ..foundation.audit_registry import AuditRegistry
from .audit_summary import AuditSummarizer


class DashboardRuntimeBridge:
    """Bridge dashboard — 5 kartu runtime audit."""

    def __init__(self, registry: AuditRegistry) -> None:
        self._registry = registry

    def cards(self):
        s = AuditSummarizer().summarize(self._registry)
        return [
            PolicyCard("ar.runtime", "audit", "ready",
                          f"{s.total} audit(s), {len(s.categories)} categories",
                          "runtime", "ready"),
            PolicyCard("ar.preview", "audit", "preview_only",
                          "preview-only runtime (no execute)",
                          "runtime", "preview_only"),
            PolicyCard("ar.noexec", "audit", "ready",
                          "not llm, not ai, no inference",
                          "runtime", "ready"),
            PolicyCard("ar.immutable", "audit", "immutable",
                          "immutable audit model",
                          "runtime", "immutable"),
            PolicyCard("ar.deterministic", "audit", "ready",
                          "deterministic provenance source",
                          "runtime", "ready"),
        ]

    def verdict_card(self):
        return self.cards()[1]
