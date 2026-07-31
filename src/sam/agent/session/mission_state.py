"""Mission State — state mission (immutable DTO, Sprint 157).

State mission mengikuti lifecycle yang disediakan state machine (Sprint 158).
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional


@dataclass(frozen=True)
class MissionState:
    """State mission (immutable)."""
    mission_id: str
    state: str = "Created"  # Created|Preparing|Running|Waiting|Completed|Cancelled|Failed
    detail: str = ""
    parent_state: Optional[str] = None
