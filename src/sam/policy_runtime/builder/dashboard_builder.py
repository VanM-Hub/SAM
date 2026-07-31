"""Dashboard Builder Bridge — 5 PolicyCards (Sprint 206)."""
from __future__ import annotations

from ..dashboard import PolicyCard
from ..model.policy import Policy
from .policy_builder import PolicyBuilder


class DashboardBuilderBridge:
    """Bridge dashboard — 5 kartu untuk builder policy."""

    def cards(self, pol: Policy = None):
        pol = pol or PolicyBuilder().build("pol0").policy
        return [
            PolicyCard("bd.policy", "builder", "ready",
                       f"policy {pol.policy_id} ({pol.rule_count()} rules)",
                       "policy", "ready"),
            PolicyCard("bd.rule", "builder", "ready",
                       "RuleBuilder composes DTO", "rule", "ready"),
            PolicyCard("bd.scope", "builder", "ready",
                       "ScopeBuilder composes DTO", "scope", "ready"),
            PolicyCard("bd.preview", "builder", "ready",
                       "PolicyPreviewDTO decided=False ext=0", "preview", "ready"),
            PolicyCard("bd.nodecide", "builder", "ready",
                       "builder: no evaluate, no decision, no inference",
                       "no-inference", "ready"),
        ]

    def overview_card(self):
        return self.cards()[0]
