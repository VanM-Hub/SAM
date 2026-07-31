"""RuntimeRegistry (Sprint 271).

Program D - Runtime Services & Deployment.
Registry runtime service level-akhir.
"""
from __future__ import annotations
from typing import Dict, List, Optional

from .runtime_service import RuntimeService


class RuntimeRegistry:
    """Registry runtime service (deterministic, read-only)."""

    def __init__(self) -> None:
        self._services: Dict[str, RuntimeService] = {}

    def register(self, service: RuntimeService) -> None:
        if service.name in self._services:
            raise ValueError(f"runtime already registered: {service.name}")
        self._services[service.name] = service

    def get(self, name: str) -> Optional[RuntimeService]:
        return self._services.get(name)

    def has(self, name: str) -> bool:
        return name in self._services

    def names(self) -> List[str]:
        return sorted(self._services.keys())

    def count(self) -> int:
        return len(self._services)

    def all_ready(self) -> bool:
        return all(s.is_initialized for s in self._services.values()) \
            if self._services else True
