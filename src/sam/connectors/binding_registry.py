"""Binding Registry — engine registrasi & manajemen binding.

Sprint 115 — Connector Binding.
Registry binding di dalam memori; sinkronus, deterministik, preview-only.
"""
from __future__ import annotations
from typing import Dict, List, Optional

from .connector_registry import ConnectorRegistry
from .binding_request import BindingRequest
from .binding_result import BindingResult


class BindingRegistry:
    """Kelola binding antara connector dan kebutuhan kapabilitas."""

    def __init__(self, connector_registry: ConnectorRegistry) -> None:
        self._connectors = connector_registry
        self._bindings: Dict[str, BindingResult] = {}

    def bind(self, request: BindingRequest) -> BindingResult:
        if request.connector_id not in self._connectors.list_ids():
            return BindingResult(request.request_id, request.connector_id, False,
                                 "connector not found")
        # semua capability_id harus didukung connector
        supported = {c.capability_id for c in
                     self._connectors.get_capabilities(request.connector_id)}
        missing = [c for c in request.capability_ids if c not in supported]
        if missing:
            return BindingResult(request.request_id, request.connector_id, False,
                                 f"missing capabilities: {missing}")
        result = BindingResult(request.request_id, request.connector_id, True,
                               "bound", list(request.capability_ids))
        self._bindings[request.request_id] = result
        return result

    def get(self, binding_id: str) -> Optional[BindingResult]:
        return self._bindings.get(binding_id)

    def list_bindings(self) -> List[BindingResult]:
        return list(self._bindings.values())

    def count(self) -> int:
        return len(self._bindings)
