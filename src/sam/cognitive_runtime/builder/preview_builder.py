"""Preview Builder — membangun preview DTO kognitif (Sprint 190).

TIDAK boleh reasoning, scoring, inferensi, atau menyimpan apa pun.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List

from ..context.cognitive_context import CognitiveContext


@dataclass(frozen=True)
class CognitivePreviewDTO:
    """Preview kognitif (immutable)."""
    label: str = ""
    context: CognitiveContext = field(default_factory=CognitiveContext)
    composed: bool = True
    inferred: bool = False
    external_calls: int = 0

    def __post_init__(self) -> None:
        if self.inferred:
            raise ValueError("cognitive preview must not infer")
        if self.external_calls != 0:
            raise ValueError("cognitive preview must have 0 external calls")


class PreviewBuilder:
    """Builder preview. Menyusun preview DTO saja — tidak pernah infer."""

    def build(self, label: str, context: CognitiveContext) -> CognitivePreviewDTO:
        return CognitivePreviewDTO(label=label, context=context)
