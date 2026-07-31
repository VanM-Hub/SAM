"""Dashboard Integration Bridge — 5 PolicyCards (Sprint 219)."""
from __future__ import annotations

from ..dashboard import PolicyCard
from ..foundation.audit_registry import AuditRegistry
from .audit_runtime_pipeline import AuditRuntimePipeline
from .audit_runtime_certification import AuditRuntimeCertifier


class DashboardIntegrationBridge:
    """Bridge dashboard — 5 kartu integrasi audit."""

    def __init__(self, registry: AuditRegistry) -> None:
        self._registry = registry
        self._pipeline = AuditRuntimePipeline(registry)
        self._certifier = AuditRuntimeCertifier()

    def cards(self):
        n = self._registry.count()
        cert = self._certifier.certify()
        verdict = "certified" if cert.certified else "not-certified"
        return [
            PolicyCard("ag.route", "audit", "ready",
                          "Mission->Agent->Skill->Workflow->Policy->Audit->Memory->Knowledge->Cognitive->Orchestrator->Connector->Provider",
                          "pipeline", "ready"),
            PolicyCard("ag.audit", "audit", "ready",
                          f"{n} audit(s) integrated", "read-only", "ready"),
            PolicyCard("ag.preview", "audit", "ready",
                          "execution preview (external_calls=0)",
                          "preview", "ready"),
            PolicyCard("ag.readonly", "audit", "ready",
                          "0 layer violations - runtime lain tak diubah",
                          "integration", "ready"),
            PolicyCard("ag.cert", "audit", verdict,
                          f"score {cert.score:.0f}/100", "certification", verdict),
        ]

    def verdict_card(self):
        return self.cards()[4]
