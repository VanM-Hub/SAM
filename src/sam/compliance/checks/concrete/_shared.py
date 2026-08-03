"""Shared baseline-driven check primitives (P1-008).

These helpers give every checker access to the BaselineSnapshot
(P1-007) so a check never scans the filesystem, never hardcodes a
path, and never hardcodes an authority.

Design rules (per P1-008):
- A checker reads the snapshot via BaselineResolver from the context.
- All selection (which files, which units, which documents) is derived
  by querying the snapshot API — no literal path lists.
- Evidence is deterministic: same snapshot -> same result.

Python 3.8 compatible — Dict/List/Optional from typing.
"""

from __future__ import annotations

import re
from typing import Dict, List, Optional, Sequence, Tuple

from ..base.check_context import CheckContext
from ...baseline.snapshot import BaselineSnapshot
from ...baseline.entry import BaselineEntry


class BaselineNotAvailableError(Exception):
    """Raised when a check needs a baseline but none is provided."""


class BaselineResolver:
    """Resolves the BaselineSnapshot for a check context.

    The baseline may be injected by the executor (preferred) via
    ``context.options["baseline"]``, or lazily loaded once from
    ``context.target_path`` when not provided. Loading is memoized
    per-context so repeated resolution is cheap.
    """

    def __init__(self) -> None:
        self._loaded: Optional[BaselineSnapshot] = None

    def resolve(self, context: CheckContext) -> BaselineSnapshot:
        """Return the baseline snapshot for the context.

        Prefers an injected baseline (context.options["baseline"]).
        Falls back to a lazily-loaded snapshot rooted at
        context.target_path.
        """
        injected = context.options.get("baseline")
        if injected is not None:
            if isinstance(injected, BaselineSnapshot):
                return injected
            if isinstance(injected, dict):
                # Plain dict form produced by BaselineSerializer.serialize().
                from ...baseline.serializer import BaselineSerializer
                return BaselineSerializer().deserialize(injected)
        if self._loaded is None:
            if not context.target_path:
                raise BaselineNotAvailableError(
                    "no baseline injected and no target_path to load from")
            from ...baseline.loader import BaselineLoader
            self._loaded = BaselineLoader(root=context.target_path).load()
        return self._loaded


class SnapshotReader:
    """Read-only facade over BaselineSnapshot for checks.

    Centralises the snapshot queries a checker may perform so the
    verification logic stays in one place (no duplicated query logic
    across the 99 checks).
    """

    def __init__(self, snapshot: BaselineSnapshot) -> None:
        self._snapshot = snapshot

    @property
    def snapshot(self) -> BaselineSnapshot:
        return self._snapshot

    def exists(self, rel_path: str) -> bool:
        return self._snapshot.exists(rel_path)

    def find(self, *queries: str) -> List[BaselineEntry]:
        return self._snapshot.find(*queries)

    def source_files(self) -> List[BaselineEntry]:
        return self._snapshot.source_files()

    def test_files(self) -> List[BaselineEntry]:
        return self._snapshot.test_files()

    def files_under(self, prefix: str) -> List[BaselineEntry]:
        return sorted(
            (e for e in self._snapshot.files()
             if e.relative_path.startswith(prefix)),
            key=lambda e: e.relative_path,
        )

    def files_under_any(self, prefixes: Sequence[str]) -> List[BaselineEntry]:
        merged: Dict[str, BaselineEntry] = {}
        for prefix in prefixes:
            for e in self.files_under(prefix):
                merged[e.relative_path] = e
        return sorted(merged.values(), key=lambda e: e.relative_path)

    def dir_children(self, directory: str) -> List[str]:
        """Immediate child basenames (files + dirs) directly under a directory."""
        prefix = directory.rstrip("/") + "/"
        children = set()
        for e in self._snapshot.files():
            if e.relative_path.startswith(prefix):
                rest = e.relative_path[len(prefix):]
                top = rest.split("/", 1)[0]
                if top:
                    children.add(top)
        return sorted(children)

    def dir_names_under(self, directory: str, depth: int = 1) -> List[str]:
        """Immediate child directory names (not files) under a directory.

        A child is a directory only if some entry in the snapshot has a
        deeper path segment beneath it. Files directly in the directory
        (no second segment) are excluded.
        """
        prefix = directory.rstrip("/") + "/"
        names = set()
        for e in self._snapshot.files():
            if e.relative_path.startswith(prefix):
                rest = e.relative_path[len(prefix):]
                seg = rest.split("/")
                if len(seg) > depth:
                    names.add(seg[depth - 1])
        return sorted(names)

    def dirs_under(self, directory: str, max_depth: int = 2) -> List[str]:
        prefix = directory.rstrip("/") + "/"
        dirs = set()
        for e in self._snapshot.files():
            if e.relative_path.startswith(prefix):
                rest = e.relative_path[len(prefix):]
                parts = rest.split("/")
                for depth in range(max_depth):
                    candidate = "/".join(parts[: depth + 1])
                    if candidate:
                        dirs.add(candidate)
        return sorted(dirs)

    def authorities(self) -> List[str]:
        return sorted({e.authority for e in self._snapshot.files() if e.authority})


