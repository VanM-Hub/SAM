"""Dashboard Runtime Bridge — 5 ExecutionCards (Sprint 167)."""
from __future__ import annotations

from .skill_runtime import SkillRuntime
from ..dashboard.skill_dashboard import ExecutionCard


class DashboardRuntimeBridge:
    """Bridge dashboard — 5 kartu untuk skill runtime."""

    def __init__(self, runtime: SkillRuntime) -> None:
        self._runtime = runtime

    def cards(self):
        n = self._runtime.registry.count()
        return [
            ExecutionCard("runtime.engine", "runtime", "ready",
                          "skill runtime engine", "preview-only", "ready"),
            ExecutionCard("runtime.pipeline", "runtime", "ready",
                          "Descriptor->Definition->Builder->Workflow->Preview",
                          "pipeline", "ready"),
            ExecutionCard("runtime.registry", "runtime", "ready",
                          f"{n} skill(s) in registry", "skill runtime", "ready"),
            ExecutionCard("runtime.external", "runtime", "ready",
                          "external_calls=0", "preview", "ready"),
            ExecutionCard("runtime.deterministic", "runtime", "ready",
                          "synchronous & deterministic", "engine", "ready"),
        ]

    def overview_card(self):
        return self.cards()[0]
