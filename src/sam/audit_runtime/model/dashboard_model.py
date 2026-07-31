"""Dashboard Model Bridge — 5 PolicyCards (Sprint 213)."""
from __future__ import annotations

from ..dashboard import PolicyCard
from .audit_scope import VALID_SCOPES


class DashboardModelBridge:
    """Bridge dashboard — 5 kartu model audit."""

    def cards(self):
        return [
            PolicyCard("am.immutable", "audit", "immutable",
                          "frozen immutable audit model",
                          "model", "immutable"),
            PolicyCard("am.scopes", "audit", "ready",
                          f"{len(VALID_SCOPES)} valid audit scopes",
                          "model", "ready"),
            PolicyCard("am.record", "audit", "ready",
                          "AuditRecord, AuditEntry, AuditReference",
                          "model", "ready"),
            PolicyCard("am.noexec", "audit", "ready",
                          "no execute / no write validation",
                          "model", "ready"),
            PolicyCard("am.deterministic", "audit", "ready",
                          "deterministic validation",
                          "model", "ready"),
        ]

    def verdict_card(self):
        return self.cards()[0]
