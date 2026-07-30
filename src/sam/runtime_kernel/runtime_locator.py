"""Runtime Locator — locator subsystem."""
from __future__ import annotations
from typing import Dict, List
from sam.runtime_kernel.runtime_registry import LocatorResult


class RuntimeLocator:
    """Locator subsystem — preview-only."""

    def __init__(self) -> None:
        self._targets: Dict[str, List[str]] = {}

    def register_target(self, target: str, entries: List[str]) -> None:
        self._targets[target] = entries

    def locate(self, locator_id: str, target: str) -> LocatorResult:
        entries = self._targets.get(target, [])
        return LocatorResult(
            locator_id=locator_id,
            target=target,
            found=len(entries) > 0,
            entries=entries,
        )

    def list_targets(self) -> List[str]:
        return list(self._targets.keys())
