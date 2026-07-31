"""ArtifactEngine — engine representasi (bukan inferensi/AI)."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ArtifactEngineInfo:
    is_llm: bool = False
    is_ai: bool = False
    preview_only: bool = True
    no_storage: bool = True


class ArtifactEngine:
    """Engine representasi artifact. Bukan LLM, bukan AI, no inference."""

    def __init__(self) -> None:
        self.info = ArtifactEngineInfo()

    def describe(self) -> ArtifactEngineInfo:
        return self.info
