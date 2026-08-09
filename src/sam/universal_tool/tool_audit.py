"""Tool Execution Audit & Explainability - WP-27/WP-28 (MISSION-5.2 / IP-5.2-003).

Audit trail execution Tool dan explainability hasil Tool.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Tuple

from .governed_tool_invocation import ToolExecutionContext
from .tool_response import ToolResponse


def _now_utc() -> str:
    return datetime.utcnow().isoformat() + "Z"


@dataclass(frozen=True)
class ToolAuditEntry:
    """Satu entri audit execution tool."""

    audit_id: str
    request_id: str
    tool_id: str
    executed: bool
    approved: bool
    controller: str = "governance"
    at: str = field(default_factory=_now_utc)

    def as_dict(self) -> dict:
        return {
            "audit_id": self.audit_id,
            "request_id": self.request_id,
            "tool_id": self.tool_id,
            "executed": self.executed,
            "approved": self.approved,
            "controller": self.controller,
            "at": self.at,
        }


class ToolAuditLog:
    """Audit trail execution tool (append-only)."""

    def __init__(self) -> None:
        self._entries: list = []

    def record(self, context: ToolExecutionContext) -> ToolAuditEntry:
        entry = ToolAuditEntry(
            audit_id=_gen(),
            request_id=context.request_id,
            tool_id=context.tool_id,
            executed=context.all_passed,
            approved=context.approved,
        )
        self._entries.append(entry)
        return entry

    def entries(self) -> Tuple[ToolAuditEntry, ...]:
        return tuple(self._entries)

    def for_tool(self, tool_id: str) -> Tuple[ToolAuditEntry, ...]:
        return tuple(e for e in self._entries if e.tool_id == tool_id)


class ToolExplainer:
    """Membangun penjelasan hasil Tool (evidence lineage)."""

    def explain(self, context: ToolExecutionContext, response: Optional[ToolResponse] = None) -> dict:
        return {
            "tool_id": context.tool_id,
            "request_id": context.request_id,
            "governance_path": [d.stage.value for d in context.decisions],
            "governed": context.all_passed,
            "response": response.as_dict() if response else None,
        }


def _gen() -> str:
    import uuid

    return uuid.uuid4().hex
