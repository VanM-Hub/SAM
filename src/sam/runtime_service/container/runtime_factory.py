"""RuntimeFactory (Sprint 265).

Program D - Runtime Services & Deployment.
Factory untuk membuat runtime instances via container.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Callable, Dict


@dataclass(frozen=True)
class RuntimeRegistration:
    """Registrasi runtime factory (immutable)."""
    name: str
    factory: Callable[[], object]
    singleton: bool = True


class RuntimeFactory:
    """Factory runtime (sync, deterministic)."""

    def __init__(self) -> None:
        self._registry: Dict[str, RuntimeRegistration] = {}
        self._instances: Dict[str, object] = {}

    def register(self, name: str, factory: Callable[[], object],
                 singleton: bool = True) -> None:
        self._registry[name] = RuntimeRegistration(
            name=name, factory=factory, singleton=singleton
        )

    def _make(self, reg: RuntimeRegistration) -> object:
        if reg.singleton and reg.name in self._instances:
            return self._instances[reg.name]
        instance = reg.factory()
        if reg.singleton:
            self._instances[reg.name] = instance
        return instance

    def resolve(self, name: str) -> object:
        reg = self._registry.get(name)
        if reg is None:
            raise KeyError(f"runtime not registered: {name}")
        return self._make(reg)

    def has(self, name: str) -> bool:
        return name in self._registry

    def names(self) -> list:
        return sorted(self._registry.keys())
