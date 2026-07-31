"""Dashboard Model Bridge — 5 PolicyCards (Sprint 221)."""
from __future__ import annotations

from ..dashboard import PolicyCard


class DashboardModelBridge:
    """Bridge dashboard — 5 kartu model artifact."""

    def cards(self):
        return [
            PolicyCard("am.artifact", "artifact", "ready",
                       "immutable Artifact DTO", "model", "ready"),
            PolicyCard("am.reference", "artifact", "ready",
                       "ArtifactReference traceable", "model", "ready"),
            PolicyCard("am.manifest", "artifact", "ready",
                       "ArtifactManifest read-only", "model", "ready"),
            PolicyCard("am.metadata", "artifact", "ready",
                       "ArtifactMetadata immutable", "model", "ready"),
            PolicyCard("am.validator", "artifact", "ready",
                       "ArtifactValidator deterministic", "model", "ready"),
        ]
