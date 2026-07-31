"""Knowledge Health — kesehatan knowledge (Sprint 185).

Phase XVIII — Knowledge Runtime.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List

from ..foundation.knowledge_registry import KnowledgeRegistry
from .knowledge_monitor import KnowledgeMonitor


@dataclass(frozen=True)
class KnowledgeHealth:
    """Kesehatan knowledge (immutable)."""
    healthy: bool = True
    total: int = 0
    healthy_knowledge: int = 0
    issues: List[str] = field(default_factory=list)


class KnowledgeHealthCheck:
    """Health check knowledge. Read-only."""

    def __init__(self, registry: KnowledgeRegistry) -> None:
        self._registry = registry
        self._monitor = KnowledgeMonitor(registry)

    def check(self) -> KnowledgeHealth:
        statuses = self._monitor.all_status()
        healthy = sum(1 for s in statuses if s.healthy)
        issues = [f"{s.knowledge_id} unregistered" for s in statuses if not s.registered]
        return KnowledgeHealth(
            healthy=len(issues) == 0,
            total=len(statuses),
            healthy_knowledge=healthy,
            issues=issues,
        )
