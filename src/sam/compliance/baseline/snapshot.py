"""BaselineSnapshot — immutable baseline inventory.

The snapshot is the single source of the file inventory for all
compliance checkers. Entries are keyed by file_id (rejecting
duplicates) and are immutable once built.

API (per P1-007):
    files()           -> all entries (deterministic order)
    documents()       -> entries whose document_type is a document
    source_files()    -> entries in the source tree
    test_files()      -> entries in the test tree
    find()            -> lookup by file_id / logical_id / path
    exists()          -> whether a file_id / logical_id / path exists
    checksum()        -> checksum for a file_id (or None)
    serialize()       -> plain dict
"""

from __future__ import annotations

from typing import Dict, Iterable, List, Optional, Tuple

from .entry import BaselineEntry


class ManifestError(Exception):
    """Raised on invalid baseline construction."""


# Document types that represent prose documents (not source/test code).
_DOCUMENT_TYPES = {
    "foundation", "specification", "adr", "runtime", "engineering",
    "blueprint", "compliance", "architecture",
}


class BaselineSnapshot:
    """Immutable inventory of baseline files."""

    def __init__(self, entries: Iterable[BaselineEntry]):
        """Build snapshot from entries.

        Raises:
            ManifestError: If a file_id is duplicated.
        """
        self._entries: Dict[str, BaselineEntry] = {}
        for entry in entries:
            if entry.file_id in self._entries:
                raise ManifestError(
                    "duplicate file_id in snapshot: %s" % entry.file_id)
            self._entries[entry.file_id] = entry
        self._frozen = True

    # -- Selection ------------------------------------------------------------

    def files(self) -> List[BaselineEntry]:
        """All entries, deterministically sorted by (file_id)."""
        return sorted(self._entries.values(), key=lambda e: e.file_id)

    def documents(self) -> List[BaselineEntry]:
        """Document-type entries, deterministically sorted."""
        return sorted(
            (e for e in self._entries.values() if e.document_type in _DOCUMENT_TYPES),
            key=lambda e: e.file_id)

    def by_type(self, document_type: str) -> List[BaselineEntry]:
        """Entries of a given document_type."""
        return sorted(
            (e for e in self._entries.values() if e.document_type == document_type),
            key=lambda e: e.file_id)

    def by_authority(self, authority: str) -> List[BaselineEntry]:
        """Entries with a given authority."""
        return sorted(
            (e for e in self._entries.values() if e.authority == authority),
            key=lambda e: e.file_id)

    def source_files(self) -> List[BaselineEntry]:
        """Entries in the source tree (src/**)."""
        return self.by_type("source")

    def test_files(self) -> List[BaselineEntry]:
        """Entries in the test tree (tests/**)."""
        return self.by_type("test")

    # -- Lookup ---------------------------------------------------------------

    def get(self, file_id: str) -> Optional[BaselineEntry]:
        """Entry by file_id, or None."""
        return self._entries.get(file_id)

    def find(self, *queries: str) -> List[BaselineEntry]:
        """Find entries matching file_id, logical_id, or relative_path.

        A query may match any of these identites. Returns deterministic
        sorted list. Supports prefix matching for paths.
        """
        results = []
        seen = set()
        for query in queries:
            for entry in self._entries.values():
                if entry.file_id in seen:
                    continue
                if (
                    entry.file_id == query
                    or entry.logical_id == query
                    or entry.relative_path == query
                    or entry.relative_path.startswith(query)
                ):
                    seen.add(entry.file_id)
                    results.append(entry)
        return sorted(results, key=lambda e: e.file_id)

    def exists(self, *queries: str) -> bool:
        """True if any query resolves to an entry."""
        return bool(self.find(*queries))

    def checksum(self, file_id: str) -> Optional[str]:
        """Checksum for a file_id, or None if absent."""
        entry = self._entries.get(file_id)
        return entry.checksum if entry else None

    # -- Introspection --------------------------------------------------------

    @property
    def count(self) -> int:
        return len(self._entries)

    def type_distribution(self) -> Dict[str, int]:
        """Count of entries per document_type, sorted by type."""
        dist: Dict[str, int] = {}
        for e in self._entries.values():
            dist[e.document_type] = dist.get(e.document_type, 0) + 1
        return {k: dist[k] for k in sorted(dist)}

    def __len__(self) -> int:
        return len(self._entries)

    def __iter__(self):
        return iter(self.files())

    def __contains__(self, file_id: str) -> bool:
        return file_id in self._entries
