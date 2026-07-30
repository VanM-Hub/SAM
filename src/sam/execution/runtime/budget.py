"""Budget/Cost — frozen DTO biaya eksekusi."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Tuple


@dataclass(frozen=True)
class Budget:
    budget_id: str
    execution_plan_id: str
    total_budget: float = 0.0
    cpu_cost_rate: float = 1.0
    memory_cost_rate: float = 0.5
    storage_cost_rate: float = 0.1
    network_cost_rate: float = 0.05
    used_cpu_units: float = 0.0
    used_memory_mb: float = 0.0
    used_storage_mb: float = 0.0
    used_network_units: float = 0.0


@dataclass(frozen=True)
class CostEstimate:
    estimate_id: str
    candidate_id: str
    cpu_cost: float = 0.0
    memory_cost: float = 0.0
    storage_cost: float = 0.0
    network_cost: float = 0.0
    estimated_total: float = 0.0


@dataclass(frozen=True)
class BudgetReport:
    budget_id: str
    total_allocated: float = 0.0
    total_estimated: float = 0.0
    remaining: float = 0.0
    is_over_budget: bool = False
    overage_amount: float = 0.0


@dataclass(frozen=True)
class BudgetSummary:
    total_budgets: int = 0
    total_budget_amount: float = 0.0
    total_estimated_cost: float = 0.0
    over_budget_count: int = 0
    status: str = "clean"
