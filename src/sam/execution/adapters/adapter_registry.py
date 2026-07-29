# OP-433 — Adapter Registry
# Python 3.8, frozen DTO, synchronous

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple
import uuid

from .adapter_protocol import ExecutionAdapterProtocol, AdapterMetadata, AdapterCapability


@dataclass(frozen=True)
class RegisteredAdapter:
    entry_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    adapter_id: str = ""
    adapter_type: str = ""
    name: str = ""
    version: str = ""
    capability_names: Tuple[str, ...] = field(default_factory=tuple)
    healthy: bool = True
    priority: int = 0
    registered_at: datetime = field(default_factory=datetime.utcnow)


@dataclass(frozen=True)
class AdapterStatistics:
    total: int = 0
    healthy: int = 0
    unhealthy: int = 0
    by_type: Dict[str, int] = field(default_factory=dict)


class AdapterRegistry:
    """Registry for execution adapters."""

    def __init__(self):
        self._adapters: Dict[str, ExecutionAdapterProtocol] = {}
        self._entries: Dict[str, RegisteredAdapter] = {}
        self._by_type: Dict[str, List[str]] = {}

    def register(self, adapter: ExecutionAdapterProtocol,
                 priority: int = 0) -> RegisteredAdapter:
        meta = adapter.metadata
        aid = meta.adapter_id

        if aid in self._adapters:
            # Update existing
            old = self._find_entry(aid)
            if old:
                self._remove_from_type_index(old)

        self._adapters[aid] = adapter
        caps = tuple(c.name for c in meta.capabilities)
        entry = RegisteredAdapter(
            adapter_id=aid, adapter_type=meta.adapter_type,
            name=meta.name, version=meta.version,
            capability_names=caps, healthy=meta.healthy,
            priority=priority,
        )
        self._entries[entry.entry_id] = entry
        self._by_type.setdefault(meta.adapter_type, []).append(entry.entry_id)
        return entry

    def unregister(self, adapter_id: str) -> bool:
        entry = self._find_entry(adapter_id)
        if entry is None:
            return False
        self._remove_from_type_index(entry)
        self._entries.pop(entry.entry_id, None)
        self._adapters.pop(adapter_id, None)
        return True

    def _find_entry(self, adapter_id: str) -> Optional[RegisteredAdapter]:
        for e in self._entries.values():
            if e.adapter_id == adapter_id:
                return e
        return None

    def _remove_from_type_index(self, entry: RegisteredAdapter) -> None:
        lst = self._by_type.get(entry.adapter_type)
        if lst and entry.entry_id in lst:
            lst.remove(entry.entry_id)

    def find(self, adapter_id: str) -> Optional[ExecutionAdapterProtocol]:
        return self._adapters.get(adapter_id)

    def find_entry(self, adapter_id: str) -> Optional[RegisteredAdapter]:
        return self._find_entry(adapter_id)

    def find_by_type(self, adapter_type: str) -> Tuple[ExecutionAdapterProtocol, ...]:
        result: List[ExecutionAdapterProtocol] = []
        for eid in self._by_type.get(adapter_type, []):
            entry = self._entries.get(eid)
            if entry and entry.adapter_id in self._adapters:
                result.append(self._adapters[entry.adapter_id])
        return tuple(result)

    def find_by_capability(self, action: str) -> Tuple[ExecutionAdapterProtocol, ...]:
        result: List[ExecutionAdapterProtocol] = []
        for adapter in self._adapters.values():
            if action in adapter.supported_actions():
                result.append(adapter)
        return tuple(result)

    def list(self) -> Tuple[RegisteredAdapter, ...]:
        return tuple(sorted(
            self._entries.values(),
            key=lambda e: (-e.priority, e.name),
        ))

    def get_statistics(self) -> AdapterStatistics:
        entries = self._entries.values()
        healthy = sum(1 for e in entries if e.healthy)
        unhealthy = len(self._entries) - healthy
        by_type: Dict[str, int] = {}
        for e in self._entries.values():
            by_type[e.adapter_type] = by_type.get(e.adapter_type, 0) + 1
        return AdapterStatistics(
            total=len(self._entries), healthy=healthy, unhealthy=unhealthy,
            by_type=by_type,
        )

    @property
    def count(self) -> int:
        return len(self._entries)

    def clear(self) -> None:
        self._adapters.clear()
        self._entries.clear()
        self._by_type.clear()


class AdapterSelector:
    """Selects optimal adapter for an envelope."""

    @staticmethod
    def select(
        registry: AdapterRegistry,
        adapter_type: Optional[str] = None,
        action: Optional[str] = None,
    ) -> Optional[ExecutionAdapterProtocol]:
        candidates: List[ExecutionAdapterProtocol] = []

        if adapter_type:
            candidates = list(registry.find_by_type(adapter_type))
        elif action:
            candidates = list(registry.find_by_capability(action))
        else:
            candidates = list(registry._adapters.values())

        # Filter healthy
        candidates = [c for c in candidates if c.health().healthy]
        return candidates[0] if candidates else None
