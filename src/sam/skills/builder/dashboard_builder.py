"""Dashboard Builder Bridge — 5 ExecutionCards (Sprint 166)."""
from __future__ import annotations

from .skill_builder import SkillBuilder
from ..dashboard.skill_dashboard import ExecutionCard


class DashboardBuilderBridge:
    """Bridge dashboard — 5 kartu untuk skill builder."""

    def __init__(self, builder: SkillBuilder = None) -> None:
        self._builder = builder or SkillBuilder()

    def cards(self):
        return [
            ExecutionCard("build.descriptor", "builder", "ready",
                          "descriptor built from DTO", "skill builder", "ready"),
            ExecutionCard("build.definition", "builder", "ready",
                          "definition built from DTO", "skill builder", "ready"),
            ExecutionCard("build.workflow", "builder", "ready",
                          "workflow assembled", "skill builder", "ready"),
            ExecutionCard("build.preview", "builder", "ready",
                          "preview generated (external_calls=0)",
                          "skill builder", "ready"),
            ExecutionCard("build.no_exec", "builder", "ready",
                          "build-only, no execution", "skill builder", "ready"),
        ]

    def overview_card(self):
        return self.cards()[0]
