"""Dashboard Builder Bridge — 5 PolicyCards (Sprint 222)."""
from __future__ import annotations

from ..dashboard import PolicyCard


class DashboardBuilderBridge:
    """Bridge dashboard — 5 kartu builder artifact."""

    def cards(self):
        return [
            PolicyCard("ab.build", "artifact", "ready",
                       "ArtifactBuilder compose DTO", "builder", "ready"),
            PolicyCard("ab.manifest", "artifact", "ready",
                       "ManifestBuilder no storage", "builder", "ready"),
            PolicyCard("ab.reference", "artifact", "ready",
                       "ReferenceBuilder traceable", "builder", "ready"),
            PolicyCard("ab.metadata", "artifact", "ready",
                       "MetadataBuilder immutable", "builder", "ready"),
            PolicyCard("ab.preview", "artifact", "ready",
                       "build-only no file write", "builder", "ready"),
        ]
