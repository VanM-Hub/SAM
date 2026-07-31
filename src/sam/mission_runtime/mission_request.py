# Copyright 2026 VanM-Hub. Licensed under Apache-2.0.
"""Sprint 134 - Mission Foundation: mission_request.

A request to open/manage a mission. Pure DTO, immutable.
Carries intent; does not perform anything.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass(frozen=True)
class MissionRequest:
    """Immutable request to operate on a mission."""

    mission_id: str
    intent: str = "open"  # open | extend | close
    source_runtime: str = "unknown"
    parent: Optional[str] = None
    parameters: Dict[str, object] = field(default_factory=dict)

    @property
    def is_lifecycle_managed(self) -> bool:
        """Mission runtime manages lifecycle only (always True)."""
        return True
