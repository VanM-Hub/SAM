"""ArtifactRuntimeManifest — manifest runtime terintegrasi (immutable)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class ArtifactRuntimeManifest:
    """Manifest integrasi Artifact Runtime. Immutable & read-only."""
    version: str = "23.0.0"
    phase: str = "XXIII"
    integrated_runtimes: Tuple[str, ...] = (
        "mission", "agent", "skill", "workflow", "policy", "audit",
        "memory", "knowledge", "cognitive", "orchestrator", "connector",
        "provider",
    )
    preview_only: bool = True
    no_storage: bool = True
    no_publish: bool = True
    immutable: bool = True
    no_execute: bool = True
    external_calls: int = 0
