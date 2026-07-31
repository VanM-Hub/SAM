"""Runtime Registry — registri runtime untuk integrasi (Sprint 249).

Program B — Model Runtime Integration.
Registri read-only dari runtime yang diintegrasikan. Immutable view, no-network.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from .model_runtime import ModelRuntime
from .model_certifier import ModelCertifier

RUNTIME_PIPELINE_ORDER = (
    "mission",
    "agent",
    "workflow",
    "memory",
    "knowledge",
    "cognitive",
    "policy",
    "audit",
    "artifact",
    "connector",
    "provider",
    "model",
    "execution_preview",
)


@dataclass(frozen=True)
class RuntimeEntry:
    """Entri runtime (immutable)."""
    name: str
    kind: str = "model"
    bridge: str = "read-only"
    external_calls: int = 0

    def as_dict(self) -> dict:
        return {
            "name": self.name,
            "kind": self.kind,
            "bridge": self.bridge,
            "external_calls": self.external_calls,
        }


class RuntimeRegistry:
    """Registri runtime. Read-only bridge ke komponen lain."""

    def __init__(self, pipeline_order: tuple = RUNTIME_PIPELINE_ORDER) -> None:
        self._order = tuple(pipeline_order)
        self._entries: Dict[str, RuntimeEntry] = {}
        self._model_runtime: Optional[ModelRuntime] = None
        self._certifier: Optional[ModelCertifier] = None

    def register(self, entry: RuntimeEntry) -> None:
        self._entries[entry.name] = entry

    def register_model_runtime(self, runtime: ModelRuntime) -> None:
        self._model_runtime = runtime
        self.register(RuntimeEntry(name="model", kind="runtime",
                                   bridge="read-only", external_calls=0))

    def order(self) -> List[str]:
        return list(self._order)

    def entry(self, name: str) -> Optional[RuntimeEntry]:
        return self._entries.get(name)

    def all(self) -> List[RuntimeEntry]:
        return [self._entries.get(n) for n in self._order if n in self._entries]

    def model_runtime(self) -> Optional[ModelRuntime]:
        return self._model_runtime

    def certifier(self) -> ModelCertifier:
        if self._certifier is None:
            self._certifier = ModelCertifier()
        return self._certifier
