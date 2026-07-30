"""Runtime Coordinator — DTOs koordinasi subsystem."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass(frozen=True)
class CoordinationTask:
    task_id: str
    subsystem: str
    action: str = ""
    status: str = "pending"
    order: int = 0


@dataclass(frozen=True)
class CoordinationPlan:
    plan_id: str
    tasks: List[CoordinationTask] = field(default_factory=list)
    total: int = 0
    completed: int = 0
    is_ready: bool = False


@dataclass(frozen=True)
class SyncPoint:
    sync_id: str
    subsystem: str
    synced: bool = False
    data: str = ""


@dataclass(frozen=True)
class OrchestrationOrder:
    order_id: str
    subsystem: str
    command: str = ""
    priority: int = 0


@dataclass(frozen=True)
class CoordinationResult:
    result_id: str
    success: bool = False
    message: str = ""
