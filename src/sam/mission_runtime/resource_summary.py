# Copyright 2026 VanM-Hub. Licensed under Apache-2.0.
"""Sprint 137 - Mission Resources: resource_summary.

Summarizes resources. Pure DTO, immutable.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class ResourceSummary:
    """Immutable summary of resources."""

    allocated_ids: Tuple[str, ...]
    total: int = 0
