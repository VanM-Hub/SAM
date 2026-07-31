"""LLM Capability — kapabilitas generik penyedia LLM (Sprint 229)."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Tuple

LLM_CAPABILITY_KEYS: Tuple[str, ...] = (
    "generate",
    "chat",
    "embed",
    "classify",
    "summarize",
    "translate",
    "extract",
    "tool_call",
)


@dataclass(frozen=True)
class LLMCapability:
    """Kapabilitas LLM generik (immutable)."""
    provider_id: str
    operation: str
    supported: bool = True
    mode: str = "preview"
    external_calls: int = 0


@dataclass(frozen=True)
class LLMCapabilitySet:
    """Set kapabilitas LLM (immutable)."""
    provider_id: str
    operations: Tuple[str, ...] = field(default_factory=tuple)

    def supports(self, operation: str) -> bool:
        return operation in self.operations

    @property
    def count(self) -> int:
        return len(self.operations)
