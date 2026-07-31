"""Tool Call — pemanggilan tool generik (Sprint 245).

Program B — Model Runtime Integration.
Generic; tidak execute tool. Immutable, preview-only.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict

from .tool_descriptor import ToolDescriptor


@dataclass(frozen=True)
class ToolCall:
    """Satu pemanggilan tool (immutable). Tidak dieksekusi."""
    call_id: str
    tool: ToolDescriptor
    arguments: Dict[str, object] = field(default_factory=dict)
    preview_only: bool = True
    external_calls: int = 0

    def as_dict(self) -> dict:
        return {
            "call_id": self.call_id,
            "tool": self.tool.as_dict(),
            "arguments": dict(self.arguments),
            "preview_only": self.preview_only,
            "external_calls": self.external_calls,
        }
