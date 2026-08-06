"""BaselineLoader — scans the SAM project tree and builds a snapshot.

The loader is the ONLY place that knows how files map to document
types and logical ids. Once a snapshot is built, checkers never scan
the tree themselves — they consult the snapshot.

Deterministic: file discovery is sorted; checksums are content-derived.
"""

from __future__ import annotations

import hashlib
import os
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

from .entry import BaselineEntry
from .snapshot import BaselineSnapshot

# Repo root is two levels up from src/sam/compliance/baseline/
_PKG_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _PKG_DIR.parents[3]

# Path prefixes (relative to repo root) -> document_type
_DOC_DIR_TYPES = {
    "docs/foundation": "foundation",
    "docs/specifications": "specification",
    "docs/adr": "adr",
    "docs/runtime": "runtime",
    "docs/engineering": "engineering",
    "docs/blueprint": "blueprint",
    "docs/blueprints": "blueprint",
    "docs/compliance": "compliance",
    "docs/architecture": "architecture",
    "docs/design": "engineering",
    "docs/core": "foundation",
}

# Files at repo root -> document_type
# Note: CONSTITUTION.md, PHILOSOPHY.md, CITIZEN_SPECIFICATION.md, MISSION.md,
# VISION.md, CHARTER.md, GOVERNANCE.md, PRINCIPLES.md, and GLOSSARY.md were moved
# to docs/foundation/ (2026-08-07) and are now scanned via
# _DOC_DIR_TYPES["docs/foundation"]. They are intentionally absent from this root
# map to keep compliance aligned with the actual repository layout.
_ROOT_FILE_TYPES = {}

# Package tree files (repo root / config files)
_PACKAGE_TYPES = {
    "pyproject.toml": "package",
    "README.md": "package",
    "setup.py": "package",
    "setup.cfg": "package",
}

# Directories scanned as source tree (relative to repo root)
_SOURCE_DIRS = ("src/sam",)
# Directories scanned as test tree (relative to repo root)
_TEST_DIRS = ("tests",)
# Filesystem dirs to skip when scanning
_SKIP_DIRS = {"__pycache__", ".pytest_cache", ".ruff_cache", ".venv", ".git", "node_modules"}


