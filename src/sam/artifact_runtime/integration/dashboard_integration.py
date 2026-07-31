"""Dashboard Integration Bridge — 5 Artifact Cards (Sprint 227)."""
from __future__ import annotations

from ..dashboard import PolicyCard
from ..foundation.artifact_registry import ArtifactRegistry
from .artifact_runtime_pipeline import ArtifactRuntimePipeline
from .artifact_runtime_summary import ArtifactRuntimeSummarizer


class DashboardIntegrationBridge:
    """Bridge dashboard — 5 kartu integrasi artifact."""

    def __init__(self, registry: ArtifactRegistry) -> None:
        self._registry = registry
        self._pipeline = ArtifactRuntimePipeline(registry)
        self._summarizer = ArtifactRuntimeSummarizer()

    def cards(self):
        n = self._registry.count()
        s = self._summarizer.summarize()
        return [
            PolicyCard("ag.route", "artifact", "ready",
                       "Mission->Agent->Skill->Workflow->Policy->Audit->Artifact->Memory->Knowledge->Cognitive->Orchestrator->Connector->Provider",
                       "pipeline", "ready"),
            PolicyCard("ag.artifact", "artifact", "ready",
                       f"{n} artifact(s) integrated", "read-only", "ready"),
            PolicyCard("ag.container", "artifact", "ready",
                       f"artifact stage index {s.container_index}",
                       "stage", "ready"),
            PolicyCard("ag.preview", "artifact", "ready",
                       "no storage / no publish (external_calls=0)",
                       "preview", "ready"),
            PolicyCard("ag.readonly", "artifact", "ready",
                       "0 layer violations - runtime lain tak diubah",
                       "integration", "ready"),
        ]
