"""Conversation Runtime Bridge — 5 read-only queries (Sprint 223)."""
from __future__ import annotations

from .artifact_runtime import ArtifactRuntime
from .artifact_pipeline import ArtifactPipeline
from .artifact_engine import ArtifactEngine
from .artifact_summary import ArtifactSummarizer
from .artifact_statistics import ArtifactCollector


class ConversationRuntimeBridge:
    """Bridge conversation — 5 query runtime artifact."""

    def __init__(self) -> None:
        self._runtime = ArtifactRuntime()
        self._pipeline = ArtifactPipeline(self._runtime)
        self._summarizer = ArtifactSummarizer()
        self._collector = ArtifactCollector()

    def query_1_run(self, name: str) -> dict:
        res = self._runtime.run(name, "report")
        return {"ok": res.ok, "external_calls": res.external_calls}

    def query_2_route(self):
        return self._pipeline.route()

    def query_3_engine(self) -> dict:
        info = ArtifactEngine().describe()
        return {"is_llm": info.is_llm, "is_ai": info.is_ai}

    def query_4_summary(self) -> dict:
        s = self._summarizer.summarize(("a", "b"), ("report", "report"))
        return {"total": s.total, "preview_only": s.preview_only}

    def query_5_statistics(self) -> dict:
        s = self._collector.collect(("report", "log"))
        return {"total": s.total, "external_calls": s.external_calls}
