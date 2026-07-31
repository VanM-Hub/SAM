# Copyright 2026 VanM-Hub. Licensed under Apache-2.0.
"""Sprint 132 - Runtime Engine: runtime_status.

Status of the orchestration engine. Pure DTO, immutable.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RuntimeStatus:
    """Immutable status of the orchestration runtime engine."""

    state: str = "ready"

    @property
    def is_ready(self) -> bool:
        return self.state == "ready"
