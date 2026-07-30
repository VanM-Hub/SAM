"""Runtime Manifest — manifest subsystem."""
from __future__ import annotations
from typing import Dict
from sam.runtime_kernel.runtime_registry import RuntimeManifest


class ManifestEngine:
    """Engine manifest — preview-only."""

    def __init__(self) -> None:
        self._manifests: Dict[str, RuntimeManifest] = {}

    def create(self, manifest_id: str, runtime_name: str, version: str,
               dependencies: Dict[str, str] = None) -> RuntimeManifest:
        m = RuntimeManifest(
            manifest_id=manifest_id,
            runtime_name=runtime_name,
            version=version,
            dependencies=dependencies or {},
        )
        self._manifests[manifest_id] = m
        return m

    def get(self, manifest_id: str) -> RuntimeManifest | None:
        return self._manifests.get(manifest_id)

    def count(self) -> int:
        return len(self._manifests)
