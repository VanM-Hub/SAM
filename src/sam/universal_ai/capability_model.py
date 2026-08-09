"""AI Capability Model - WP-05 (MISSION-5.1 / IP-5.1-001).

Model capability AI declarative, dapat digunakan oleh capability resolution.
Tidak mengandung provider-specific execution logic.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Tuple


class AICapabilityKind(str, Enum):
    """Jenis kemampuan AI yang dapat dideklarasikan."""

    TEXT_GENERATION = "text_generation"
    STRUCTURED_OUTPUT = "structured_output"
    VISION = "vision"
    EMBEDDING = "embedding"
    TOOL_CALLING = "tool_calling"
    CONTEXT_HANDLING = "context_handling"


@dataclass(frozen=True)
class AICapability:
    """Satu deklarasi capability AI."""

    kind: AICapabilityKind
    name: str = ""
    detail: Tuple[Tuple[str, str], ...] = field(default_factory=tuple)

    def as_dict(self) -> dict:
        return {
            "kind": self.kind.value,
            "name": self.name or self.kind.value,
            "detail": dict(self.detail),
        }


class AICapabilityModel:
    """Kumpulan capability yang dimiliki sebuah entitas AI."""

    def __init__(self, capabilities: Tuple[AICapability, ...] = ()) -> None:
        self._capabilities = tuple(capabilities)

    def has(self, kind: AICapabilityKind) -> bool:
        return any(c.kind == kind for c in self._capabilities)

    def capabilities(self) -> Tuple[AICapability, ...]:
        return self._capabilities

    def kinds(self) -> Tuple[AICapabilityKind, ...]:
        return tuple(c.kind for c in self._capabilities)

    def describe(self) -> Tuple[str, ...]:
        return tuple(c.name or c.kind.value for c in self._capabilities)

    def as_list(self) -> list:
        return [c.as_dict() for c in self._capabilities]
