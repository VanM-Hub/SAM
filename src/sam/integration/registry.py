# OP-402 — Integration Registry
# Python 3.8, frozen DTO, synchronous

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Tuple
import uuid

from .contracts import IntegrationProtocol, IntegrationDescriptor, IntegrationCapability


@dataclass(frozen=True)
class RegistryEntry:
    entry_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    integration_id: str = ""
    integration_type: str = ""
    name: str = ""; version: str = ""
    capability_names: Tuple[str, ...] = field(default_factory=tuple)
    healthy: bool = True
    priority: int = 0


@dataclass(frozen=True)
class RegistryStatistics:
    total: int = 0; healthy: int = 0; unhealthy: int = 0
    by_type: Dict[str, int] = field(default_factory=dict)


class IntegrationRegistry:
    def __init__(self):
        self._providers: Dict[str, IntegrationProtocol] = {}
        self._entries: Dict[str, RegistryEntry] = {}
        self._by_type: Dict[str, List[str]] = {}

    def register(self, provider: IntegrationProtocol, priority: int = 0) -> RegistryEntry:
        d = provider.descriptor; pid = d.integration_id
        if pid in self._providers:
            old = self._find_entry(pid)
            if old: return old
        self._providers[pid] = provider
        caps = d.capability_names if isinstance(d.capability_names, tuple) else tuple(d.capability_names)
        entry = RegistryEntry(integration_id=pid, integration_type=d.integration_type,
            name=d.name, version=d.version, capability_names=caps, healthy=d.healthy, priority=priority)
        self._entries[entry.entry_id] = entry
        self._by_type.setdefault(d.integration_type, []).append(entry.entry_id)
        return entry

    def unregister(self, integration_id: str) -> bool:
        e = self._find_entry(integration_id)
        if not e: return False
        lst = self._by_type.get(e.integration_type)
        if lst and e.entry_id in lst: lst.remove(e.entry_id)
        self._entries.pop(e.entry_id, None); self._providers.pop(integration_id, None); return True

    def _find_entry(self, pid: str) -> Optional[RegistryEntry]:
        for e in self._entries.values():
            if e.integration_id == pid: return e
        return None

    def find(self, pid: str) -> Optional[IntegrationProtocol]: return self._providers.get(pid)
    def find_entry(self, pid: str) -> Optional[RegistryEntry]: return self._find_entry(pid)
    def find_by_type(self, t: str) -> Tuple[IntegrationProtocol, ...]:
        return tuple(self._providers[e.integration_id] for eid in self._by_type.get(t,[])
                     if (e:=self._entries.get(eid)) and e.integration_id in self._providers)
    def find_by_action(self, action: str) -> Tuple[IntegrationProtocol, ...]:
        return tuple(p for p in self._providers.values() if action in p.supported_actions())
    def list(self) -> Tuple[RegistryEntry, ...]:
        return tuple(sorted(self._entries.values(), key=lambda e: (-e.priority, e.name)))
    def get_statistics(self) -> RegistryStatistics:
        h = sum(1 for e in self._entries.values() if e.healthy)
        u = len(self._entries)-h; bt: Dict[str,int] = {}
        for e in self._entries.values(): bt[e.integration_type] = bt.get(e.integration_type, 0)+1
        return RegistryStatistics(total=len(self._entries), healthy=h, unhealthy=u, by_type=bt)
    @property
    def count(self): return len(self._entries)
    def clear(self): self._providers.clear(); self._entries.clear(); self._by_type.clear()
