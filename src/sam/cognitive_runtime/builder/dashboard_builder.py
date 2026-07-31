"""Dashboard Builder Bridge — 5 ExecutionCards (Sprint 190)."""
from __future__ import annotations

from ..dashboard import ExecutionCard
from ..context.cognitive_context import CognitiveContext
from ..context.cognitive_snapshot import CognitiveSnapshot
from .context_builder import ContextBuilder
from .snapshot_builder import SnapshotBuilder
from .workspace_builder import CognitiveWorkspaceDTO
from .preview_builder import CognitivePreviewDTO


class DashboardBuilderBridge:
    """Bridge dashboard — 5 kartu untuk builder kognitif."""

    def cards(self, ctx: CognitiveContext = None):
        ctx = ctx or ContextBuilder().build("c0")
        return [
            ExecutionCard("bd.context", "builder", "ready",
                          f"context {ctx.cognitive_id} ({ctx.entry_count()} entries)",
                          "context", "ready"),
            ExecutionCard("bd.snapshot", "builder", "ready",
                          "CognitiveSnapshot composed", "snapshot", "ready"),
            ExecutionCard("bd.workspace", "builder", "ready",
                          "CognitiveWorkspaceDTO immutable", "workspace", "ready"),
            ExecutionCard("bd.preview", "builder", "ready",
                          "CognitivePreviewDTO inferred=False ext=0", "preview", "ready"),
            ExecutionCard("bd.noinfer", "builder", "ready",
                          "builder: no reasoning, no scoring, no inference", "no-inference", "ready"),
        ]

    def overview_card(self):
        return self.cards()[0]
