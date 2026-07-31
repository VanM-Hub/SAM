"""Sprint 266 - Monitoring: history (riwayat metrik immutable)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

from .metrics import RuntimeMetrics


@dataclass(frozen=True)
class RuntimeHistory:
    """Riwayat counter metrik (append-only, immutable)."""

    _entries: Tuple[RuntimeMetrics, ...] = ()

    def record(self, metrics: RuntimeMetrics) -> "RuntimeHistory":
        return RuntimeHistory(_entries=self._entries + (metrics,))

    @property
    def entries(self) -> Tuple[RuntimeMetrics, ...]:
        return self._entries

    def __len__(self) -> int:
        return len(self._entries)

    def last(self) -> RuntimeMetrics:
        if not self._entries:
            return RuntimeMetrics()
        return self._entries[-1]
