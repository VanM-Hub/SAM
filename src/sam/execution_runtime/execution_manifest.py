"""Execution Manifest (Sprint 258).

Program C - Real Execution Runtime.
Manifest immutable yang menjadi bahan sertifikasi.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict

from .execution_descriptor import ExecutionDescriptor
from .execution_contract import ExecutionContract
from .execution_metadata import ExecutionMetadata


@dataclass(frozen=True)
class ExecutionManifest:
    """Manifest eksekusi (immutable)."""
    manifest_id: str
    descriptor: ExecutionDescriptor
    contract: ExecutionContract
    metadata: ExecutionMetadata

    def as_dict(self) -> dict:
        return {"manifest_id": self.manifest_id,
                "descriptor": self.descriptor.as_dict(),
                "contract": self.contract.as_dict(),
                "metadata": self.metadata.as_dict()}
