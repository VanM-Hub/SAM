# Copyright 2026 VanM-Hub. Licensed under Apache-2.0.
"""Sprint 130 - Synchronization: sync_request.

Request to synchronize runtimes. Pure DTO, immutable.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Tuple


@dataclass(frozen=True)
class SyncRequest:
    """Immutable request describing what to synchronize."""

    sync_id: str
    runtimes: Tuple[str, ...] = field(default_factory=tuple)
    deterministic: bool = True
