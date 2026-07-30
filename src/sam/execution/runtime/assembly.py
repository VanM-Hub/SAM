"""Execution Plan Assembly — frozen assembly DTOs."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple


@dataclass(frozen=True)
class AssemblyComponent:
    name: str
    component_type: str
    status: str
    description: str = ""
    items_count: int = 0


@dataclass(frozen=True)
class ExecutionAssembly:
    assembly_id: str
    execution_plan_id: str
    components: Tuple[AssemblyComponent, ...] = field(default_factory=tuple)
    total_components: int = 0
    ready_components: int = 0
    failed_components: int = 0
    is_ready: bool = False


@dataclass(frozen=True)
class ReadinessReport:
    report_id: str
    assembly_id: str
    overall_readiness: float = 0.0
    component_readiness: Dict[str, float] = field(default_factory=dict)
    missing_components: Tuple[str, ...] = field(default_factory=tuple)
    is_ready: bool = False


@dataclass(frozen=True)
class AssemblySummary:
    total_assemblies: int = 0
    ready_assemblies: int = 0
    avg_readiness: float = 0.0
    total_components_across: int = 0
    status: str = "not_ready"
