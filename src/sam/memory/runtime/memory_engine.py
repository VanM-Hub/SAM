"""Memory Engine — engine runtime memori (Sprint 175).

Preview-only, deterministic.
"""
from __future__ import annotations
from dataclasses import dataclass

from .memory_runtime import MemoryRuntime, MemoryRunResult


@dataclass(frozen=True)
class MemoryEngineInfo:
    """Info engine memori (immutable)."""
    version: str
    preview_only: bool = True
    deterministic: bool = True


class MemoryEngine:
    """Engine memori. Preview-only facade."""

    VERSION = "1.0.0"

    def __init__(self, runtime: MemoryRuntime) -> None:
        self._runtime = runtime

    def info(self) -> MemoryEngineInfo:
        return MemoryEngineInfo(version=self.VERSION)

    def run(self, memory_id: str) -> MemoryRunResult:
        return self._runtime.run(memory_id)

    def health(self) -> bool:
        return True
