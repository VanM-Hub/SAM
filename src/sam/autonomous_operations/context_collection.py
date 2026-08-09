"""Operational Context Collection - WP-03 (MISSION-4.5 / IP-4.5-001).

Mengumpulkan seluruh konteks operasional yang relevan sebelum investigasi.
Context immutable, dapat ditelusuri, digunakan pada seluruh investigation.
"""
from __future__ import annotations

from typing import Any, Callable, Dict, Optional, Tuple

from .autonomous_investigation import ContextSnapshot


class ContextCollector:
    """Mengumpulkan konteks operasional (read-only)."""

    def __init__(self) -> None:
        self._probes: Dict[str, Callable[[], Dict[str, Any]]] = {}
        self._snapshots: Tuple[ContextSnapshot, ...] = ()

    def register_probe(
        self, category: str, key: str, fn: Callable[[], Dict[str, Any]]
    ) -> None:
        self._probes[f"{category}:{key}"] = (category, key, fn)

    def collect(self) -> ContextSnapshot:
        snapshot = ContextSnapshot()
        for _full, (category, key, fn) in self._probes.items():
            try:
                data = fn() or {}
            except Exception:
                data = {"error": "probe failed"}
            if category == "runtime":
                snapshot.add_runtime(key, data)
            elif category == "provider":
                snapshot.add_provider(key, data)
            elif category == "mission":
                snapshot.add_mission(key, data)
            elif category == "workflow":
                snapshot.add_workflow(key, data)
        self._snapshots += (snapshot,)
        return snapshot

    def all_snapshots(self) -> Tuple[ContextSnapshot, ...]:
        return self._snapshots

    def last_snapshot(self) -> Optional[ContextSnapshot]:
        return self._snapshots[-1] if self._snapshots else None
