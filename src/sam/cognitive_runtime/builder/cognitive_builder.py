"""Cognitive Builder — builder DTO kognitif (Sprint 190).

Builder HANYA menyusun DTO. TIDAK boleh reasoning, scoring, inferensi.
Deterministik & preview-only.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List

from ..context.cognitive_context import CognitiveContext


@dataclass(frozen=True)
class CognitiveBuildResult:
    """Hasil build (immutable)."""
    ok: bool = True
    context: CognitiveContext = field(default_factory=CognitiveContext)
    detail: str = ""


class CognitiveBuilder:
    """Builder utama runtime kognitif. Deterministik."""

    def build_context(self, cognitive_id: str, scope: str = "mission") -> CognitiveBuildResult:
        return CognitiveBuildResult(
            ok=True,
            context=CognitiveContext(cognitive_id=cognitive_id, scope=scope),
            detail="built",
        )
