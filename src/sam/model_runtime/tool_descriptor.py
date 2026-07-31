"""Tool Descriptor — deskripsi tool generik (Sprint 245).

Program B — Model Runtime Integration.
Generic; tidak execute tool. Immutable, preview-only.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass(frozen=True)
class ToolDescriptor:
    """Deskripsi tool generik (immutable). Tidak mengeksekusi tool."""
    tool_id: str
    name: str
    description: str = ""
    parameters_schema: Dict[str, object] = field(default_factory=dict)
    required: List[str] = field(default_factory=list)
    preview_only: bool = True
    external_calls: int = 0

    def as_dict(self) -> dict:
        return {
            "tool_id": self.tool_id,
            "name": self.name,
            "description": self.description,
            "parameters_schema": dict(self.parameters_schema),
            "required": list(self.required),
            "preview_only": self.preview_only,
            "external_calls": self.external_calls,
        }
