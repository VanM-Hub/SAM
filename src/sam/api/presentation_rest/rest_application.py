"""REST Application - Program J (Presentation Host).

`RESTApplication` membungkus `fastapi.FastAPI` dan mengelola registrasi
`RESTRouter`. Composition-only: aplikasi TIDAK tahu capability; router +
endpoint di-inject di J2 (wiring ke `runtime_service.api`).

TIDAK ada business logic. TIDAK mengimpor Runtime/Registry/Provider/Connector/
ExecutionRuntime.
"""
from __future__ import annotations
from typing import List, Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .rest_router import RESTRouter


class RESTApplication:
    """Host REST API presentasi (composition-only)."""

    def __init__(self,
                 title: str = "SAM REST API",
                 version: str = "1.0",
                 description: str = "",
                 routers: Optional[List[RESTRouter]] = None) -> None:
        self._app = FastAPI(title=title, version=version, description=description)
        self._app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_methods=["*"],
            allow_headers=["*"],
        )
        self._routers: List[RESTRouter] = []
        if routers:
            for r in routers:
                self.register_router(r)

    # -- properties --
    @property
    def app(self) -> FastAPI:
        """FastAPI app bawaan (untuk uvicorn / test client)."""
        return self._app

    @property
    def routers(self) -> List[RESTRouter]:
        return list(self._routers)

    # -- registration --
    def register_router(self, router: RESTRouter) -> "RESTApplication":
        """Daftarkan RESTRouter ke aplikasi (composition-only)."""
        self._routers.append(router)
        self._app.include_router(router.router)
        return self

    def register_routers(self, routers: List[RESTRouter]) -> "RESTApplication":
        for r in routers:
            self.register_router(r)
        return self

    def openapi_paths(self) -> List[str]:
        """Path endpoint terdaftar (inspection)."""
        paths: List[str] = []
        for r in self._routers:
            paths.extend(r.paths())
        return paths
