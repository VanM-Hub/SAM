"""Model Registry — registri unit model (Sprint 239).

Program B — Model Runtime Integration.
Register/attach hanya komposisi in-memory — tidak ada penyimpanan eksternal.
"""
from __future__ import annotations
from typing import Dict, List

from .model_descriptor import ModelDescriptor
from .model_capability import ModelCapability


class ModelRegistry:
    """Registri model. In-memory, no write to disk/network."""

    def __init__(self) -> None:
        self._descriptors: Dict[str, ModelDescriptor] = {}
        self._capabilities: Dict[str, List[ModelCapability]] = {}

    def register(self, descriptor: ModelDescriptor) -> None:
        self._descriptors[descriptor.id] = descriptor

    def attach_capability(self, capability: ModelCapability) -> None:
        self._capabilities.setdefault(capability.owner_id, []).append(capability)

    def get(self, model_id: str) -> ModelDescriptor | None:
        return self._descriptors.get(model_id)

    def get_by_name(self, name: str) -> ModelDescriptor | None:
        for descriptor in self._descriptors.values():
            if descriptor.name == name:
                return descriptor
        return None

    def exists(self, model_id: str) -> bool:
        return model_id in self._descriptors

    def all(self) -> List[ModelDescriptor]:
        return list(self._descriptors.values())

    def count(self) -> int:
        return len(self._descriptors)

    def capabilities(self, model_id: str) -> List[ModelCapability]:
        return list(self._capabilities.get(model_id, []))

    def clear(self) -> None:
        self._descriptors.clear()
        self._capabilities.clear()