class DiskReader:
    """Reads file content from a target root path deterministically.

    Reads are cached globally by (root, relative path) so a source file
    is read from disk at most once per session regardless of how many
    checks inspect it — essential for deterministic, fast execution
    across the 99 checkers.
    """

    _CACHE: Dict[tuple, str] = {}

    def __init__(self, target: str) -> None:
        self._target = target or ""

    def read(self, rel: str) -> str:
        import os
        full = os.path.join(self._target, rel)
        key = (self._target, rel)
        if key in DiskReader._CACHE:
            return DiskReader._CACHE[key]
        try:
            with open(full, "r", encoding="utf-8", errors="replace") as fh:
                content = fh.read()
        except (OSError, UnicodeDecodeError):
            content = ""
        DiskReader._CACHE[key] = content
        return content

    @classmethod
    def clear_cache(cls) -> None:
        cls._CACHE = {}


class ContentIndex:
    """Lazily-built content index over source files in a snapshot.

    Reads each candidate source file from disk once (memoized via
    DiskReader cache) and answers containment queries deterministically.
    Used by L1/L2 SOURCE_CONTAINS / SOURCE_ABSENT checks.

    The read root is the baseline root (context.options["baseline_root"])
    when injected, else context.target_path. Baseline paths are
    project-root-relative, so reading must be relative to the same root
    the snapshot was built from.
    """

    def __init__(self, resolver: BaselineResolver, context: CheckContext,
                 prefixes: Sequence[str] = ("src/sam/",)) -> None:
        self._resolver = resolver
        self._context = context
        self._root = context.options.get("baseline_root") or context.target_path
        self._reader = DiskReader(self._root)
        self._prefixes = tuple(prefixes)

    def _filenames(self) -> List[str]:
        snap = self._resolver.resolve(self._context)
        names = [
            e.relative_path for e in snap.files()
            if e.relative_path.startswith(self._prefixes)
        ]
        return sorted(names)

    def any_file_contains(self, needle: str,
                          is_regex: bool = False) -> Tuple[bool, List[str]]:
        """True if any candidate file contains the needle."""
        hits = []
        for rel in self._filenames():
            content = self._reader.read(rel)
            if _contains(content, needle, is_regex):
                hits.append(rel)
        return (bool(hits), hits)

    def all_files_absent(self, needle: str,
                         is_regex: bool = False) -> bool:
        found, _ = self.any_file_contains(needle, is_regex)
        return not found

    def count_matches(self, needle: str,
                      is_regex: bool = False) -> int:
        total = 0
        for rel in self._filenames():
            content = self._reader.read(rel)
            if is_regex:
                total += len(re.findall(needle, content))
            else:
                total += content.count(needle)
        return total


def _contains(content: str, needle: str, is_regex: bool) -> bool:
    if is_regex:
        try:
            return re.search(needle, content, re.MULTILINE) is not None
        except re.error:
            return needle in content
    return needle in content
