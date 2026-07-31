# Copyright 2026 VanM-Hub. Licensed under Apache-2.0.
"""Sprint 130 - Synchronization: sync_summary.

Summarizes a sync snapshot. Pure DTO, immutable.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class SyncSummary:
    """Immutable summary of a synchronization."""

    sync_id: str
    runtimes: Tuple[str, ...]
    synchronized: int = 0
    total: int = 0
