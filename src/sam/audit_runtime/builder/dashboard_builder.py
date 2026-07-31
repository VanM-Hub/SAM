"""Dashboard Builder Bridge — 5 PolicyCards (Sprint 214)."""
from __future__ import annotations

from ..dashboard import PolicyCard


class DashboardBuilderBridge:
    """Bridge dashboard — 5 kartu builder audit."""

    def cards(self):
        return [
            PolicyCard("ab.build", "audit", "ready",
                          "builder compose DTO only",
                          "builder", "ready"),
            PolicyCard("ab.nostore", "audit", "ready",
                          "no storage (builder does not save)",
                          "builder", "ready"),
            PolicyCard("ab.preview", "audit", "preview_only",
                          "preview DTO (decided=False, external_calls=0)",
                          "builder", "preview_only"),
            PolicyCard("ab.noexec", "audit", "ready",
                          "no execute, no decision",
                          "builder", "ready"),
            PolicyCard("ab.immutable", "audit", "immutable",
                          "build result immutable (frozen)",
                          "builder", "immutable"),
        ]

    def verdict_card(self):
        return self.cards()[2]
