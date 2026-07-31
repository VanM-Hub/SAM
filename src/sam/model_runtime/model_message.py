"""Model Message — pesan generik model (Sprint 240).

Program B — Model Runtime Integration.
Generik, tidak mengenal provider. Immutable, preview-only.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class ModelMessage:
    """Satu pesan generik (immutable). role: system|user|assistant|tool."""
    role: str = "user"
    content: str = ""
    tool_call_id: Optional[str] = None
    tool_calls: List[Dict[str, Any]] = field(default_factory=list)
    name: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.role not in ("system", "user", "assistant", "tool"):
            raise ValueError(f"invalid role: {self.role}")

    def as_dict(self) -> dict:
        return {
            "role": self.role,
            "content": self.content,
            "tool_call_id": self.tool_call_id,
            "tool_calls": [dict(tc) for tc in self.tool_calls],
            "name": self.name,
            "metadata": dict(self.metadata),
        }
