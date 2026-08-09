"""Citizen, Runtime & Provider Explorers - WP-03/04/05 (MISSION-4.6 / IP-4.6-001).

Eksplorasi seluruh Citizen / Runtime / Provider secara read-only. Explorer
tidak melakukan mutation; hanya mengonsumsi capability via API (views).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Optional, Tuple


# ---------------------------------------------------------------------------
# WP-03 Citizen Explorer
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class CitizenInfo:
    """Informasi satu Citizen."""

    citizen_id: str
    name: str = ""
    type: str = "capability"
    capabilities: Tuple[str, ...] = field(default_factory=tuple)
    health: str = "unknown"

    def as_dict(self) -> dict:
        return {
            "citizen_id": self.citizen_id,
            "name": self.name,
            "type": self.type,
            "capabilities": list(self.capabilities),
            "health": self.health,
        }


class CitizenExplorer:
    """Eksplorasi Citizen (read-only, discovery view)."""

    def __init__(self) -> None:
        self._citizens: Dict[str, CitizenInfo] = {}

    def register(self, info: CitizenInfo) -> None:
        self._citizens[info.citizen_id] = info

    def discover(self) -> Tuple[Dict[str, Any], ...]:
        return tuple(c.as_dict() for c in self._citizens.values())

    def detail(self, citizen_id: str) -> Optional[Dict[str, Any]]:
        c = self._citizens.get(citizen_id)
        return c.as_dict() if c else None

    def relationships(self, citizen_id: str) -> Dict[str, Any]:
        return {
            "citizen_id": citizen_id,
            "known_peers": list(self._citizens.keys()),
            "read_only": True,
        }

    def health_view(self) -> Dict[str, Any]:
        return {
            "total": len(self._citizens),
            "by_health": {
                h: sum(1 for c in self._citizens.values() if c.health == h)
                for h in ("healthy", "degraded", "unknown", "critical")
            },
        }


# ---------------------------------------------------------------------------
# WP-04 Runtime Explorer
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class RuntimeView:
    """Tampilan satu runtime."""

    runtime_id: str
    name: str = ""
    status: str = "unknown"
    health: str = "unknown"
    dependencies: Tuple[str, ...] = field(default_factory=tuple)
    metrics: Dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict:
        return {
            "runtime_id": self.runtime_id,
            "name": self.name,
            "status": self.status,
            "health": self.health,
            "dependencies": list(self.dependencies),
            "metrics": self.metrics,
        }


class RuntimeExplorer:
    """Eksplorasi Runtime (observasional, tanpa mutation)."""

    def __init__(self) -> None:
        self._registry: Dict[str, Callable[[], RuntimeView]] = {}

    def register(self, runtime_id: str, fn: Callable[[], RuntimeView]) -> None:
        self._registry[runtime_id] = fn

    def observe(self, runtime_id: str) -> Optional[Dict[str, Any]]:
        fn = self._registry.get(runtime_id)
        if fn is None:
            return None
        return fn().as_dict()

    def topology(self) -> Tuple[Dict[str, Any], ...]:
        return tuple(
            fn().as_dict() for fn in self._registry.values()
        )

    def dependency_map(self) -> Dict[str, Tuple[str, ...]]:
        return {
            rid: fn().dependencies for rid, fn in self._registry.items()
        }


# ---------------------------------------------------------------------------
# WP-05 Provider Explorer
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ProviderView:
    """Tampilan satu provider."""

    provider_id: str
    name: str = ""
    status: str = "unknown"
    health: str = "unknown"
    capabilities: Tuple[str, ...] = field(default_factory=tuple)
    metrics: Dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict:
        return {
            "provider_id": self.provider_id,
            "name": self.name,
            "status": self.status,
            "health": self.health,
            "capabilities": list(self.capabilities),
            "metrics": self.metrics,
        }


class ProviderExplorer:
    """Eksplorasi Provider (observasional)."""

    def __init__(self) -> None:
        self._registry: Dict[str, Callable[[], ProviderView]] = {}

    def register(self, provider_id: str, fn: Callable[[], ProviderView]) -> None:
        self._registry[provider_id] = fn

    def observe(self, provider_id: str) -> Optional[Dict[str, Any]]:
        fn = self._registry.get(provider_id)
        if fn is None:
            return None
        return fn().as_dict()

    def all(self) -> Tuple[Dict[str, Any], ...]:
        return tuple(fn().as_dict() for fn in self._registry.values())
