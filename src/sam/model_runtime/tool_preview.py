"""Tool Preview — preview tool deterministik (Sprint 245).

Program B — Model Runtime Integration.
Generic; tidak execute tool. Preview-only, external_calls=0.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List

from .tool_descriptor import ToolDescriptor
from .tool_arguments import ToolArguments
from .tool_call import ToolCall


@dataclass(frozen=True)
class ToolPreview:
    """Preview tool (immutable). Tidak dieksekusi."""
    preview_id: str
    calls: List[ToolCall] = field(default_factory=list)
    would_execute: bool = False
    note: str = "preview only - tools not executed"
    external_calls: int = 0

    def as_dict(self) -> dict:
        return {
            "preview_id": self.preview_id,
            "calls": [c.as_dict() for c in self.calls],
            "would_execute": self.would_execute,
            "note": self.note,
            "external_calls": self.external_calls,
        }


class ToolPreviewEngine:
    """Preview tool. Menyiapkan representasi panggilan, tanpa eksekusi."""

    def preview(self, tool: ToolDescriptor, arguments: dict) -> ToolPreview:
        call = ToolCall(
            call_id=f"call-{tool.tool_id}",
            tool=tool,
            arguments=dict(arguments),
            preview_only=True,
            external_calls=0,
        )
        return ToolPreview(
            preview_id="pv-tool",
            calls=[call],
            would_execute=False,
            note="preview only - tools not executed",
            external_calls=0,
        )

    def build_arguments(self, tool: ToolDescriptor, values: dict) -> ToolArguments:
        provided = [k for k in values if k in tool.parameters_schema or True]
        missing = [r for r in tool.required if r not in values]
        return ToolArguments(
            tool_id=tool.tool_id,
            values=dict(values),
            provided=list(provided),
            missing=list(missing),
        )
