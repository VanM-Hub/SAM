"""OpenClaw Tool Registry — daftar tool (read-only, preview).

Sprint 149 — OpenClaw Provider.
Registrasi tool yang boleh di-preview. Tidak invoke.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List


@dataclass(frozen=True)
class ToolDefinition:
    """Deskripsi tool (immutable)."""
    name: str
    description: str = ""
    preview_only: bool = True


class OpenClawToolRegistry:
    """Registry tool OpenClaw — read-only query, tidak invoke."""

    def __init__(self) -> None:
        self._tools: Dict[str, ToolDefinition] = {}

    def add(self, tool: ToolDefinition) -> bool:
        if tool.name in self._tools:
            return False
        self._tools[tool.name] = tool
        return True

    def get(self, name: str) -> ToolDefinition:
        return self._tools.get(name)

    def names(self) -> List[str]:
        return list(self._tools.keys())

    def count(self) -> int:
        return len(self._tools)

    def has(self, name: str) -> bool:
        return name in self._tools
