"""Runtime Health — kesehatan runtime (Sprint 161).

Agent Runtime — health check read-only, deterministik.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List

from ..coordinator.runtime_registry import RuntimeRegistry


@dataclass(frozen=True)
class RuntimeHealth:
    """Kesehatan runtime (immutable)."""
    healthy: bool = True
    total: int = 0
    available: int = 0
    issues: List[str] = field(default_factory=list)


class RuntimeHealthCheck:
    """Health check runtime. Read-only."""

    def __init__(self, registry: RuntimeRegistry) -> None:
        self._registry = registry

    def check(self) -> RuntimeHealth:
        entries = [self._registry.get(n) for n in self._registry.names()]
        entries = [e for e in entries if e is not None]
        available = sum(1 for e in entries if e.available)
        issues = []
        for e in entries:
            if not e.available:
                issues.append(f"{e.name} unavailable")
        return RuntimeHealth(
            healthy=len(issues) == 0,
            total=len(entries),
            available=available,
            issues=issues,
        )
