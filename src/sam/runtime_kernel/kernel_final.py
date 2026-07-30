"""Runtime Kernel Final — DTOs final."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class KernelFinalReport:
    report_id: str
    version: str
    status: str = "pending"
    components: List[str] = field(default_factory=list)
    metrics: Dict[str, int] = field(default_factory=dict)


@dataclass(frozen=True)
class ComponentHealth:
    component: str
    healthy: bool = True
    message: str = ""


@dataclass(frozen=True)
class KernelSummary:
    summary_id: str
    total_components: int = 0
    healthy_count: int = 0
    version: str = ""


@dataclass(frozen=True)
class FinalVerdict:
    verdict_id: str
    ready: bool = False
    reason: str = ""
