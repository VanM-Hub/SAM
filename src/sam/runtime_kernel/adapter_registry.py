"""Adapter Registry — registri adapter subsystem."""
from __future__ import annotations
from typing import Dict, List, Optional
from sam.runtime_kernel.runtime_adapter import SubsystemAdapter


class AdapterRegistry:
    """Registry adapter — preview-only."""

    def __init__(self) -> None:
        self._adapters: Dict[str, SubsystemAdapter] = {}

    def register(self, adapter: SubsystemAdapter) -> None:
        self._adapters[adapter.adapter_id] = adapter

    def get(self, adapter_id: str) -> SubsystemAdapter | None:
        return self._adapters.get(adapter_id)

    def list_all(self) -> List[SubsystemAdapter]:
        return list(self._adapters.values())

    def count(self) -> int:
        return len(self._adapters)

    def find_by_subsystem(self, name: str) -> List[SubsystemAdapter]:
        return [a for a in self._adapters.values() if a.subsystem_name == name]
