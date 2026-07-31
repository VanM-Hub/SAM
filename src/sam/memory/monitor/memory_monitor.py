"""Memory Monitor — monitor memori (Sprint 177).

Phase XVII — Memory Runtime.
Read-only, deterministic.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List

from ..foundation.memory_registry import MemoryRegistry
from ..catalog.memory_version import MemoryVersionProvider


@dataclass(frozen=True)
class MemoryStatus:
    """Status memori (immutable)."""
    memory_id: str
    registered: bool = False
    has_capability: bool = False
    has_contract: bool = False
    version: str = ""
    healthy: bool = False


class MemoryMonitor:
    """Monitor memori. Read-only."""

    def __init__(self, registry: MemoryRegistry) -> None:
        self._registry = registry
        self._version = MemoryVersionProvider(registry)

    def status(self, memory_id: str) -> MemoryStatus:
        registered = self._registry.exists(memory_id)
        has_cap = bool(self._registry.get_capabilities(memory_id))
        has_contract = self._registry.get_contract(memory_id) is not None
        version = self._version.version_of(memory_id)
        healthy = registered and has_cap
        return MemoryStatus(
            memory_id=memory_id, registered=registered,
            has_capability=has_cap, has_contract=has_contract,
            version=version, healthy=healthy,
        )

    def all_status(self) -> List[MemoryStatus]:
        return [self.status(mid) for mid in self._registry.list_ids()]

    def healthy_count(self) -> int:
        return sum(1 for s in self.all_status() if s.healthy)
