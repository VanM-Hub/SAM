"""Budget Engine — cost estimation & budget tracking."""
from __future__ import annotations
from typing import Dict, List, Optional
from sam.execution.runtime.execution_candidate import ExecutionCandidate
from sam.execution.runtime.budget import Budget, CostEstimate, BudgetReport, BudgetSummary


class BudgetEngine:
    """Engine untuk estimasi biaya dan tracking budget."""

    def __init__(self) -> None:
        self._budgets: Dict[str, Budget] = {}
        self._estimates: Dict[str, CostEstimate] = {}

    def register_budget(self, budget: Budget) -> None:
        self._budgets[budget.budget_id] = budget

    def get_budget(self, budget_id: str) -> Optional[Budget]:
        return self._budgets.get(budget_id)

    def estimate(self, candidate: ExecutionCandidate,
                 budget_id: str = "",
                 cpu_rate: float = 1.0,
                 memory_rate: float = 0.5,
                 storage_rate: float = 0.1,
                 network_rate: float = 0.05) -> CostEstimate:
        """Estimasi biaya untuk satu kandidat."""
        cpu = candidate.estimated_effort * cpu_rate * 2.0
        mem = candidate.estimated_effort * memory_rate * 10.0
        storage = candidate.estimated_effort * storage_rate * 5.0
        network = candidate.estimated_effort * network_rate

        estimate = CostEstimate(
            estimate_id=f"est_{candidate.candidate_id}",
            candidate_id=candidate.candidate_id,
            cpu_cost=round(cpu, 2),
            memory_cost=round(mem, 2),
            storage_cost=round(storage, 2),
            network_cost=round(network, 2),
            estimated_total=round(cpu + mem + storage + network, 2),
        )
        self._estimates[estimate.estimate_id] = estimate
        return estimate

    def estimate_batch(self, candidates: List[ExecutionCandidate],
                       rates: Optional[Dict[str, float]] = None) -> List[CostEstimate]:
        """Estimasi batch untuk beberapa kandidat."""
        rates = rates or {}
        return [
            self.estimate(
                c,
                cpu_rate=rates.get("cpu", 1.0),
                memory_rate=rates.get("memory", 0.5),
                storage_rate=rates.get("storage", 0.1),
                network_rate=rates.get("network", 0.05),
            )
            for c in candidates
        ]

    def generate_report(self, budget_id: str) -> Optional[BudgetReport]:
        """Generate budget report."""
        budget = self._budgets.get(budget_id)
        if not budget:
            return None

        total_estimated = sum(
            e.estimated_total
            for e in self._estimates.values()
        )
        remaining = budget.total_budget - total_estimated
        overage = max(0.0, -remaining)

        return BudgetReport(
            budget_id=budget_id,
            total_allocated=budget.total_budget,
            total_estimated=round(total_estimated, 2),
            remaining=round(remaining, 2),
            is_over_budget=remaining < 0,
            overage_amount=round(overage, 2),
        )

    def get_summary(self) -> BudgetSummary:
        """Buat ringkasan budget."""
        total_budget = sum(b.total_budget for b in self._budgets.values())
        total_est = sum(
            e.estimated_total
            for e in self._estimates.values()
        )
        over = sum(
            1 for b in self._budgets
            for r in [self.generate_report(b)]
            if r and r.is_over_budget
        )
        status = "over_budget" if over > 0 else "clean"
        return BudgetSummary(
            total_budgets=len(self._budgets),
            total_budget_amount=round(total_budget, 2),
            total_estimated_cost=round(total_est, 2),
            over_budget_count=over,
            status=status,
        )
