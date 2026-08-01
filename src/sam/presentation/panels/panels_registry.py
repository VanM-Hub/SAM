"""Sprint 274 - Desktop Panels: registry 10 panel (metadata-only)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

from .panel_model import PanelModel


@dataclass(frozen=True)
class PanelsRegistry:
    """Registri deklaratif panel yang dikenal Presentation Layer."""

    _panels: Tuple[PanelModel, ...] = ()

    def register(self, model: PanelModel) -> "PanelsRegistry":
        return PanelsRegistry(self._panels + (model,))

    def register_all(self, models: Tuple[PanelModel, ...]) -> "PanelsRegistry":
        return PanelsRegistry(self._panels + tuple(models))

    @property
    def panels(self) -> Tuple[PanelModel, ...]:
        return self._panels

    @property
    def names(self) -> Tuple[str, ...]:
        return tuple(p.name for p in self._panels)

    def get(self, name: str):
        for p in self._panels:
            if p.name == name:
                return p
        return None

    def __len__(self) -> int:
        return len(self._panels)

    def as_dict(self) -> dict:
        return {"panels": [p.as_dict() for p in self._panels]}


def default_panels() -> Tuple[PanelModel, ...]:
    """Sepuluh panel standar Presentation Layer (semua read-only)."""
    return (
        PanelModel(name="Mission", source_runtime="Mission Runtime"),
        PanelModel(name="Runtime", source_runtime="Runtime Kernel"),
        PanelModel(name="Memory", source_runtime="Memory Runtime"),
        PanelModel(name="Knowledge", source_runtime="Knowledge Runtime"),
        PanelModel(name="Workflow", source_runtime="Workflow Runtime"),
        PanelModel(name="Policy", source_runtime="Policy Runtime"),
        PanelModel(name="Audit", source_runtime="Audit Runtime"),
        PanelModel(name="Artifact", source_runtime="Artifact Runtime"),
        PanelModel(name="Provider", source_runtime="Provider Runtime"),
        PanelModel(name="Execution", source_runtime="Execution Runtime"),
    )
