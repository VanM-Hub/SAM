"""Dependency Injection (Sprint 265).

Program D - Runtime Services & Deployment.
Container: semua runtime dibuat melalui container, tidak instantiate manual.
"""
from __future__ import annotations
from typing import Any, Callable, List, Optional

from .provider_factory import ProviderFactory, ProviderRegistration
from .runtime_factory import RuntimeFactory, RuntimeRegistration
from .service_factory import ServiceFactory, ServiceRegistration
from .resolver import Resolver

DI_VERSION = "27.0.0"


class Container:
    """Container injeksi dependensi (sync, deterministic).

    Semua runtime/service/provider dibuat melalui container ini.
    Tidak boleh instantiate manual di luar container.
    """

    def __init__(self) -> None:
        self._resolver = Resolver()

    @property
    def resolver(self) -> Resolver:
        return self._resolver

    # Provider
    def register_provider(self, name: str, kind: str = "llm",
                          enabled: bool = True) -> None:
        self._resolver.register_provider(name, kind=kind, enabled=enabled)

    # Runtime
    def register_runtime(self, name: str, factory: Callable[[], Any]) -> None:
        self._resolver.register_runtime(name, factory)

    # Service
    def register_service(self, name: str, factory: Callable[..., Any],
                         dependencies: Optional[List[str]] = None) -> None:
        self._resolver.register_service(name, factory, dependencies=dependencies)

    # Resolve
    def get_provider_registration(self, name: str) -> ProviderRegistration:
        return self._resolver.providers.create(name)

    def get_runtime(self, name: str) -> Any:
        return self._resolver.runtimes.resolve(name)

    def get_service(self, name: str) -> Any:
        return self._resolver.services.resolve(name)

    def has_runtime(self, name: str) -> bool:
        return self._resolver.runtimes.has(name)

    def has_service(self, name: str) -> bool:
        return self._resolver.services.has(name)

    def runtime_names(self) -> list:
        return self._resolver.runtimes.names()
