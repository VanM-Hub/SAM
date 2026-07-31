# Copyright 2026 VanM-Hub. Licensed under Apache-2.0.
"""Sprint 135 - Mission Definition: mission_scope.

Scope of a mission. Pure DTO, immutable.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Tuple


@dataclass(frozen=True)
class MissionScope:
    """Immutable boundary of a mission."""

    domain: str = "default"
    modules: Tuple[str, ...] = field(default_factory=tuple)
    excluded: Tuple[str, ...] = field(default_factory=tuple)
