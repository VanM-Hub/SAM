"""Dashboard Definition Bridge — 5 ExecutionCards (Sprint 165)."""
from __future__ import annotations

from .skill_definition import SkillDefinition
from ..dashboard.skill_dashboard import ExecutionCard


class DashboardDefinitionBridge:
    """Bridge dashboard — 5 kartu untuk skill definition."""

    def __init__(self, definition: SkillDefinition = None) -> None:
        self._definition = definition

    def cards(self):
        has = self._definition is not None
        n_in = self._definition.input_count if has else 0
        n_out = self._definition.output_count if has else 0
        return [
            ExecutionCard("def.definition", "definition", "ready",
                          "definition stored" if has else "no definition",
                          "skill definition", "ready"),
            ExecutionCard("def.inputs", "definition", "ready",
                          f"{n_in} input(s)", "definition", "ready"),
            ExecutionCard("def.outputs", "definition", "ready",
                          f"{n_out} output(s)", "definition", "ready"),
            ExecutionCard("def.parameters", "definition", "ready",
                          "parameters tracked", "definition", "ready"),
            ExecutionCard("def.constraints", "definition", "ready",
                          "constraints tracked", "definition", "ready"),
        ]

    def overview_card(self):
        return self.cards()[0]
