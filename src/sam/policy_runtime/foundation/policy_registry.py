"""Policy Registry — registri policy (Sprint 204)."""
from __future__ import annotations
from typing import Dict, List

from .policy_descriptor import PolicyDescriptor
from .policy_capability import PolicyCapability


class PolicyRegistry:
    """Registri policy. Register/attach hanya komposisi in-memory (no write)."""

    def __init__(self) -> None:
        self._descriptors: Dict[str, PolicyDescriptor] = {}
        self._capabilities: Dict[str, List[PolicyCapability]] = {}

    def register(self, descriptor: PolicyDescriptor) -> None:
        self._descriptors[descriptor.id] = descriptor

    def attach_capability(self, capability: PolicyCapability) -> None:
        self._capabilities.setdefault(capability.owner_id, []).append(capability)

    def get(self, policy_id: str) -> PolicyDescriptor | None:
        return self._descriptors.get(policy_id)

    def exists(self, policy_id: str) -> bool:
        return policy_id in self._descriptors

    def all(self) -> List[PolicyDescriptor]:
        return list(self._descriptors.values())

    def count(self) -> int:
        return len(self._descriptors)

    def capabilities(self, policy_id: str) -> List[PolicyCapability]:
        return list(self._capabilities.get(policy_id, []))
