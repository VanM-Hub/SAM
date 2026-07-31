"""Preview Engine — engine preview connector.

Sprint 119 — Connector Preview.
Menghasilkan preview simulasi berdasarkan capability connector — tanpa eksekusi.
"""
from __future__ import annotations
from typing import List

from .connector_registry import ConnectorRegistry
from .preview_request import PreviewRequest
from .preview_result import PreviewResult


class PreviewEngine:
    """Preview simulasi untuk connector."""

    def __init__(self, registry: ConnectorRegistry) -> None:
        self._registry = registry

    def preview(self, request: PreviewRequest) -> PreviewResult:
        connector = self._registry.get(request.connector_id)
        if connector is None:
            return PreviewResult(request.preview_id, request.connector_id,
                                 request.operation, False, [], 0,
                                 "connector not found")
        caps = self._registry.get_capabilities(request.connector_id)
        cap_names = [c.name for c in caps]
        effects = [
            f"preview {request.operation} on {connector.name}",
            f"capabilities: {', '.join(cap_names) if cap_names else 'none'}",
            "dry-run: no external call made",
        ]
        return PreviewResult(request.preview_id, request.connector_id, request.operation,
                             True, effects, 0, "preview simulated")
