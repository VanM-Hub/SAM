"""Conversation Integration Bridge — 5 query read-only (Sprint 171)."""
from __future__ import annotations

from ..foundation.skill_registry import SkillRegistry
from .skill_runtime_pipeline import SkillRuntimePipeline, INTEGRATION_ROUTE
from .skill_runtime_report import SkillRuntimeReporter
from .skill_runtime_certification import SkillRuntimeCertifier


class ConversationIntegrationBridge:
    """Bridge conversation — 5 query read-only integrasi skill."""

    def __init__(self, registry: SkillRegistry) -> None:
        self._registry = registry
        self._pipeline = SkillRuntimePipeline(registry)
        self._reporter = SkillRuntimeReporter(registry)
        self._certifier = SkillRuntimeCertifier()

    def query_1_route(self) -> list:
        """Query 1 — rute pipeline integrasi."""
        return self._pipeline.route()

    def query_2_status(self) -> dict:
        """Query 2 — status registry."""
        return {"total_skills": self._registry.count()}

    def query_3_pipeline(self, skill_id: str) -> dict:
        """Query 3 — jalankan pipeline preview (read-only)."""
        run = self._pipeline.run(skill_id)
        return {"ok": run.ok, "external_calls": run.external_calls}

    def query_4_report(self) -> dict:
        """Query 4 — laporan runtime."""
        rep = self._reporter.report()
        return {"total": rep.total_skills, "ready": rep.ready}

    def query_5_certification(self) -> dict:
        """Query 5 — status sertifikasi."""
        c = self._certifier.certify()
        return {"certified": c.certified, "score": c.score}
