"""Conversation Builder Bridge — query read-only (Sprint 190)."""
from __future__ import annotations

from ..context.cognitive_context import CognitiveContext
from .context_builder import ContextBuilder
from .snapshot_builder import SnapshotBuilder
from .workspace_builder import WorkspaceBuilder
from .preview_builder import PreviewBuilder


class ConversationBuilderBridge:
    """Bridge conversation — 5 query read-only builder kognitif."""

    def __init__(self) -> None:
        self._ctx = ContextBuilder()
        self._snap = SnapshotBuilder()
        self._ws = WorkspaceBuilder()
        self._prev = PreviewBuilder()

    def query_1_context(self, cognitive_id: str) -> CognitiveContext:
        return self._ctx.build(cognitive_id)

    def query_2_snapshot(self, snapshot_id: str, context: CognitiveContext):
        return self._snap.build(snapshot_id, context)

    def query_3_workspace(self, workspace_id: str):
        return self._ws.build(workspace_id)

    def query_4_preview(self, label: str, context: CognitiveContext):
        return self._prev.build(label, context)

    def query_5_compose(self, cognitive_id: str) -> dict:
        ctx = self._ctx.build(cognitive_id)
        return {"cognitive_id": ctx.cognitive_id, "entry_count": ctx.entry_count()}
