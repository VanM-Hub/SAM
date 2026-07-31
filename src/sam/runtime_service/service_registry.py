"""RuntimeServiceRegistry (Sprint 261).

Program D - Runtime Services & Deployment.
Registry of runtime services (immutable entries, deterministic lookup).
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Optional

from .descriptor import RuntimeServiceDescriptor


@dataclass(frozen=True)
class RegisteredService:
    """Entri registry (immutable)."""
    descriptor: RuntimeServiceDescriptor
    enabled: bool = True
    order: int = 0


class RuntimeServiceRegistry:
    """Registry service runtime. Deterministic, read-only."""

    def __init__(self) -> None:
        self._services: Dict[str, RegisteredService] = {}

    def register(self, descriptor: RuntimeServiceDescriptor,
                 enabled: bool = True, order: int = 0) -> None:
        if descriptor.name in self._services:
            raise ValueError(f"service already registered: {descriptor.name}")
        self._services[descriptor.name] = RegisteredService(
            descriptor=descriptor, enabled=enabled, order=order
        )

    def get(self, name: str) -> Optional[RuntimeServiceDescriptor]:
        entry = self._services.get(name)
        return entry.descriptor if entry else None

    def has(self, name: str) -> bool:
        return name in self._services

    def list(self) -> List[RuntimeServiceDescriptor]:
        entries = sorted(self._services.values(), key=lambda e: (e.order, e.descriptor.name))
        return [e.descriptor for e in entries if e.enabled]

    def count(self) -> int:
        return len(self._services)

    def names(self) -> List[str]:
        return [d.name for d in self.list()]
