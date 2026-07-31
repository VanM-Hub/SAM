"""Conversation Policy Bridge — query read-only (Sprint 204)."""
from __future__ import annotations

from .policy_registry import PolicyRegistry


class ConversationPolicyBridge:
    """Bridge conversation — status policy read-only."""

    def __init__(self, registry: PolicyRegistry) -> None:
        self._registry = registry

    def summary(self) -> dict:
        return {
            "total_Policy": self._registry.count(),
            "preview_only": True,
        }

    def status(self, policy_id: str) -> str:
        return "registered" if self._registry.exists(policy_id) else "missing"
