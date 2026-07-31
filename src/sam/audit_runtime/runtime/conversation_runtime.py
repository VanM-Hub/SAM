"""Conversation Runtime Bridge — 5 query read-only (Sprint 215)."""
from __future__ import annotations

from ..foundation.audit_registry import AuditRegistry
from .audit_runtime import AuditRuntime
from .audit_pipeline import AuditPipeline
from .audit_summary import AuditSummarizer
from .audit_statistics import AuditStatisticsCollector


class ConversationRuntimeBridge:
    """Bridge conversation — 5 query read-only runtime audit."""

    def __init__(self, registry: AuditRegistry) -> None:
        self._registry = registry

    def query_1_run(self, audit_id: str) -> dict:
        """Query 1 — jalankan audit (preview read-only)."""
        r = AuditRuntime().run(self._registry, audit_id)
        return {"ok": r.ok, "external_calls": r.external_calls}

    def query_2_pipeline(self, audit_id: str) -> dict:
        """Query 2 — jalankan pipeline."""
        p = AuditPipeline().run(self._registry, audit_id)
        return {"ok": p.ok, "stages": len(p.stages)}

    def query_3_summary(self) -> dict:
        """Query 3 — ringkasan."""
        s = AuditSummarizer().summarize(self._registry)
        return {"total": s.total, "categories": list(s.categories)}

    def query_4_statistics(self) -> dict:
        """Query 4 — statistik."""
        st = AuditStatisticsCollector().collect(self._registry)
        return {"total": st.total, "per_category": st.per_category}

    def query_5_capabilities(self) -> dict:
        """Query 5 — kapabilitas runtime."""
        return AuditRuntime.capabilities()
