"""Snapshot Builder — membangun CognitiveSnapshot (Sprint 190)."""
from __future__ import annotations
from datetime import datetime

from ..context.cognitive_snapshot import CognitiveSnapshot
from ..context.cognitive_context import CognitiveContext


class SnapshotBuilder:
    """Builder snapshot. Deterministik (timestamp sebagai identitas)."""

    def build(self, snapshot_id: str, context: CognitiveContext,
              sources: list = None) -> CognitiveSnapshot:
        return CognitiveSnapshot(
            snapshot_id=snapshot_id, context=context,
            created_at=datetime.utcnow().isoformat(timespec="seconds") + "Z",
            sources=list(sources or []),
        )
