"""Knowledge Engine — engine runtime knowledge (Sprint 183).

Preview-only, deterministic, tanpa inferensi.
"""
from __future__ import annotations
from dataclasses import dataclass

from .knowledge_runtime import KnowledgeRuntime, KnowledgeRunResult


@dataclass(frozen=True)
class KnowledgeEngineInfo:
    """Info engine knowledge (immutable)."""
    version: str
    preview_only: bool = True
    deterministic: bool = True
    inference: bool = False


class KnowledgeEngine:
    """Engine knowledge. Preview-only facade."""

    VERSION = "1.0.0"

    def __init__(self, runtime: KnowledgeRuntime) -> None:
        self._runtime = runtime

    def info(self) -> KnowledgeEngineInfo:
        return KnowledgeEngineInfo(version=self.VERSION)

    def run(self, knowledge_id: str) -> KnowledgeRunResult:
        return self._runtime.run(knowledge_id)

    def health(self) -> bool:
        return True
