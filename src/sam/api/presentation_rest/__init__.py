"""REST Presentation Host - Program J.

Struktur host REST API (composition-only):
- RESTApplication : pembungkus FastAPI app.
- RESTRouter      : pembungkus APIRouter + registrasi RESTEndpoint.
- RESTEndpoint    : DTO immutable spesifikasi endpoint (ADR-023).
- RESTSerializer  : pemetaan hasil capability -> dict JSON.

Wiring ke `runtime_service.api` dilakukan di entry `sam.api` (J2), TIDAK di sini.
"""
from __future__ import annotations

from .rest_application import RESTApplication
from .rest_router import RESTRouter, RESTEndpoint
from .rest_serializer import RESTSerializer

__all__ = [
    "RESTApplication",
    "RESTRouter",
    "RESTEndpoint",
    "RESTSerializer",
]
