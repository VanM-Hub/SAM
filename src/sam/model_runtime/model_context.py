"""Model Context — konteks generik model (Sprint 240).

Program B — Model Runtime Integration.
Generik, tidak mengenal provider. Immutable, preview-only.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List

from .model_message import ModelMessage


@dataclass(frozen=True)
class ModelContext:
    """Konteks generik model (immutable)."""
    messages: List[ModelMessage] = field(default_factory=list)
    system: str = ""
    variables: Dict[str, Any] = field(default_factory=dict)
    max_turns: int = 10

    def as_dict(self) -> dict:
        return {
            "messages": [m.as_dict() for m in self.messages],
            "system": self.system,
            "variables": dict(self.variables),
            "max_turns": self.max_turns,
        }

    def with_message(self, message: ModelMessage) -> "ModelContext":
        return ModelContext(
            messages=list(self.messages) + [message],
            system=self.system,
            variables=dict(self.variables),
            max_turns=self.max_turns,
        )
