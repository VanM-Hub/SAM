"""Operational Context - WP-33 (MISSION-5.1 / IP-5.1-004).

Context kondisi operasional SAM sebagai snapshot untuk reasoning request.
Reasoning tidak boleh memodifikasi operational state.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Tuple


@dataclass(frozen=True)
class OperationalContext:
    """Snapshot kondisi operasional SAM (read-only untuk reasoning)."""

    runtime_state: Tuple[Tuple[str, str], ...] = field(default_factory=tuple)
    provider_state: Tuple[Tuple[str, str], ...] = field(default_factory=tuple)
    workflow_state: Tuple[Tuple[str, str], ...] = field(default_factory=tuple)
    execution_state: Tuple[Tuple[str, str], ...] = field(default_factory=tuple)
    investigation_state: Tuple[Tuple[str, str], ...] = field(default_factory=tuple)
    readiness: str = ""
    failure_info: Tuple[Tuple[str, str], ...] = field(default_factory=tuple)

    def as_dict(self) -> dict:
        return {
            "runtime_state": dict(self.runtime_state),
            "provider_state": dict(self.provider_state),
            "workflow_state": dict(self.workflow_state),
            "execution_state": dict(self.execution_state),
            "investigation_state": dict(self.investigation_state),
            "readiness": self.readiness,
            "failure_info": dict(self.failure_info),
        }


class OperationalContextProvider:
    """Menyusun snapshot operational context."""

    def snapshot(self, **states: Tuple[Tuple[str, str], ...]) -> OperationalContext:
        fields = {k: v for k, v in states.items()}
        return OperationalContext(
            runtime_state=fields.get("runtime_state", ()),
            provider_state=fields.get("provider_state", ()),
            workflow_state=fields.get("workflow_state", ()),
            execution_state=fields.get("execution_state", ()),
            investigation_state=fields.get("investigation_state", ()),
            readiness=fields.get("readiness", ""),
            failure_info=fields.get("failure_info", ()),
        )
