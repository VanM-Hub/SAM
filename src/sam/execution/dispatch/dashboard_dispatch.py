# OP-427 — Dashboard Dispatch
# Python 3.8, frozen DTO, synchronous, presentation only

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple

from .dispatch_queue import DispatchQueue, QueueStatistics
from .dispatch_audit import DispatchAudit, DispatchAuditSummary


@dataclass(frozen=True)
class DispatchCard:
    total_requests: int = 0
    queued: int = 0
    dispatched: int = 0
    completed: int = 0
    failed: int = 0
    cancelled: int = 0


@dataclass(frozen=True)
class QueueCardDTO:
    total_queued: int = 0
    pending: int = 0
    avg_priority: float = 0.0
    estimated_wait_seconds: int = 0


@dataclass(frozen=True)
class AuditCard:
    total_entries: int = 0
    by_action: Dict[str, int] = field(default_factory=dict)


@dataclass(frozen=True)
class ValidationCardDTO:
    known_connectors: int = 0
    healthy_connectors: int = 0
    passes_default_check: bool = True


@dataclass(frozen=True)
class ConnectorDispatchCard:
    filesystem_ready: bool = False
    rest_api_ready: bool = False
    git_ready: bool = False
    shell_ready: bool = False
    total_ready: int = 0


@dataclass(frozen=True)
class StatisticsCard:
    total_requests: int = 0
    success_rate: float = 0.0
    avg_dispatch_time: str = ""


@dataclass(frozen=True)
class DispatchDashboard:
    dispatch: DispatchCard = field(default_factory=DispatchCard)
    queue: QueueCardDTO = field(default_factory=QueueCardDTO)
    audit: AuditCard = field(default_factory=AuditCard)
    validation: ValidationCardDTO = field(default_factory=ValidationCardDTO)
    connectors: ConnectorDispatchCard = field(default_factory=ConnectorDispatchCard)
    statistics: StatisticsCard = field(default_factory=StatisticsCard)
    timestamp: datetime = field(default_factory=datetime.utcnow)


class DispatchDashboardBuilder:
    """Builds dispatch dashboard DTOs — pure composition."""

    @staticmethod
    def build(
        queue: DispatchQueue,
        audit: DispatchAudit,
        connector_count: int = 0,
        healthy_count: int = 0,
    ) -> DispatchDashboard:
        stats = queue.get_statistics()
        audit_summary = audit.get_summary()

        dispatch_card = DispatchCard(
            total_requests=stats.total_queued or audit_summary.total_entries,
            queued=stats.pending,
            dispatched=stats.dispatched,
            completed=stats.completed,
            failed=stats.failed,
            cancelled=stats.cancelled,
        )

        queue_card = QueueCardDTO(
            total_queued=stats.total_queued,
            pending=stats.pending,
            avg_priority=stats.avg_priority,
            estimated_wait_seconds=stats.estimated_wait_seconds,
        )

        audit_card = AuditCard(
            total_entries=audit_summary.total_entries,
            by_action=audit_summary.by_action,
        )

        validation_card = ValidationCardDTO(
            known_connectors=connector_count,
            healthy_connectors=healthy_count,
            passes_default_check=connector_count > 0,
        )

        connectors_ready = connector_count > 0 and healthy_count == connector_count
        connector_dispatch_card = ConnectorDispatchCard(
            filesystem_ready=connectors_ready,
            rest_api_ready=connectors_ready,
            git_ready=connectors_ready,
            shell_ready=connectors_ready,
            total_ready=healthy_count,
        )

        total_req = stats.total_queued or audit_summary.total_entries
        if total_req > 0:
            success_rate = (stats.completed / total_req) if total_req > 0 else 0.0
        else:
            success_rate = 0.0

        stats_card = StatisticsCard(
            total_requests=total_req,
            success_rate=round(success_rate, 4),
            avg_dispatch_time="N/A",
        )

        return DispatchDashboard(
            dispatch=dispatch_card,
            queue=queue_card,
            audit=audit_card,
            validation=validation_card,
            connectors=connector_dispatch_card,
            statistics=stats_card,
        )
