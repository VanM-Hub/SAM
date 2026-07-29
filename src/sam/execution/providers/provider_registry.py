# OP-442 — Provider Registry
# Python 3.8, frozen DTO, synchronous

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Tuple
import uuid

from .provider_protocol import ExecutionProviderProtocol, ProviderMetadata, ProviderDescriptor


@dataclass(frozen=True)
class RegisteredProvider:
    entry_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    provider_id: str = ""
    provider_type: str = ""
    name: str = ""
    version: str = ""
    capability_names: Tuple[str, ...] = field(default_factory=tuple)
    healthy: bool = True
    priority: int = 0


@dataclass(frozen=True)
class ProviderStatistics:
    total: int = 0; healthy: int = 0; unhealthy: int = 0
    by_type: Dict[str, int] = field(default_factory=dict)


class ProviderRegistry:
    def __init__(self):
        self._providers: Dict[str, ExecutionProviderProtocol] = {}
        self._entries: Dict[str, RegisteredProvider] = {}
        self._by_type: Dict[str, List[str]] = {}

    def register(self, provider: ExecutionProviderProtocol, priority: int = 0) -> RegisteredProvider:
        meta = provider.metadata; pid = meta.provider_id
        if pid in self._providers:
            # Already registered — return existing entry
            old = self._find_entry(pid)
            if old: return old
        self._providers[pid] = provider
        caps = tuple(c.name for c in meta.capabilities)
        entry = RegisteredProvider(provider_id=pid, provider_type=meta.provider_type,
            name=meta.name, version=meta.version, capability_names=caps,
            healthy=meta.healthy, priority=priority)
        self._entries[entry.entry_id] = entry
        self._by_type.setdefault(meta.provider_type, []).append(entry.entry_id)
        return entry

    def unregister(self, provider_id: str) -> bool:
        e = self._find_entry(provider_id)
        if not e: return False
        self._remove_from_index(e)
        self._entries.pop(e.entry_id, None); self._providers.pop(provider_id, None); return True

    def _find_entry(self, pid: str) -> Optional[RegisteredProvider]:
        for e in self._entries.values():
            if e.provider_id == pid: return e
        return None

    def _remove_from_index(self, e: RegisteredProvider) -> None:
        lst = self._by_type.get(e.provider_type)
        if lst and e.entry_id in lst: lst.remove(e.entry_id)

    def find(self, pid: str) -> Optional[ExecutionProviderProtocol]: return self._providers.get(pid)
    def find_entry(self, pid: str) -> Optional[RegisteredProvider]: return self._find_entry(pid)
    def find_by_type(self, pt: str) -> Tuple[ExecutionProviderProtocol, ...]:
        result = []
        for eid in self._by_type.get(pt, []):
            e = self._entries.get(eid)
            if e and e.provider_id in self._providers:
                result.append(self._providers[e.provider_id])
        return tuple(result)
    def find_by_action(self, action: str) -> Tuple[ExecutionProviderProtocol, ...]:
        return tuple(p for p in self._providers.values() if action in p.supported_actions())
    def list(self) -> Tuple[RegisteredProvider, ...]:
        return tuple(sorted(self._entries.values(), key=lambda e: (-e.priority, e.name)))
    def get_statistics(self) -> ProviderStatistics:
        h=sum(1 for e in self._entries.values() if e.healthy); u=len(self._entries)-h
        bt:Dict[str,int]={}
        for e in self._entries.values(): bt[e.provider_type]=bt.get(e.provider_type,0)+1
        return ProviderStatistics(total=len(self._entries),healthy=h,unhealthy=u,by_type=bt)
    @property
    def count(self): return len(self._entries)
    def clear(self):
        self._providers.clear(); self._entries.clear(); self._by_type.clear()
