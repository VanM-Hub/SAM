"""BaselineEntry — a single record in the baseline snapshot.

Each entry describes one file the compliance suite can reference.
It carries a stable identity (file_id, logical_id) independent of the
relative path so checkers can address a document by a stable id even
if the path changes.

Immutable — a frozen dataclass (Python 3.8 compatible via `Dict`).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


@dataclass(frozen=True)
class BaselineEntry:
    """A single indexed file in the baseline snapshot."""

    file_id: str                  # stable id, e.g. "DOC-FOUNDATION-001"
    logical_id: str               # logical name, e.g. "CITIZEN_SPECIFICATION"
    document_type: str            # e.g. "foundation", "specification", "adr", "source", ...
    authority: Optional[str]      # e.g. "CONSTITUTION", "Specification", "ADR", None
    checksum: str                 # sha256 of file content
    relative_path: str            # path relative to repo root, POSIX-style
    traceability: Tuple[str, ...] = ()  # related file_ids / logical_ids

    def to_dict(self) -> Dict[str, object]:
        """Plain dict representation for serialization."""
        return {
            "file_id": self.file_id,
            "logical_id": self.logical_id,
            "document_type": self.document_type,
            "authority": self.authority,
            "checksum": self.checksum,
            "relative_path": self.relative_path,
            "traceability": list(self.traceability),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, object]) -> "BaselineEntry":
        """Rebuild an entry from a plain dict (tolerant of missing keys)."""
        return cls(
            file_id=str(data.get("file_id", "")),
            logical_id=str(data.get("logical_id", "")),
            document_type=str(data.get("document_type", "document")),
            authority=data.get("authority"),
            checksum=str(data.get("checksum", "")),
            relative_path=str(data.get("relative_path", "")),
            traceability=tuple(data.get("traceability") or ()),
        )

    def __repr__(self) -> str:
        return "BaselineEntry(file_id=%s, logical_id=%s, type=%s)" % (
            self.file_id, self.logical_id, self.document_type)
