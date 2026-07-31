# Copyright 2026 VanM-Hub. Licensed under Apache-2.0.
"""Sprint 135 - Mission Definition: mission_metadata.

Metadata for a mission. Pure DTO, immutable.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict


@dataclass(frozen=True)
class MissionMetadata:
    """Immutable metadata describing a mission."""

    mission_id: str
    owner: str = "system"
    version: str = "1.0.0"
    labels: Dict[str, str] = field(default_factory=dict)
