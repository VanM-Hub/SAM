"""Artifact Runtime — representasi resmi seluruh keluaran pipeline SAM (Phase XXIII).

Representation only: TIDAK menyimpan, TIDAK mempublikasi, TIDAK mengeksekusi.
Sumber artifact deterministik berupa bentuk canonical hasil pipeline, tanpa IO.
"""
from ..artifact_runtime.foundation import (
    ArtifactDescriptor,
    ArtifactCapability,
    ArtifactContract,
    ArtifactMetadata,
    ArtifactRegistry,
)
from ..artifact_runtime.foundation.conversation_artifact import (
    ConversationArtifactBridge,
)
from ..artifact_runtime.foundation.dashboard_artifact import (
    DashboardArtifactBridge,
)

__all__ = [
    "ArtifactDescriptor",
    "ArtifactCapability",
    "ArtifactContract",
    "ArtifactMetadata",
    "ArtifactRegistry",
    "ConversationArtifactBridge",
    "DashboardArtifactBridge",
]
