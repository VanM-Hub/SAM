"""Resolver (Sprint 265).

Program D - Runtime Services & Deployment.
Gabungkan provider + runtime + service factory jadi satu resolver/container inti.
"""
from __future__ import annotations
from typing import TypeVar

from .provider_factory import ProviderFactory
from .runtime_factory import RuntimeFactory
from .service_factory import ServiceFactory

T = TypeVar("T")


class Resolver:
    """Resolver gabungan (sync, deterministic)."""

    def __init__(self) -> None:
        self._providers = ProviderFactory()
        self._runtimes = RuntimeFactory()
        self._services = ServiceFactory()

    @property
    def providers(self) -> ProviderFactory:
        return self._providers

    @property
    def runtimes(self) -> RuntimeFactory:
        return self._runtimes

    @property
    def services(self) -> ServiceFactory:
        return self._services

    def register_provider(self, name: str, **kw) -> None:
        self._providers.register(name, **kw)

    def register_runtime(self, name: str, factory) -> None:
        self._runtimes.register(name, factory)

    def register_service(self, name: str, factory,
                         dependencies: list = None) -> None:
        self._services.register(name, factory, dependencies=dependencies)

    def resolve(self, kind: str, name: str) -> object:
        if kind == "provider":
            return self._providers.create(name)
        if kind == "runtime":
            return self._runtimes.resolve(name)
        if kind == "service":
            return self._services.resolve(name)
        raise ValueError(f"unknown kind: {kind}")
