# OP-412 — Plugin Registry
# Python 3.8, frozen DTO, synchronous

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Tuple
import uuid

from .plugin_protocol import PluginProtocol, PluginDescriptor, PluginCapability


@dataclass(frozen=True)
class PluginEntry:
    entry_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    plugin_id: str = ""; name: str = ""; version: str = ""
    capability_names: Tuple[str, ...] = field(default_factory=tuple)
    healthy: bool = True; enabled: bool = True
    dependencies: Tuple[str, ...] = field(default_factory=tuple)
    priority: int = 0


@dataclass(frozen=True)
class PluginStatistics:
    total: int = 0; enabled: int = 0; disabled: int = 0; healthy: int = 0; unhealthy: int = 0


class PluginRegistry:
    def __init__(self):
        self._plugins: Dict[str, PluginProtocol] = {}
        self._entries: Dict[str, PluginEntry] = {}
        self._by_capability: Dict[str, List[str]] = {}

    def register(self, plugin: PluginProtocol) -> PluginEntry:
        d = plugin.descriptor; pid = d.plugin_id
        old = self._find_entry(pid)
        if old: self._remove_entry(old)
        self._plugins[pid] = plugin
        caps = tuple(c.name for c in d.capabilities)
        entry = PluginEntry(plugin_id=pid, name=d.name, version=d.version,
            capability_names=caps, healthy=d.healthy, enabled=d.enabled,
            dependencies=d.dependencies)
        self._entries[entry.entry_id] = entry
        for c in caps: self._by_capability.setdefault(c, []).append(entry.entry_id)
        return entry

    def unregister(self, plugin_id: str) -> bool:
        e = self._find_entry(plugin_id)
        if not e: return False
        self._remove_entry(e); self._plugins.pop(plugin_id, None); return True

    def _find_entry(self, pid: str) -> Optional[PluginEntry]:
        for e in self._entries.values():
            if e.plugin_id == pid: return e
        return None

    def _remove_entry(self, e: PluginEntry) -> None:
        self._entries.pop(e.entry_id, None)
        for caps in self._by_capability.values():
            if e.entry_id in caps: caps.remove(e.entry_id)

    def find(self, pid: str) -> Optional[PluginProtocol]: return self._plugins.get(pid)
    def find_entry(self, pid: str) -> Optional[PluginEntry]: return self._find_entry(pid)
    def find_by_capability(self, cap: str) -> Tuple[PluginProtocol, ...]:
        return tuple(self._plugins[e.plugin_id] for eid in self._by_capability.get(cap,[])
                     if (e:=self._entries.get(eid)) and e.plugin_id in self._plugins)
    def list(self) -> Tuple[PluginEntry, ...]:
        return tuple(sorted(self._entries.values(), key=lambda e: (-e.priority, e.name)))
    def enable(self, pid: str) -> bool:
        e = self._find_entry(pid)
        if not e: return False
        self._entries[e.entry_id] = PluginEntry(entry_id=e.entry_id, plugin_id=e.plugin_id, name=e.name,
            version=e.version, capability_names=e.capability_names, healthy=e.healthy, enabled=True,
            dependencies=e.dependencies, priority=e.priority)
        return True
    def disable(self, pid: str) -> bool:
        e = self._find_entry(pid)
        if not e: return False
        self._entries[e.entry_id] = PluginEntry(entry_id=e.entry_id, plugin_id=e.plugin_id, name=e.name,
            version=e.version, capability_names=e.capability_names, healthy=e.healthy, enabled=False,
            dependencies=e.dependencies, priority=e.priority)
        return True
    def get_statistics(self) -> PluginStatistics:
        en = sum(1 for e in self._entries.values() if e.enabled)
        di = len(self._entries)-en; h = sum(1 for e in self._entries.values() if e.healthy)
        u = len(self._entries)-h
        return PluginStatistics(total=len(self._entries), enabled=en, disabled=di, healthy=h, unhealthy=u)
    @property
    def count(self): return len(self._entries)
    def clear(self): self._plugins.clear(); self._entries.clear(); self._by_capability.clear()
