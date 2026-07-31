"""Dashboard Policy Bridge — 5 PolicyCards (Sprint 204)."""
from __future__ import annotations

from ..dashboard import PolicyCard
from .policy_registry import PolicyRegistry


class DashboardPolicyBridge:
    """Bridge dashboard — 5 kartu untuk fondasi policy."""

    def __init__(self, registry: PolicyRegistry) -> None:
        self._registry = registry

    def cards(self):
        n = self._registry.count()
        verdict = "ready" if n > 0 else "empty"
        return [
            PolicyCard("fd.policy", "foundation", verdict,
                       f"{n} policy descriptor(s)", "policy foundation", verdict),
            PolicyCard("fd.descriptor", "foundation", "ready",
                       "PolicyDescriptor frozen", "deterministic", "ready"),
            PolicyCard("fd.capability", "foundation", "ready",
                       "PolicyCapability frozen", "no-inference", "ready"),
            PolicyCard("fd.contract", "foundation", "ready",
                       "PolicyContract preview-only", "preview", "ready"),
            PolicyCard("fd.metadata", "foundation", "ready",
                       "PolicyMetadata version 21.0.0", "read-only", "ready"),
        ]

    def overview_card(self):
        return self.cards()[0]
