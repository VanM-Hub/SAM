"""Execution Plan — frozen DTO rencana eksekusi."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class ExecutionPlan:
    """Rencana eksekusi — blueprint lengkap task execution."""
    plan_id: str
    draft_id: str
    context_id: str
    total_tasks: int
    total_steps: int
    environment: str = "normal"
    strategies: List[str] = field(default_factory=list)
    sequences: List[str] = field(default_factory=list)
    priority_score: float = 0.0
    schedule_info: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
