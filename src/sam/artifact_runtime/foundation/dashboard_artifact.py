"""Dashboard Artifact Bridge — 5 PolicyCards (Sprint 220)."""
from __future__ import annotations

from ..dashboard import PolicyCard
from .artifact_registry import ArtifactRegistry


class DashboardArtifactBridge:
    """Bridge dashboard — 5 kartu fondasi artifact."""

    def __init__(self, registry: ArtifactRegistry) -> None:
        self._registry = registry

    def cards(self):
        n = self._registry.count()
        return [
            PolicyCard("af.descriptors", "artifact", "ready",
                       f"{n} descriptor(s)", "registry", "ready"),
            PolicyCard("af.immutable", "artifact", "ready",
                       "immutable artifact model", "foundation", "ready"),
            PolicyCard("af.preview", "artifact", "ready",
                       "no storage / no publish / no execute",
                       "foundation", "ready"),
            PolicyCard("af.deterministic", "artifact", "ready",
                       "deterministic representation",
                       "foundation", "ready"),
            PolicyCard("af.traceable", "artifact", "ready",
                       "provenance traceable end-to-end",
                       "foundation", "ready"),
        ]
