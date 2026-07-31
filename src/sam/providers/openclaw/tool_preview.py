"""OpenClaw Tool Preview — preview request tool tanpa invoke.

Sprint 149 — OpenClaw Provider.
Menghasilkan preview invoke tool (simulasi). Tidak memanggil tool.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List

from .tool_request import OpenClawToolRequest


@dataclass(frozen=True)
class OpenClawToolPreview:
    """Preview invoke tool (immutable)."""
    request_id: str
    tool: str
    preview: bool = True
    invoked: bool = False
    external_calls: int = 0
    arguments: Dict[str, object] = field(default_factory=dict)
    notes: List[str] = field(default_factory=list)


class OpenClawToolPreviewEngine:
    """Preview tool — external_calls selalu 0, tidak invoke."""

    def preview(self, request: OpenClawToolRequest) -> OpenClawToolPreview:
        return OpenClawToolPreview(
            request_id=request.request_id,
            tool=request.tool,
            preview=True,
            invoked=False,
            external_calls=0,
            arguments=dict(request.arguments),
            notes=["dry-run: tool not invoked"],
        )
