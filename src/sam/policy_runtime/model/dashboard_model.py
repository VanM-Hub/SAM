"""Dashboard Model Bridge — 5 PolicyCards (Sprint 205)."""
from __future__ import annotations

from ..dashboard import PolicyCard
from .policy import Policy
from .policy_validator import PolicyValidator


class DashboardModelBridge:
    """Bridge dashboard — 5 kartu untuk model policy."""

    def __init__(self) -> None:
        self._validator = PolicyValidator()

    def cards(self, policy: Policy = None):
        pol = policy or Policy("pol0")
        return [
            PolicyCard("md.policy", "model", "ready",
                       f"{pol.policy_id} ({pol.rule_count()} rules)",
                       "policy", "ready"),
            PolicyCard("md.rule", "model", "ready",
                       "PolicyRule frozen", "rule", "ready"),
            PolicyCard("md.scope", "model", "ready",
                       "PolicyScope validated", "scope", "ready"),
            PolicyCard("md.constraint", "model", "ready",
                       "PolicyConstraint frozen", "constraint", "ready"),
            PolicyCard("md.valid", "model", "ready",
                       "PolicyValidator deterministic", "no-inference", "ready"),
        ]

    def overview_card(self):
        return self.cards()[0]
