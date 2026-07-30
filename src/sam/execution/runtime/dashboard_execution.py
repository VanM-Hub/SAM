"""Dashboard Execution Bridge — 6 immutable cards."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from sam.execution.runtime.execution_registry import ExecutionRegistry


@dataclass(frozen=True)
class ExecutionCard:
    """Kartu dashboard execution — immutable."""
    title: str
    description: str
    status: str
    metrics: Dict[str, Any]
    items: List[str]


class DashboardExecution:
    """Dashboard bridge untuk execution runtime — 6 immutable cards."""

    def __init__(self, registry: ExecutionRegistry) -> None:
        self._registry = registry

    def overview_card(self) -> ExecutionCard:
        """Card 1: Overview execution."""
        return ExecutionCard(
            title="Execution Overview",
            description="Ringkasan status execution",
            status="ready",
            metrics={
                "total_contexts": self._registry.snapshot().context_count,
                "total_requests": self._registry.snapshot().request_count,
                "total_candidates": self._registry.snapshot().candidate_count,
                "total_items": self._registry.total_items,
            },
            items=["contexts", "requests", "candidates"],
        )

    def context_card(self) -> ExecutionCard:
        """Card 2: Context info."""
        ctx_ids = list(self._registry.snapshot().context_ids)
        return ExecutionCard(
            title="Execution Contexts",
            description="Daftar execution context terdaftar",
            status="active" if ctx_ids else "empty",
            metrics={"count": len(ctx_ids)},
            items=ctx_ids,
        )

    def request_card(self) -> ExecutionCard:
        """Card 3: Request info."""
        req_ids = list(self._registry.snapshot().request_ids)
        return ExecutionCard(
            title="Execution Requests",
            description="Daftar execution request terdaftar",
            status="active" if req_ids else "empty",
            metrics={"count": len(req_ids)},
            items=req_ids,
        )

    def candidate_card(self) -> ExecutionCard:
        """Card 4: Candidate info."""
        cand_ids = list(self._registry.snapshot().candidate_ids)
        return ExecutionCard(
            title="Execution Candidates",
            description="Daftar execution candidate terdaftar",
            status="active" if cand_ids else "empty",
            metrics={"count": len(cand_ids)},
            items=cand_ids,
        )

    def summary_card(self) -> ExecutionCard:
        """Card 5: Summary execution."""
        snap = self._registry.snapshot()
        return ExecutionCard(
            title="Execution Summary",
            description="Ringkasan seluruh komponen execution",
            status="ready",
            metrics={
                "contexts": snap.context_count,
                "requests": snap.request_count,
                "candidates": snap.candidate_count,
                "is_empty": self._registry.is_empty,
            },
            items=["summary"],
        )

    def status_card(self) -> ExecutionCard:
        """Card 6: Status execution."""
        return ExecutionCard(
            title="Execution Status",
            description="Status execution runtime saat ini",
            status="idle" if self._registry.is_empty else "populated",
            metrics={"is_empty": self._registry.is_empty},
            items=["idle" if self._registry.is_empty else "ready"],
        )
