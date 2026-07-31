"""Conversation Preview — bridge read-only untuk preview.

Sprint 119 — Connector Preview.
Preview via bridge — tetap preview-only, tidak pernah kirim ke luar.
"""
from __future__ import annotations

from .connector_registry import ConnectorRegistry
from .preview_engine import PreviewEngine
from .preview_request import PreviewRequest
from .preview_result import PreviewResult


class ConversationPreviewBridge:
    """Bridge conversation preview."""

    def __init__(self, registry: ConnectorRegistry) -> None:
        self._engine = PreviewEngine(registry)

    def preview(self, request: PreviewRequest) -> PreviewResult:
        if not request.dry_run:
            request = PreviewRequest(request.preview_id, request.connector_id,
                                     request.operation, request.neutral_payload, True)
        return self._engine.preview(request)
