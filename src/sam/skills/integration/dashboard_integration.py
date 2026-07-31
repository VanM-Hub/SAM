"""Dashboard Integration Bridge — 5 ExecutionCards (Sprint 171)."""
from __future__ import annotations

from ..foundation.skill_registry import SkillRegistry
from ..dashboard.skill_dashboard import ExecutionCard
from .skill_runtime_pipeline import SkillRuntimePipeline
from .skill_runtime_certification import SkillRuntimeCertifier


class DashboardIntegrationBridge:
    """Bridge dashboard — 5 kartu untuk integrasi skill."""

    def __init__(self, registry: SkillRegistry) -> None:
        self._registry = registry
        self._pipeline = SkillRuntimePipeline(registry)
        self._certifier = SkillRuntimeCertifier()

    def cards(self):
        n = self._registry.count()
        cert = self._certifier.certify()
        verdict = "certified" if cert.certified else "not-certified"
        return [
            ExecutionCard("int.route", "integration", "ready",
                          "Mission->Agent->Skill->Orchestrator->Connector->Provider",
                          "pipeline", "ready"),
            ExecutionCard("int.skill", "integration", "ready",
                          f"{n} skill(s) integrated", "read-only", "ready"),
            ExecutionCard("int.preview", "integration", "ready",
                          "execution preview (external_calls=0)", "preview", "ready"),
            ExecutionCard("int.readonly", "integration", "ready",
                          "0 layer violations - runtime lain tak diubah",
                          "integration", "ready"),
            ExecutionCard("int.cert", "integration", verdict,
                          f"score {cert.score:.0f}/100", "certification", verdict),
        ]

    def verdict_card(self):
        return self.cards()[4]
