"""Timeline — frozen DTO timeline eksekusi."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple


@dataclass(frozen=True)
class TimelineEvent:
    """Event dalam timeline."""
    event_id: str
    timestamp: float
    event_type: str
    description: str = ""
    candidate_ids: Tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class Timeline:
    """Timeline eksekusi."""
    timeline_id: str
    execution_order_id: str
    events: Tuple[TimelineEvent, ...] = field(default_factory=tuple)
    total_events: int = 0
    start_time: float = 0.0
    end_time: float = 0.0
    estimated_duration: float = 0.0


@dataclass(frozen=True)
class ExecutionWindow:
    """Window waktu eksekusi."""
    window_id: str
    timeline_id: str
    start_time: float
    end_time: float
    candidate_ids: Tuple[str, ...] = field(default_factory=tuple)
    window_type: str = "execution"


@dataclass(frozen=True)
class Milestone:
    """Milestone dalam eksekusi."""
    milestone_id: str
    timestamp: float
    name: str
    description: str = ""
    milestone_type: str = "checkpoint"


@dataclass(frozen=True)
class TimelineSnapshot:
    """Snapshot timeline."""
    timeline_id: str
    total_events: int = 0
    total_windows: int = 0
    total_milestones: int = 0
    estimated_duration: float = 0.0
    status: str = "pending"