class BaselineLoader:
    """Loads a BaselineSnapshot from the SAM project tree."""

    def __init__(self, root: Optional[str] = None) -> None:
        """Build loader.

        Args:
            root: Repo root. Defaults to the detected repo root.
        """
        self._root = Path(root) if root else _REPO_ROOT

    # -- Public API -----------------------------------------------------------

    def load(self) -> BaselineSnapshot:
        """Scan the tree and build a deterministic BaselineSnapshot."""
        entries = self._collect()
        return BaselineSnapshot(entries)

    # -- Collection -----------------------------------------------------------

    def _collect(self) -> List[BaselineEntry]:
        collected: List[BaselineEntry] = []
        counter = _IdCounter()

        for rel, document_type, authority in self._iter_root_documents():
            collected.append(self._build_entry(
                rel, document_type, authority, counter))

        for rel, document_type in self._iter_dir_documents():
            authority = _authority_for_type(document_type)
            collected.append(self._build_entry(
                rel, document_type, authority, counter))

        for rel in self._iter_tree(_SOURCE_DIRS, kinds=(".py",)):
            collected.append(self._build_entry(
                rel, "source", None, counter))

        for rel in self._iter_tree(_TEST_DIRS, kinds=(".py",)):
            collected.append(self._build_entry(
                rel, "test", None, counter))

        for rel, document_type in self._iter_package_files():
            collected.append(self._build_entry(
                rel, document_type, "System", counter))

        return collected

    def _build_entry(
        self,
        rel: str,
        document_type: str,
        authority: Optional[str],
        counter: "_IdCounter",
        traceability: Tuple[str, ...] = (),
    ) -> BaselineEntry:
        """Compute checksum and stable ids for a file."""
        path = self._root / rel
        checksum = _sha256(path)
        file_id = counter.next(document_type)
        logical_id = _logical_id(rel, document_type)
        return BaselineEntry(
            file_id=file_id,
            logical_id=logical_id,
            document_type=document_type,
            authority=authority,
            checksum=checksum,
            relative_path=rel,
            traceability=traceability,
        )

    # -- Iterators ------------------------------------------------------------

    def _iter_root_documents(self) -> Iterable[Tuple[str, str, Optional[str]]]:
        """Yield (relpath, type, authority) for root-level docs."""
        for rel, document_type in sorted(_ROOT_FILE_TYPES.items()):
            if (self._root / rel).is_file():
                yield rel, document_type, _authority_for_type(document_type)

    def _iter_dir_documents(self) -> Iterable[Tuple[str, str]]:
        """Yield (relpath, type) for docs under known directories."""
        for prefix, document_type in sorted(_DOC_DIR_TYPES.items()):
            base = self._root / prefix
            if not base.is_dir():
                continue
            for rel in self._iter_tree((prefix,), kinds=(".md",)):
                yield rel, self._classify_doc(rel, document_type)

    @staticmethod
    def _classify_doc(rel: str, inferred: str) -> str:
        """Override inferred type based on filename markers."""
        name = Path(rel).name.lower()
        if "blueprint" in name:
            return "blueprint"
        if name.startswith("adr-"):
            return "adr"
        return inferred

    def _iter_package_files(self) -> Iterable[Tuple[str, str]]:
        """Yield (relpath, type) for package/config root files."""
        for rel, document_type in sorted(_PACKAGE_TYPES.items()):
            if (self._root / rel).is_file():
                yield rel, document_type

    def _iter_tree(
        self, prefixes, kinds: Tuple[str, ...], trace_root: bool = True
    ) -> Iterable[str]:
        """Yield POSIX relative paths under prefixes, skipping noise dirs."""
        entries = []
        for prefix in prefixes:
            base = self._root / prefix
            if not base.exists():
                continue
            for dirpath, dirnames, filenames in os.walk(str(base)):
                dirnames[:] = [d for d in dirnames if d not in _SKIP_DIRS]
                dirnames.sort()
                for fname in sorted(filenames):
                    if fname.endswith(kinds):
                        full = os.path.join(dirpath, fname)
                        rel = os.path.relpath(full, str(self._root))
                        entries.append(rel.replace(os.sep, "/"))
        return iter(sorted(entries))


class _IdCounter:
    """Assigns stable sequential file_ids per document_type."""

    def __init__(self) -> None:
        self._counts: Dict[str, int] = {}

    def next(self, document_type: str) -> str:
        self._counts[document_type] = self._counts.get(document_type, 0) + 1
        idx = self._counts[document_type]
        return "FID-%s-%03d" % (document_type.upper(), idx)


def _authority_for_type(document_type: str) -> Optional[str]:
    """Map a document_type to an authority label, if any."""
    mapping = {
        "foundation": "CONSTITUTION",
        "specification": "Specification",
        "adr": "ADR",
        "architecture": "Architecture",
        "blueprint": "Blueprint",
        "engineering": "Engineering",
        "compliance": "Compliance",
        "runtime": "Runtime",
    }
    return mapping.get(document_type)


def _logical_id(rel: str, document_type: str) -> str:
    """Derive a stable, collision-resistant logical_id from relative path.

    Because same-named modules exist in different packages (and the path
    separator vs underscore encoding is not injective), the logical id is
    a deterministic short hash of the relative path. Hash is over the
    normalized path string so it is stable across re-scans and platforms.
    """
    import hashlib
    digest = hashlib.sha256(rel.encode("utf-8")).hexdigest()[:10].upper()
    return "%s_%s" % (document_type.upper(), digest)


def _sha256(path: Path) -> str:
    """Compute the sha256 hex digest of a file."""
    h = hashlib.sha256()
    with open(str(path), "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()
