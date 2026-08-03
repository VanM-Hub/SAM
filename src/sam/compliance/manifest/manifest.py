"""ComplianceManifest — single deterministic execution configuration.

The manifest is the ONE source of execution configuration.
No configuration is scattered inside code. It binds every catalog
check (P1-004) to its execution entry, and provides deterministic
query + dependency resolution.

Python 3.8 compatible.
"""

from typing import Dict, List, Optional, Iterator

from .entry import ManifestEntry


class ManifestError(Exception):
    """Manifest-level error (e.g., duplicate entry, unknown dependency)."""
    pass


class ComplianceManifest:
    """Collection of ManifestEntry, the single execution config.

    Rules (enforced by validator, partially enforced here):
    - every catalog check appears exactly once
    - no missing / no duplicate check
    - deterministic execution_order
    - dependency graph acyclic
    - no conditional ordering / random ordering / runtime mutation
    """

    def __init__(self, entries: Optional[List[ManifestEntry]] = None):
        """Build a manifest from a list of ManifestEntry.

        Args:
            entries: List of ManifestEntry. If None, empty manifest.

        Raises:
            ManifestError: If duplicate check_id.
        """
        self._entries: Dict[str, ManifestEntry] = {}
        if entries:
            for entry in entries:
                if entry.check_id in self._entries:
                    raise ManifestError(
                        "Duplicate manifest entry: %s" % entry.check_id)
                self._entries[entry.check_id] = entry

    # -- Core queries ---------------------------------------------------------

    def get(self, check_id: str) -> Optional[ManifestEntry]:
        """Get a single entry by ID. Returns None if not found."""
        return self._entries.get(check_id)

    def entries(self) -> List[ManifestEntry]:
        """All entries, sorted by (execution_order, check_id)."""
        return sorted(
            self._entries.values(),
            key=lambda e: (e.execution_order, e.check_id),
        )

    def enabled(self) -> List[ManifestEntry]:
        """All enabled entries, in deterministic order."""
        return [e for e in self.entries() if e.enabled]

    def disabled(self) -> List[ManifestEntry]:
        """All disabled entries, in deterministic order."""
        return [e for e in self.entries() if not e.enabled]

    def ordered(self) -> List[ManifestEntry]:
        """Entries ordered topologically by dependency graph,
        then by execution_order as the deterministic tie-break.

        Implements a stable topological sort (Kahn's algorithm)
        with execution_order as the deterministic allocator.
        """
        order: List[ManifestEntry] = []
        remaining = dict(self._entries)

        # Build unresolved dependency sets
        deps: Dict[str, set] = {}
        for cid, entry in self._entries.items():
            deps[cid] = {d for d in entry.dependencies
                         if d in self._entries}

        # Allocator: pick the available (no unresolved deps) entry with
        # the smallest (execution_order, check_id) deterministically.
        while remaining:
            ready = [cid for cid, d in deps.items()
                     if cid in remaining and not d & set(remaining.keys())]
            if not ready:
                # Cycle detected — break deterministically, validator
                # reports it. Fall back to (order, id) sorting.
                ready = list(remaining.keys())
            ready.sort(key=lambda cid: (self._entries[cid].execution_order, cid))
            chosen = ready[0]
            order.append(self._entries[chosen])
            del remaining[chosen]

        return order

    # -- Dependency resolution ------------------------------------------------

    def resolve_dependencies(self, check_id: str) -> List[ManifestEntry]:
        """Return the transitive set of dependencies for a check,
        in deterministic order (topological). Does not include the
        check itself.

        Args:
            check_id: Target check id.

        Returns:
            List of ManifestEntry (dependencies only), deterministic order.
        """
        if check_id not in self._entries:
            raise ManifestError("Unknown check: %s" % check_id)

        resolved: List[str] = []
        seen: set = set()

        def visit(cid: str):
            if cid in seen:
                return
            seen.add(cid)
            entry = self._entries[cid]
            for dep in sorted(entry.dependencies):
                if dep in self._entries and dep not in seen:
                    visit(dep)
            if cid != check_id:
                resolved.append(cid)

        visit(check_id)
        # Deterministic: order by execution position among self.entries()
        pos = {e.check_id: idx for idx, e in enumerate(self.entries())}
        resolved.sort(key=lambda cid: (pos.get(cid, 0), cid))
        return [self._entries[cid] for cid in resolved]

    # -- Introspection --------------------------------------------------------

    def count(self) -> int:
        """Total number of entries."""
        return len(self._entries)

    def check_ids(self) -> List[str]:
        """All check IDs in deterministic order."""
        return sorted(self._entries.keys())

    def __len__(self) -> int:
        return self.count()

    def __iter__(self) -> Iterator[ManifestEntry]:
        return iter(self.entries())

    def __contains__(self, check_id: str) -> bool:
        return check_id in self._entries

    def __getitem__(self, check_id: str) -> ManifestEntry:
        entry = self._entries.get(check_id)
        if entry is None:
            raise KeyError("Manifest entry not found: %s" % check_id)
        return entry
