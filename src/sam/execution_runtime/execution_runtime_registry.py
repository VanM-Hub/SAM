"""Execution Integration - Runtime Registry (Sprint 259).

Program C - Real Execution Runtime.
Registri runtime yang diintegrasikan ke pipeline akhir. Read-only view.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from .execution_runtime import ExecutionRuntime
from .execution_certifier import ExecutionCertifier

PIPELINE_ORDER = (
    "mission", "workflow", "policy", "memory", "knowledge", "cognitive",
    "orchestrator", "connector", "provider", "model_runtime", "approval",
    "execution_runtime", "artifact",
)


@dataclass(frozen=True)
class RuntimeEntry:
    """Entri runtime (immutable)."""
    name: str
    kind: str = "runtime"
    bridge: str = "read-only"
    external_calls: int = 0

    def as_dict(self) -> dict:
        return {"name": self.name, "kind": self.kind,
                "bridge": self.bridge, "external_calls": self.external_calls}


class ExecutionRuntimeRegistry:
    """Registri runtime pipeline akhir. Read-only."""

    def __init__(self, pipeline_order: tuple = PIPELINE_ORDER) -> None:
        self._order = tuple(pipeline_order)
        self._entries: Dict[str, RuntimeEntry] = {}
        self._execution_runtime: Optional[ExecutionRuntime] = None
        self._certifier: Optional[ExecutionCertifier] = None

    def register(self, entry: RuntimeEntry) -> None:
        self._entries[entry.name] = entry

    def register_execution_runtime(self, runtime: ExecutionRuntime) -> None:
        self._execution_runtime = runtime
        self.register(RuntimeEntry(name="execution_runtime", kind="execution",
                                   bridge="read-only", external_calls=0))

    def order(self) -> List[str]:
        return list(self._order)

    def entry(self, name: str) -> Optional[RuntimeEntry]:
        return self._entries.get(name)

    def all(self) -> List[RuntimeEntry]:
        return [self._entries[n] for n in self._order if n in self._entries]

    def execution_runtime(self) -> Optional[ExecutionRuntime]:
        return self._execution_runtime

    def certifier(self) -> ExecutionCertifier:
        if self._certifier is None:
            self._certifier = ExecutionCertifier()
        return self._certifier
