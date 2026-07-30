"""Runtime Descriptor — deskripsi subsystem."""
from __future__ import annotations
from typing import Dict, List
from sam.runtime_kernel.runtime_registry import RuntimeDescriptor


class DescriptorEngine:
    """Engine deskriptor — preview-only."""

    def __init__(self) -> None:
        self._descriptors: Dict[str, RuntimeDescriptor] = {}

    def create(self, descriptor_id: str, subsystem: str, runtime_type: str,
               capabilities: List[str] = None) -> RuntimeDescriptor:
        d = RuntimeDescriptor(
            descriptor_id=descriptor_id,
            subsystem=subsystem,
            runtime_type=runtime_type,
            capabilities=capabilities or [],
        )
        self._descriptors[descriptor_id] = d
        return d

    def get(self, descriptor_id: str) -> RuntimeDescriptor | None:
        return self._descriptors.get(descriptor_id)

    def count(self) -> int:
        return len(self._descriptors)
