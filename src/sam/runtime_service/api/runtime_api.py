"""RuntimeAPI (Sprint 267).

Program D - Runtime Services & Deployment.
Internal API — belum HTTP. Dispatch request/response + status/health.
"""
from __future__ import annotations
from typing import Callable, Dict

from .health import APIHealth
from .request import APIRequest
from .response import APIResponse
from .status import APIStatus


class RuntimeAPI:
    """Internal API runtime (sync, deterministic, belum HTTP)."""

    def __init__(self) -> None:
        self._handlers: Dict[str, Callable[[APIRequest], APIResponse]] = {}

    def register(self, action: str,
                 handler: Callable[[APIRequest], APIResponse]) -> None:
        self._handlers[action] = handler

    def has(self, action: str) -> bool:
        return action in self._handlers

    def handle(self, request: APIRequest) -> APIResponse:
        handler = self._handlers.get(request.action)
        if handler is None:
            return APIResponse(
                request_id=request.request_id, status="error",
                error=f"unknown action: {request.action}",
            )
        try:
            return handler(request)
        except Exception as exc:  # pragma: no cover
            return APIResponse(
                request_id=request.request_id, status="error",
                error=str(exc),
            )

    def status(self) -> APIStatus:
        return APIStatus(
            services={a: "ok" for a in self._handlers},
        )

    def health(self) -> APIHealth:
        if self._handlers:
            return APIHealth(status="healthy", checks=list(self._handlers))
        return APIHealth(status="degraded", message="no handlers registered")
