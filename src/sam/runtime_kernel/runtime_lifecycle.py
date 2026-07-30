"""Runtime Lifecycle — frozen DTOs lifecycle runtime."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class LifecyclePhase:
    phase_id: str
    name: str
    status: str = "pending"
    order: int = 0


@dataclass(frozen=True)
class StartupPlan:
    plan_id: str
    phases: List[LifecyclePhase] = field(default_factory=list)
    total_phases: int = 0
    completed_phases: int = 0
    is_ready: bool = False


@dataclass(frozen=True)
class ShutdownPlan:
    plan_id: str
    reason: str = ""
    graceful: bool = True
    total_tasks: int = 0
    completed_tasks: int = 0
    is_complete: bool = False


@dataclass(frozen=True)
class RestartPlan:
    plan_id: str
    shutdown_id: str = ""
    startup_id: str = ""
    status: str = "pending"
