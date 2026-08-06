"""REST Router - Program J (Presentation Host).

Struktur host REST API (composition-only). `RESTEndpoint` adalah DTO immutable
(ADR-023) yang mendeskripsikan satu endpoint REST: path, method, tag, dan
resolver. `RESTRouter` membungkus `fastapi.APIRouter` dan mendaftarkan endpoint
(via `include_router` / route registration).

TIDAK ada business logic. Resolver endpoint di-inject saat J2 (wiring ke
`runtime_service.api`). Modul ini TIDAK mengimpor Runtime/Registry/Provider/
Connector/ExecutionRuntime.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Callable, List, Optional

from fastapi import APIRouter


@dataclass(frozen=True)
class RESTEndpoint:
    """Spesifikasi satu endpoint REST (immutable, ADR-023).

    Attributes:
        path: path relatif di dalam router (mis. "/workflow").
        kwargs: parameter route FastAPI (method, status_code, dll).
        handler: sync/async handler yang dipanggil saat request.
        tag: label grup untuk OpenAPI.
    """
    path: str
    tag: str
    handler: Callable
    method: str = "GET"

    def route_kwargs(self) -> dict:
        """Kwargs registrasi route FastAPI (composition-only)."""
        return {
            "methods": [self.method],
            "tags": [self.tag],
        }


class RESTRouter:
    """Pembungkus FastAPI APIRouter untuk registrasi endpoint (composition-only)."""

    def __init__(self, prefix: str = "", tags: Optional[List[str]] = None) -> None:
        self._prefix = prefix
        self._tags = tags or []
        self._router = APIRouter(prefix=self._prefix, tags=self._tags)

    @property
    def router(self) -> APIRouter:
        """APIRouter bawaan (untuk include ke aplikasi)."""
        return self._router

    @property
    def prefix(self) -> str:
        return self._prefix

    def register(self, endpoint: RESTEndpoint) -> "RESTRouter":
        """Daftarkan satu endpoint ke router (composition-only)."""
        self._router.add_api_route(
            endpoint.path,
            endpoint.handler,
            **endpoint.route_kwargs(),
        )
        return self

    def register_many(self, endpoints: List[RESTEndpoint]) -> "RESTRouter":
        """Daftarkan beberapa endpoint sekaligus."""
        for ep in endpoints:
            self.register(ep)
        return self

    def register_router(self, router: "RESTRouter") -> "RESTRouter":
        """Include router lain (nested)."""
        self._router.include_router(router.router)
        return self

    def paths(self) -> List[str]:
        """Path terdaftar (inspection, composition-only)."""
        return [r.path for r in self._router.routes]
