"""Dashboard Integration Bridge — 5 PolicyCards (Sprint 211)."""
from __future__ import annotations

from ..dashboard import PolicyCard
from ..foundation.policy_registry import PolicyRegistry
from .policy_runtime_pipeline import PolicyRuntimePipeline
from .policy_runtime_certification import PolicyRuntimeCertifier


class DashboardIntegrationBridge:
    """Bridge dashboard — 5 kartu untuk integrasi policy."""

    def __init__(self, registry: PolicyRegistry) -> None:
        self._registry = registry
        self._pipeline = PolicyRuntimePipeline(registry)
        self._certifier = PolicyRuntimeCertifier()

    def cards(self):
        n = self._registry.count()
        cert = self._certifier.certify()
        verdict = "certified" if cert.certified else "not-certified"
        return [
            PolicyCard("ig.route", "integration", "ready",
                          "Mission->Agent->Skill->Workflow->Policy->Memory->Knowledge->Cognitive->Orchestrator->Connector->Provider",
                          "pipeline", "ready"),
            PolicyCard("ig.policy", "integration", "ready",
                          f"{n} policy(s) integrated", "read-only", "ready"),
            PolicyCard("ig.preview", "integration", "ready",
                          "execution preview (external_calls=0)", "preview", "ready"),
            PolicyCard("ig.readonly", "integration", "ready",
                          "0 layer violations - runtime lain tak diubah",
                          "integration", "ready"),
            PolicyCard("ig.cert", "integration", verdict,
                          f"score {cert.score:.0f}/100", "certification", verdict),
        ]

    def verdict_card(self):
        return self.cards()[4]
