"""Simulation Engine — preview execution simulation."""
from __future__ import annotations
from typing import List, Optional, Tuple
from sam.execution.runtime.execution_candidate import ExecutionCandidate
from sam.execution.runtime.simulation import (
    SimulationConfig, SimulationStep, SimulationResult, SimulationSummary,
)


class SimulationEngine:
    """Engine simulasi eksekusi — preview-only."""

    def __init__(self) -> None:
        self._results: List[SimulationResult] = []

    def simulate(self, config: SimulationConfig,
                 candidates: List[ExecutionCandidate]) -> SimulationResult:
        """Jalankan simulasi."""
        steps: List[SimulationStep] = []
        current_time = 0.0
        total_cpu = 0.0
        total_mem = 0.0

        for i, c in enumerate(candidates):
            cpu = c.estimated_effort * 2.0
            mem = c.estimated_effort * 10.0
            dur = c.estimated_effort
            step = SimulationStep(
                step_number=i + 1,
                timestamp=current_time,
                candidate_id=c.candidate_id,
                action=c.candidate_type if c.candidate_type else "execute",
                cpu_used=cpu,
                memory_used=mem,
                duration_ms=dur * 1000.0,
            )
            steps.append(step)
            current_time += dur
            total_cpu += cpu
            total_mem += mem

        result = SimulationResult(
            simulation_id=config.simulation_id,
            steps=tuple(steps),
            total_steps=len(steps),
            total_duration_ms=current_time * 1000.0,
            total_cpu_used=total_cpu,
            total_memory_used=total_mem,
        )
        self._results.append(result)
        return result

    def get_summary(self) -> SimulationSummary:
        """Buat ringkasan dari seluruh simulasi."""
        total_steps = sum(r.total_steps for r in self._results)
        total_duration = sum(r.total_duration_ms for r in self._results)
        n = len(self._results)
        scenarios = tuple(
            r.simulation_id if hasattr(r, 'simulation_id') else ""
            for r in self._results[-10:]
        )
        return SimulationSummary(
            total_simulations=n,
            total_steps_across=total_steps,
            avg_duration_ms=total_duration / n if n > 0 else 0.0,
            scenarios=scenarios,
            status="active" if n > 0 else "idle",
        )
