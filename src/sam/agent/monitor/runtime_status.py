"""Runtime Status — status runtime (Sprint 161).

Agent Runtime — status runtime read-only.
"""
from __future__ import annotations
from dataclasses import dataclass, field

from ..coordinator.runtime_registry import RuntimeRegistry


@dataclass(frozen=True)
class RuntimeStatus:
    """Status runtime (immutable)."""
    runtime_name: str
    available: bool = True
    preview_only: bool = True


class RuntimeStatusView:
    """Pandangan status runtime. Read-only."""

    def __init__(self, registry: RuntimeRegistry) -> None:
        self._registry = registry

    def status(self, name: str) -> RuntimeStatus:
        entry = self._registry.get(name)
        if entry is None:
            return RuntimeStatus(runtime_name=name, available=False)
        return RuntimeStatus(
            runtime_name=name,
            available=entry.available,
            preview_only=entry.preview_only,
        )

    def all_status(self):
        return [self.status(n) for n in self._registry.names()]
