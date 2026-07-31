"""ServiceFactory (Sprint 265).

Program D - Runtime Services & Deployment.
Factory untuk membuat service instances via container.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Callable, Dict, List


@dataclass(frozen=True)
class ServiceRegistration:
    """Registrasi service (immutable)."""
    name: str
    factory: Callable[..., object]
    dependencies: List[str] = field(default_factory=list)


class ServiceFactory:
    """Factory service (sync, deterministic)."""

    def __init__(self) -> None:
        self._registry: Dict[str, ServiceRegistration] = {}
        self._instances: Dict[str, object] = {}

    def register(self, name: str, factory: Callable[..., object],
                 dependencies: List[str] = None) -> None:
        self._registry[name] = ServiceRegistration(
            name=name, factory=factory,
            dependencies=list(dependencies or []),
        )

    def resolve(self, name: str) -> object:
        if name in self._instances:
            return self._instances[name]
        reg = self._registry.get(name)
        if reg is None:
            raise KeyError(f"service not registered: {name}")
        deps = [self.resolve(d) for d in reg.dependencies]
        instance = reg.factory(*deps)
        self._instances[name] = instance
        return instance

    def has(self, name: str) -> bool:
        return name in self._registry

    def names(self) -> list:
        return sorted(self._registry.keys())
