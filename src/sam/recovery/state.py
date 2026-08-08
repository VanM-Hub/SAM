"""Recovery State — DTO checkpoint & metadata.

Immutable dataclass (ADR-023). Menjaga bentuk data checkpoint yang
serializable (JSON) dan aman diamankan checksum.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Optional


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class SnapshotMetadata:
    """Metadata satu checkpoint (tanpa payload state)."""

    checkpoint_id: str
    scope: str                 # namespace runtime/subsistem (mis. "runtime:mission")
    created_at: str
    checksum_sha256: str = ""
    data_version: int = 1
    labels: frozenset[tuple[str, str]] = frozenset()

    def as_dict(self) -> dict:
        return {
            "checkpoint_id": self.checkpoint_id,
            "scope": self.scope,
            "created_at": self.created_at,
            "checksum_sha256": self.checksum_sha256,
            "data_version": self.data_version,
            "labels": dict(self.labels),
        }


@dataclass(frozen=True)
class CheckpointState:
    """Payload state yang disimpan/disimpan ulang."""

    scope: str
    state: Dict[str, Any]
    metadata: SnapshotMetadata

    @staticmethod
    def compute_checksum(state: Dict[str, Any]) -> str:
        """Checksum SHA-256 dari representasi canonical state."""
        canonical = _canonical_json(state)
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _canonical_json(value: Any) -> str:
    """Representasi JSON canonical (sort_keys, ensure_ascii) utk checksum stabil."""
    import json

    return json.dumps(value, sort_keys=True, ensure_ascii=True, separators=(",", ":"))
