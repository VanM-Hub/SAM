"""Cognitive Runtime — engine utama runtime kognitif (Sprint 191)."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict

from ..context.cognitive_context import CognitiveContext
from ..foundation.cognitive_registry import CognitiveRegistry


@dataclass(frozen=True)
class CognitiveRunResult:
    """Hasil run runtime kognitif (immutable)."""
    ok: bool = True
    cognitive_id: str = ""
    context: CognitiveContext = field(default_factory=CognitiveContext)
    external_calls: int = 0
    inferred: bool = False


class CognitiveRuntime:
    """Runtime kognitif. Deterministik, preview-only, tanpa inferensi."""

    def __init__(self, registry: CognitiveRegistry) -> None:
        self._registry = registry

    def run(self, cognitive_id: str) -> CognitiveRunResult:
        if not self._registry.exists(cognitive_id):
            return CognitiveRunResult(
                ok=False, cognitive_id=cognitive_id, external_calls=0,
            )
        return CognitiveRunResult(
            ok=True, cognitive_id=cognitive_id,
            context=CognitiveContext(cognitive_id=cognitive_id),
            external_calls=0, inferred=False,
        )

    def engine_info(self) -> dict:
        return {
            "runtime": "cognitive_runtime",
            "no_inference": True,
            "preview_only": True,
        }
