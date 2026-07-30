"""Simulation — frozen DTO simulasi eksekusi."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple


@dataclass(frozen=True)
class SimulationConfig:
    """Konfigurasi simulasi."""
    simulation_id: str
    scenario_name: str
    max_iterations: int = 100
    time_step_ms: float = 10.0
    execution_order_id: str = ""
    candidate_ids: Tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class SimulationStep:
    """Satu step dalam simulasi."""
    step_number: int
    timestamp: float
    candidate_id: str = ""
    action: str = "pending"
    cpu_used: float = 0.0
    memory_used: float = 0.0
    duration_ms: float = 0.0


@dataclass(frozen=True)
class SimulationResult:
    """Hasil simulasi."""
    simulation_id: str
    steps: Tuple[SimulationStep, ...] = field(default_factory=tuple)
    total_steps: int = 0
    total_duration_ms: float = 0.0
    total_cpu_used: float = 0.0
    total_memory_used: float = 0.0


@dataclass(frozen=True)
class SimulationSummary:
    """Ringkasan simulasi."""
    total_simulations: int = 0
    total_steps_across: int = 0
    avg_duration_ms: float = 0.0
    scenarios: Tuple[str, ...] = field(default_factory=tuple)
    status: str = "idle"
