"""Model Manifest — manifes model (Sprint 248).

Program B — Model Runtime Integration.
Manifes untuk sertifikasi. Immutable, deterministik.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List

from .model_descriptor import ModelDescriptor
from .model_contract import ModelContract
from .model_metadata import ModelMetadata


@dataclass(frozen=True)
class ModelManifest:
    """Manifes model (immutable). Holds signature data for certification."""
    manifest_id: str
    descriptor: ModelDescriptor
    contract: ModelContract
    metadata: ModelMetadata
    integrity_extra: Dict[str, object] = field(default_factory=dict)

    def as_dict(self) -> dict:
        return {
            "manifest_id": self.manifest_id,
            "descriptor": self.descriptor.as_dict(),
            "contract": self.contract.as_dict(),
            "metadata": self.metadata.as_dict(),
            "integrity_extra": dict(self.integrity_extra),
        }
