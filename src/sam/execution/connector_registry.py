# OP-393 — Connector Registry
# Python 3.8 compatible, frozen dataclass, synchronous only
# Registry for execution connectors — does NOT instantiate them automatically

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple, Protocol
import uuid

from .connector_protocol import ConnectorProtocol, ConnectorInfo


# ---------------------------------------------------------------------------
# Registry DTOs
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class RegistryEntry:
    """An entry in the connector registry."""
    entry_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    connector_id: str = ""
    name: str = ""
    connector_type: str = ""
    version: str = ""
    description: str = ""
    capability_actions: Tuple[str, ...] = field(default_factory=tuple)
    healthy: bool = True
    priority: int = 0  # higher = preferred
    registered_at: datetime = field(default_factory=datetime.utcnow)


@dataclass(frozen=True)
class CapabilityLookup:
    """Result of a capability lookup."""
    connector_ids: Tuple[str, ...] = field(default_factory=tuple)
    connector_types: Tuple[str, ...] = field(default_factory=tuple)
    total_found: int = 0


# ---------------------------------------------------------------------------
# ConnectorRegistry
# ---------------------------------------------------------------------------

class ConnectorRegistry:
    """Registry for execution connectors.

    Stores connector metadata and provides lookup/capability search.
    Does NOT instantiate connectors — only stores references.
    """

    def __init__(self) -> None:
        self._entries: Dict[str, RegistryEntry] = {}  # entry_id -> entry
        self._connectors: Dict[str, ConnectorProtocol] = {}  # connector_id -> connector
        self._by_type: Dict[str, List[str]] = {}  # connector_type -> [entry_id]
        self._by_action: Dict[str, List[str]] = {}  # action -> [entry_id]

    # --- Registration ---

    def register(self, connector: ConnectorProtocol, priority: int = 0) -> RegistryEntry:
        """Register a connector. Does NOT instantiate — just stores reference.

        Returns the RegistryEntry. Detects duplicates by connector_id.
        """
        info = connector.info
        connector_id = info.connector_id

        # Duplicate detection
        if connector_id in self._connectors:
            # Update existing entry
            old_entry = self._find_entry_by_connector_id(connector_id)
            if old_entry:
                # Remove old indices
                self._remove_from_indices(old_entry)
                self._entries.pop(old_entry.entry_id, None)

        # Store connector reference
        self._connectors[connector_id] = connector

        # Create entry
        actions = connector.supported_actions()
        entry = RegistryEntry(
            connector_id=connector_id,
            name=info.name,
            connector_type=info.connector_type,
            version=info.version,
            description=info.description,
            capability_actions=actions,
            healthy=info.healthy,
            priority=priority,
        )

        self._entries[entry.entry_id] = entry
        self._add_to_indices(entry, actions)

        return entry

    def _find_entry_by_connector_id(self, connector_id: str) -> Optional[RegistryEntry]:
        for entry in self._entries.values():
            if entry.connector_id == connector_id:
                return entry
        return None

    def _add_to_indices(self, entry: RegistryEntry, actions: Tuple[str, ...]) -> None:
        self._by_type.setdefault(entry.connector_type, []).append(entry.entry_id)
        for action in actions:
            self._by_action.setdefault(action, []).append(entry.entry_id)

    def _remove_from_indices(self, entry: RegistryEntry) -> None:
        type_list = self._by_type.get(entry.connector_type)
        if type_list and entry.entry_id in type_list:
            type_list.remove(entry.entry_id)

        for action in entry.capability_actions:
            action_list = self._by_action.get(action)
            if action_list and entry.entry_id in action_list:
                action_list.remove(entry.entry_id)

    def unregister(self, connector_id: str) -> bool:
        """Remove a connector from registry by its ID."""
        entry = self._find_entry_by_connector_id(connector_id)
        if entry is None:
            return False

        self._remove_from_indices(entry)
        self._entries.pop(entry.entry_id, None)
        self._connectors.pop(connector_id, None)
        return True

    # --- Lookup ---

    def find(self, connector_id: str) -> Optional[ConnectorProtocol]:
        """Find a connector by its connector_id."""
        return self._connectors.get(connector_id)

    def find_entry(self, connector_id: str) -> Optional[RegistryEntry]:
        """Find a registry entry by connector_id."""
        return self._find_entry_by_connector_id(connector_id)

    def find_by_type(self, connector_type: str) -> Tuple[ConnectorProtocol, ...]:
        """Find all connectors of a given type."""
        entry_ids = self._by_type.get(connector_type, [])
        result = []
        for eid in entry_ids:
            entry = self._entries.get(eid)
            if entry and entry.connector_id in self._connectors:
                result.append(self._connectors[entry.connector_id])
        return tuple(result)

    def find_by_action(self, action: str) -> Tuple[ConnectorProtocol, ...]:
        """Find all connectors that support a given action."""
        entry_ids = self._by_action.get(action, [])
        result = []
        for eid in entry_ids:
            entry = self._entries.get(eid)
            if entry and entry.connector_id in self._connectors:
                result.append(self._connectors[entry.connector_id])
        return tuple(result)

    def capability_lookup(self, action: str) -> CapabilityLookup:
        """Look up connectors by capability (action support)."""
        connectors = self.find_by_action(action)
        return CapabilityLookup(
            connector_ids=tuple(c.info.connector_id for c in connectors),
            connector_types=tuple(c.info.connector_type for c in connectors),
            total_found=len(connectors),
        )

    # --- List / Summary ---

    def list(self) -> Tuple[RegistryEntry, ...]:
        """List all registered entries, sorted by priority descending."""
        return tuple(
            sorted(self._entries.values(), key=lambda e: e.priority, reverse=True)
        )

    def health_summary(self) -> Dict[str, Any]:
        """Get health summary of all registered connectors."""
        total = len(self._entries)
        healthy_count = sum(1 for e in self._entries.values() if e.healthy)
        by_type: Dict[str, int] = {}
        for e in self._entries.values():
            by_type[e.connector_type] = by_type.get(e.connector_type, 0) + 1

        return {
            "total_connectors": total,
            "healthy": healthy_count,
            "unhealthy": total - healthy_count,
            "by_type": by_type,
        }

    @property
    def count(self) -> int:
        return len(self._entries)

    def clear(self) -> None:
        """Clear all entries (for testing)."""
        self._entries.clear()
        self._connectors.clear()
        self._by_type.clear()
        self._by_action.clear()
