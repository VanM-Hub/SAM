# Copyright 2026 VanM-Hub. Licensed under Apache-2.0.
"""Sprint 124 - Runtime Discovery: runtime_descriptor.

Describes a discovered runtime so SAM knows it exists. Pure DTO.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Tuple


@dataclass(frozen=True)
class RuntimeDescriptor:
    """Immutable description of a runtime known to the orchestrator."""

    runtime_id: str
    name: str
    version: str = "0.0.0"
    pipeline_position: int = 0
    tags: Tuple[str, ...] = field(default_factory=tuple)

    @property
    def is_discovered(self) -> bool:
        return bool(self.runtime_id)
