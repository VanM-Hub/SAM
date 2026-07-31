"""Execution Registry (Sprint 250).

Program C - Real Execution Runtime.
Immutable registry of execution descriptors grouped by mode.
"""
from __future__ import annotations
from typing import Dict, List, Optional

from .execution_descriptor import ExecutionDescriptor


class ExecutionRegistry:
    """Registri deskriptor eksekusi. Read-only, no network."""

    def __init__(self) -> None:
        self._by_id: Dict[str, ExecutionDescriptor] = {}
        self._by_mode: Dict[str, List[str]] = {"preview": [], "execute": [], "rollback": []}

    def register(self, descriptor: ExecutionDescriptor) -> None:
        self._by_id[descriptor.id] = descriptor
        if descriptor.mode in self._by_mode and descriptor.id not in self._by_mode[descriptor.mode]:
            self._by_mode[descriptor.mode].append(descriptor.id)

    def get(self, execution_id: str) -> Optional[ExecutionDescriptor]:
        return self._by_id.get(execution_id)

    def by_mode(self, mode: str) -> List[ExecutionDescriptor]:
        return [self._by_id[i] for i in self._by_mode.get(mode, [])]

    def all(self) -> List[ExecutionDescriptor]:
        return list(self._by_id.values())

    def count(self) -> int:
        return len(self._by_id)
