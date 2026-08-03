"""BaselineIndex — fast deterministic lookup index over a snapshot.

Builds several lookup maps (by file_id, logical_id, document_type,
authority, relative_path) once, then serves O(1) lookups. All maps are
built deterministically and are immutable after construction.
"""

from __future__ import annotations

from typing import Dict, List, Optional

from .entry import BaselineEntry
from .snapshot import BaselineSnapshot


class BaselineIndex:
    """Read-only lookup index over BaselineSnapshot entries."""

    def __init__(self, snapshot: BaselineSnapshot) -> None:
        """Build index from a snapshot.

        Builds:
            _by_file_id    : file_id -> entry
            _by_logical    : logical_id -> entry (unique per snapshot)
            _by_type       : document_type -> [entry]
            _by_authority  : authority -> [entry]
            _by_path       : relative_path -> entry (unique)
        """
        self._snapshot = snapshot
        self._by_file_id: Dict[str, BaselineEntry] = {}
        self._by_logical: Dict[str, BaselineEntry] = {}
        self._by_type: Dict[str, List[BaselineEntry]] = {}
        self._by_authority: Dict[str, List[BaselineEntry]] = {}
        self._by_path: Dict[str, BaselineEntry] = {}

        for entry in snapshot.files():  # already sorted by file_id
            self._by_file_id[entry.file_id] = entry
            if entry.logical_id not in self._by_logical:
                # keep first occurrence deterministically
                self._by_logical[entry.logical_id] = entry
            self._by_type.setdefault(entry.document_type, []).append(entry)
            auth = entry.authority
            if auth is not None:
                self._by_authority.setdefault(auth, []).append(entry)
            self._by_path[entry.relative_path] = entry

    # -- Accessors ------------------------------------------------------------

    @property
    def snapshot(self) -> BaselineSnapshot:
        return self._snapshot

    def by_file_id(self, file_id: str) -> Optional[BaselineEntry]:
        return self._by_file_id.get(file_id)

    def by_logical_id(self, logical_id: str) -> Optional[BaselineEntry]:
        return self._by_logical.get(logical_id)

    def by_path(self, relative_path: str) -> Optional[BaselineEntry]:
        return self._by_path.get(relative_path)

    def by_type(self, document_type: str) -> List[BaselineEntry]:
        """Entries of a type, in deterministic (file_id) order."""
        return list(self._by_type.get(document_type, []))

    def by_authority(self, authority: str) -> List[BaselineEntry]:
        """Entries with an authority, deterministic order."""
        return list(self._by_authority.get(authority, []))

    def types(self) -> List[str]:
        """Available document types, sorted."""
        return sorted(self._by_type)

    def authorities(self) -> List[str]:
        """Available authorities, sorted."""
        return sorted(self._by_authority)

    def __len__(self) -> int:
        return len(self._by_file_id)
