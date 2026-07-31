"""ServerRuntime (Sprint 268).

Program D - Runtime Services & Deployment.
Menggabungkan Runtime + Connector + Provider + Execution.
Internal server — belum HTTP listening.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Optional

from ..lifecycle.runtime import LifecycleRuntime


@dataclass(frozen=True)
class ComponentStatus:
    """Status komponen server (immutable)."""
    name: str
    ready: bool = False
    detail: str = ""


class ServerRuntime:
    """Server runtime (sync, deterministic, local-only)."""

    def __init__(self, name: str = "sam-server",
                 layers: Optional[tuple] = None) -> None:
        self._name = name
        self._layers = layers or ("runtime", "connector",
                                  "provider", "execution")
        self._lifecycle = LifecycleRuntime()
        self._components: Dict[str, ComponentStatus] = {}
        self._started = False

    @property
    def name(self) -> str:
        return self._name

    @property
    def layers(self) -> tuple:
        return self._layers

    @property
    def status(self) -> str:
        return self._lifecycle.status

    @property
    def started(self) -> bool:
        return self._started

    def set_started(self, value: bool) -> None:
        self._started = value

    def register_component(self, name: str) -> None:
        if name in self._components:
            raise ValueError(f"component already registered: {name}")
        self._components[name] = ComponentStatus(name=name)

    def mark_ready(self, name: str, detail: str = "") -> None:
        if name not in self._components:
            raise KeyError(f"component not registered: {name}")
        self._components[name] = ComponentStatus(
            name=name, ready=True, detail=detail
        )

    def components(self) -> List[ComponentStatus]:
        return [self._components[k] for k in sorted(self._components)]

    def all_ready(self) -> bool:
        return all(c.ready for c in self._components.values()) \
            if self._components else True
