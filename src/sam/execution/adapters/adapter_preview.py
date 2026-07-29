# OP-434 — Adapter Preview
# Python 3.8, frozen DTO, synchronous, simulation only

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple

from .execution_envelope import ExecutionEnvelope, ExecutionEnvelopeItem


@dataclass(frozen=True)
class PreviewOperation:
    operation_id: str = ""
    action: str = ""
    target: str = ""
    adapter_type: str = ""
    estimated_duration_seconds: int = 0
    planned_impact: str = ""
    affected_resources: Tuple[str, ...] = field(default_factory=tuple)
    rollback_summary: str = ""


@dataclass(frozen=True)
class PreviewResult:
    total_operations: int = 0
    operations: Tuple[PreviewOperation, ...] = field(default_factory=tuple)
    estimated_total_duration: int = 0
    total_affected_resources: int = 0
    rollback_possible: bool = True
    overall_impact: str = ""


@dataclass(frozen=True)
class PreviewSummary:
    operations_count: int = 0
    estimated_duration_seconds: int = 0
    affected_resources_count: int = 0
    rollback_available: bool = True
    preview_note: str = "Preview complete. No actual execution occurred."
    timestamp: datetime = field(default_factory=datetime.utcnow)


class PreviewAdapter:
    """Generates previews for execution envelopes.

    Only produces simulations — no real execution.
    """

    def preview(self, envelope: ExecutionEnvelope) -> PreviewResult:
        if not envelope.items:
            return PreviewResult()

        operations: List[PreviewOperation] = []
        total_affected = 0

        for item in envelope.items:
            resources = self._estimate_resources(item)
            total_affected += len(resources)

            op = PreviewOperation(
                operation_id=item.item_id,
                action=item.action,
                target=item.target,
                adapter_type=item.adapter_type,
                estimated_duration_seconds=item.estimated_duration_seconds or 1,
                planned_impact=self._estimate_impact(item),
                affected_resources=resources,
                rollback_summary=self._estimate_rollback(item),
            )
            operations.append(op)

        total_duration = sum(
            op.estimated_duration_seconds for op in operations
        )

        return PreviewResult(
            total_operations=len(operations),
            operations=tuple(operations),
            estimated_total_duration=total_duration,
            total_affected_resources=total_affected,
            rollback_possible=True,
            overall_impact=self._assess_overall_impact(operations),
        )

    def to_summary(self, result: PreviewResult) -> PreviewSummary:
        return PreviewSummary(
            operations_count=result.total_operations,
            estimated_duration_seconds=result.estimated_total_duration,
            affected_resources_count=result.total_affected_resources,
            rollback_available=result.rollback_possible,
        )

    @staticmethod
    def _estimate_resources(item: ExecutionEnvelopeItem) -> Tuple[str, ...]:
        if item.adapter_type == "filesystem":
            return (item.target or "unknown",)
        elif item.adapter_type == "rest_api":
            return (f"endpoint:{item.target or 'unknown'}",)
        elif item.adapter_type == "shell":
            return ("process", "stdout", "stderr")
        else:
            return (item.target or "unknown",)

    @staticmethod
    def _estimate_impact(item: ExecutionEnvelopeItem) -> str:
        action_impact = {
            "read": "Read operation, no side effects",
            "write": "Write operation, may modify target",
            "create": "Create operation, adds new resource",
            "delete": "Delete operation, removes resource permanently",
            "execute": "Execute operation, runs command on target",
            "monitor": "Monitor operation, reads state",
            "search": "Search operation, reads data",
        }
        return action_impact.get(item.action, "Unknown operation impact")

    @staticmethod
    def _estimate_rollback(item: ExecutionEnvelopeItem) -> str:
        if item.action in ("delete", "execute", "write"):
            return f"Rollback available for {item.action}, may need manual verification"
        return f"Rollback for {item.action} is straightforward"

    @staticmethod
    def _assess_overall_impact(ops: List[PreviewOperation]) -> str:
        high_risk_actions = {"delete", "execute"}
        for op in ops:
            if op.action in high_risk_actions:
                return "HIGH - Contains high-risk operations (delete/execute)"
        write_actions = {"write", "create"}
        for op in ops:
            if op.action in write_actions:
                return "MEDIUM - Contains write operations"
        return "LOW - Read-only or monitor operations"
