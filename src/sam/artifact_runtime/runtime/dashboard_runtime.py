"""Dashboard Runtime Bridge — 5 PolicyCards (Sprint 223)."""
from __future__ import annotations

from ..dashboard import PolicyCard


class DashboardRuntimeBridge:
    """Bridge dashboard — 5 kartu runtime artifact."""

    def cards(self):
        return [
            PolicyCard("ar.runtime", "artifact", "ready",
                       "ArtifactRuntime preview-only", "runtime", "ready"),
            PolicyCard("ar.pipeline", "artifact", "ready",
                       "Desc->Artifact->Builder->Preview",
                       "runtime", "ready"),
            PolicyCard("ar.engine", "artifact", "ready",
                       "not LLM / not AI", "runtime", "ready"),
            PolicyCard("ar.summary", "artifact", "ready",
                       "read-only summary", "runtime", "ready"),
            PolicyCard("ar.stats", "artifact", "ready",
                       "external_calls=0", "runtime", "ready"),
        ]
