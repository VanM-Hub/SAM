"""Tool Connection Status, Operational Context, Investigation & History - WP-33..37.

Workspace presentation layer: status koneksi, context operasional, investigasi,
history execution, result explorer.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Tuple

from .connection_management import ConnectionManager
from .tool_audit import ToolAuditEntry, ToolAuditLog
from .tool_health import ToolHealth, ToolHealthCheck


@dataclass(frozen=True)
class ToolConnectionStatus:
    """Status koneksi tool (dari connector records)."""

    connector_id: str
    connected: bool
    state: str = ""

    def as_dict(self) -> dict:
        return {"connector_id": self.connector_id, "connected": self.connected, "state": self.state}


class ToolConnectionStatusView:
    """Menyajikan status koneksi seluruh connector."""

    def __init__(self, connections: ConnectionManager) -> None:
        self._connections = connections

    def all(self) -> Tuple[ToolConnectionStatus, ...]:
        return tuple(
            ToolConnectionStatus(connector_id=cid, connected=r.connected, state=r.state.value)
            for cid, r in self._connections._records.items()
        )


@dataclass(frozen=True)
class ToolOperationalContext:
    """Context operasional tool (snapshot)."""

    tool_id: str
    health: Optional[ToolHealth]
    connection_state: str = ""

    def as_dict(self) -> dict:
        return {
            "tool_id": self.tool_id,
            "health": self.health.as_dict() if self.health else None,
            "connection_state": self.connection_state,
        }


@dataclass(frozen=True)
class ToolInvestigation:
    """Hasil investigasi sederhana tool."""

    tool_id: str
    summary: str
    findings: Tuple[str, ...] = field(default_factory=tuple)

    def as_dict(self) -> dict:
        return {"tool_id": self.tool_id, "summary": self.summary, "findings": list(self.findings)}


class ToolWorkspace:
    """Fasilitas presentasi Operational Tool Workspace (read-only)."""

    def __init__(
        self,
        audit: Optional[ToolAuditLog] = None,
        health: Optional[ToolHealthCheck] = None,
    ) -> None:
        self.audit = audit or ToolAuditLog()
        self._health = health or ToolHealthCheck()

    def execution_history(self, tool_id: str) -> Tuple[ToolAuditEntry, ...]:
        return self.audit.for_tool(tool_id)

    def investigate(self, tool_id: str) -> ToolInvestigation:
        entries = self.audit.for_tool(tool_id)
        executed = sum(1 for e in entries if e.executed)
        return ToolInvestigation(
            tool_id=tool_id,
            summary=f"{len(entries)} execution records, {executed} executed",
            findings=(f"executed={executed}", f"total={len(entries)}"),
        )

    def operational_context(self, tool_id: str) -> ToolOperationalContext:
        return ToolOperationalContext(tool_id=tool_id, health=self._health.assess(tool_id))
