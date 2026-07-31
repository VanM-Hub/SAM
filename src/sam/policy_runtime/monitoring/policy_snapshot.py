"""Policy Snapshot — snapshot policy (Sprint 209)."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict

from ..foundation.policy_registry import PolicyRegistry


@dataclass(frozen=True)
class PolicySnapshot:
    """Snapshot policy (immutable)."""
    total: int = 0
    category_counts: Dict[str, int] = field(default_factory=dict)


class PolicySnapshotter:
    """Snapshotter policy. Read-only."""

    def __init__(self, registry: PolicyRegistry) -> None:
        self._registry = registry

    def snapshot(self) -> PolicySnapshot:
        descs = self._registry.all()
        counts = {}
        for d in descs:
            counts[d.category] = counts.get(d.category, 0) + 1
        return PolicySnapshot(total=len(descs), category_counts=counts)
