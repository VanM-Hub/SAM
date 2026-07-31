"""Dashboard Skill Bridge — 5 ExecutionCards (Sprint 164)."""
from __future__ import annotations

from .skill_registry import SkillRegistry
from ..dashboard.skill_dashboard import ExecutionCard


class DashboardSkillBridge:
    """Bridge dashboard — 5 kartu untuk skill foundation."""

    def __init__(self, registry: SkillRegistry) -> None:
        self._registry = registry

    def cards(self):
        total = self._registry.count()
        return [
            ExecutionCard("skill.foundation", "skill", "ready",
                          f"{total} skill(s) registered", "skill registry", "ready"),
            ExecutionCard("skill.descriptor", "skill", "ready",
                          "descriptors stored", "registry query", "ready"),
            ExecutionCard("skill.capability", "skill", "ready",
                          "capabilities attached", "registry query", "ready"),
            ExecutionCard("skill.contract", "skill", "ready",
                          "contracts attached", "registry query", "ready"),
            ExecutionCard("skill.metadata", "skill", "ready",
                          "metadata attached", "registry query", "ready"),
        ]

    def overview_card(self):
        return self.cards()[0]
