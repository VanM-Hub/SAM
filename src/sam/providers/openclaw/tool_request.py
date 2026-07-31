"""OpenClaw Tool Request — frozen DTO request tool (preview).

Sprint 149 — OpenClaw Provider.
Representasi request tool tanpa invoke.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict


@dataclass(frozen=True)
class OpenClawToolRequest:
    """Request tool OpenClaw (immutable, preview-only)."""
    request_id: str
    tool: str
    arguments: Dict[str, object] = field(default_factory=dict)

    def is_valid(self) -> bool:
        return bool(self.request_id) and bool(self.tool)
