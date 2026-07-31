"""Tool Arguments — argumen tool generik (Sprint 245).

Program B — Model Runtime Integration.
Generic; tidak execute tool. Immutable, preview-only.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class ToolArguments:
    """Argumen tool (immutable). Representasi, tidak dieksekusi."""
    tool_id: str
    values: Dict[str, Any] = field(default_factory=dict)
    provided: List[str] = field(default_factory=list)
    missing: List[str] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {
            "tool_id": self.tool_id,
            "values": dict(self.values),
            "provided": list(self.provided),
            "missing": list(self.missing),
        }

    @property
    def complete(self) -> bool:
        return not self.missing
