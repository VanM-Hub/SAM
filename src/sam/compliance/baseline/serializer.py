"""BaselineSerializer — deterministic (de)serialization of a snapshot.

Serialization uses sorted keys so identical snapshots always produce
identical JSON bytes. The round-trip preserves all entries.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List

from .entry import BaselineEntry
from .snapshot import BaselineSnapshot


class BaselineSerializer:
    """Serializes BaselineSnapshot <-> dict / JSON string."""

    #: Snapshot format marker for forward-compatibility checks.
    FORMAT = "P1-007-baseline/v1"

    # -- Serialize ------------------------------------------------------------

    def serialize(self, snapshot: BaselineSnapshot) -> Dict[str, Any]:
        """Return a plain dict representation (deterministic order)."""
        entries = [entry.to_dict() for entry in snapshot.files()]
        return {
            "format": self.FORMAT,
            "entry_count": snapshot.count,
            "type_distribution": snapshot.type_distribution(),
            "entries": entries,
        }

    def to_json(self, snapshot: BaselineSnapshot, indent: int = 2) -> str:
        """Return a deterministic JSON string."""
        return json.dumps(self.serialize(snapshot), indent=indent, sort_keys=True)

    # -- Deserialize ----------------------------------------------------------

    def deserialize(self, data: Dict[str, Any]) -> BaselineSnapshot:
        """Build a snapshot from a serialized dict.

        Raises:
            ValueError: If the format marker is not recognized.
        """
        fmt = data.get("format")
        if fmt != self.FORMAT:
            raise ValueError("unsupported baseline format: %r" % (fmt,))
        raw_entries = data.get("entries", [])
        entries = [BaselineEntry.from_dict(e) for e in raw_entries]
        return BaselineSnapshot(entries)

    def from_json(self, text: str) -> BaselineSnapshot:
        """Build a snapshot from a JSON string."""
        return self.deserialize(json.loads(text))
