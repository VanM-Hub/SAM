"""Connector Filter — engine filter connector.

Sprint 113 — Connector Discovery.
Filter daftar connector berdasarkan kriteria (read-only, deterministik).
"""
from __future__ import annotations
from typing import List, Optional

from .connector_registry import ConnectorRegistry
from .connector_descriptor import ConnectorDescriptor


class ConnectorFilter:
    """Filter connector dari registry berdasarkan kriteria."""

    def __init__(self, registry: ConnectorRegistry) -> None:
        self._registry = registry

    def _all(self) -> List[ConnectorDescriptor]:
        return [self._registry.get(cid) for cid in self._registry.list_ids()
                if self._registry.get(cid) is not None]

    def by_type(self, connector_type: str) -> List[ConnectorDescriptor]:
        return [d for d in self._all() if d.connector_type == connector_type]

    def by_tag(self, tag: str) -> List[ConnectorDescriptor]:
        return [d for d in self._all() if tag in d.tags]

    def by_name_contains(self, fragment: str) -> List[ConnectorDescriptor]:
        frag = fragment.lower()
        return [d for d in self._all() if frag in d.name.lower()]

    def by_version(self, version: str) -> List[ConnectorDescriptor]:
        return [d for d in self._all() if d.version == version]
