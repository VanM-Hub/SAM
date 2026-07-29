# OP-426 — Conversation Dispatch Bridge
# Python 3.8, frozen DTO, synchronous, read-only queries

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple

from sam.execution.engine.execution_builder import ExecutionBuilder, ExecutionPackage
from sam.execution.execution_request import ExecutionPlan, ExecutionRequest

from .dispatch_request import (
    DispatchRequest, DispatchTask, DispatchStatus, DispatchPriority,
)
from .dispatcher import ConnectorDispatcher, DispatchContext, DispatchSession
from .dispatch_validator import DispatchValidator, DispatchValidationReport
from .dispatch_queue import DispatchQueue, QueuedDispatch, QueueStatistics
from .dispatch_audit import DispatchAudit, DispatchAuditEntry, DispatchAuditSummary


@dataclass(frozen=True)
class DispatchQueryResult:
    query_type: str = ""
    data: Any = None
    count: int = 0
    timestamp: datetime = field(default_factory=datetime.utcnow)


class ConversationDispatchBridge:
    """Read-only query bridge for dispatch operations.

    Queries:
    - dispatch queue
    - dispatch detail
    - dispatch preview
    - dispatch audit
    - dispatch validation
    - dispatch readiness
    - dispatch history
    - dispatch statistics
    - connector dispatch
    - approval status
    """

    def __init__(
        self,
        dispatcher: ConnectorDispatcher,
        validator: DispatchValidator,
        queue: DispatchQueue,
        audit: DispatchAudit,
    ) -> None:
        self._dispatcher = dispatcher
        self._validator = validator
        self._queue = queue
        self._audit = audit

    def query(self, query_type: str,
              params: Optional[Dict[str, Any]] = None) -> DispatchQueryResult:
        params = params or {}
        handlers = {
            "dispatch queue": self._query_queue,
            "dispatch detail": self._query_detail,
            "dispatch preview": self._query_preview,
            "dispatch audit": self._query_audit,
            "dispatch validation": self._query_validation,
            "dispatch readiness": self._query_readiness,
            "dispatch history": self._query_history,
            "dispatch statistics": self._query_statistics,
            "connector dispatch": self._query_connector,
            "approval status": self._query_approval,
        }
        handler = handlers.get(query_type.lower())
        if handler is None:
            return DispatchQueryResult(
                query_type=query_type,
                data={"error": f"Unknown query type: {query_type}"},
                count=0,
            )
        return handler(params)

    def _query_queue(self, params: Dict[str, Any]) -> DispatchQueryResult:
        items = self._queue.get_all()
        data = {
            "queue": [
                {
                    "request_id": i.request_id[:8],
                    "priority": i.priority.value,
                    "status": i.status.value,
                    "retry_count": i.retry_count,
                }
                for i in items[:20]
            ],
            "total": len(items),
        }
        return DispatchQueryResult(
            query_type="dispatch queue", data=data, count=len(items),
        )

    def _query_detail(self, params: Dict[str, Any]) -> DispatchQueryResult:
        request_id = params.get("request_id", "")
        item = self._queue.get(request_id)
        if item is None:
            return DispatchQueryResult(
                query_type="dispatch detail",
                data={"error": "Not found in queue"},
                count=0,
            )
        data = {
            "request_id": item.request_id[:8],
            "priority": item.priority.value,
            "status": item.status.value,
            "retry_count": item.retry_count,
        }
        return DispatchQueryResult(
            query_type="dispatch detail", data=data, count=1,
        )

    def _query_preview(self, params: Dict[str, Any]) -> DispatchQueryResult:
        session = self._dispatcher.create_session()
        b = ExecutionBuilder()
        req = ExecutionRequest(
            connector_type=params.get("connector_type", "file"),
            action=params.get("action", "read"),
        )
        plan = ExecutionPlan(requests=(req,))
        pkg = b.build(plan)
        context = self._dispatcher.build_dispatch(pkg, session)
        data = {
            "preview": context.preview,
            "connector_healthy": context.connector_healthy,
            "policy_approved": context.policy_approved,
            "validated": context.validated,
        }
        return DispatchQueryResult(
            query_type="dispatch preview", data=data, count=1,
        )

    def _query_audit(self, params: Dict[str, Any]) -> DispatchQueryResult:
        entries = self._audit.get_entries(
            request_id=params.get("request_id"),
            action=params.get("action"),
        )
        data = {
            "entries": [
                {
                    "action": e.action,
                    "details": e.details[:50],
                    "timestamp": str(e.timestamp),
                }
                for e in entries[:20]
            ],
            "total": len(entries),
        }
        return DispatchQueryResult(
            query_type="dispatch audit", data=data, count=len(entries),
        )

    def _query_validation(self, params: Dict[str, Any]) -> DispatchQueryResult:
        b = ExecutionBuilder()
        req = ExecutionRequest(
            connector_type=params.get("connector_type", "file"),
            action=params.get("action", "read"),
        )
        plan = ExecutionPlan(requests=(req,))
        pkg = b.build(plan)
        session = self._dispatcher.create_session()
        context = self._dispatcher.build_dispatch(pkg, session)
        req_obj = context.dispatch_request
        if req_obj:
            report = self._validator.validate(
                req_obj, connector_exists=True, connector_healthy=True,
                approval_exists=params.get("approved", False),
            )
        else:
            report = DispatchValidationReport(passed=False)

        data = {
            "passed": report.passed,
            "errors": report.errors,
            "warnings": report.warnings,
            "total_issues": report.total_issues,
            "issues": [
                {"category": i.category, "severity": i.severity, "message": i.message}
                for i in report.issues[:10]
            ],
        }
        return DispatchQueryResult(
            query_type="dispatch validation", data=data, count=report.total_issues,
        )

    def _query_readiness(self, params: Dict[str, Any]) -> DispatchQueryResult:
        queue_ok = self._queue.count > 0
        data = {
            "ready": queue_ok,
            "queue_has_items": queue_ok,
            "total_queued": self._queue.count,
        }
        return DispatchQueryResult(
            query_type="dispatch readiness", data=data, count=1,
        )

    def _query_history(self, params: Dict[str, Any]) -> DispatchQueryResult:
        summary = self._audit.get_summary()
        data = {
            "total_entries": summary.total_entries,
            "first_entry": str(summary.first_entry) if summary.first_entry else "",
            "last_entry": str(summary.last_entry) if summary.last_entry else "",
            "by_action": summary.by_action,
        }
        return DispatchQueryResult(
            query_type="dispatch history", data=data, count=summary.total_entries,
        )

    def _query_statistics(self, params: Dict[str, Any]) -> DispatchQueryResult:
        stats = self._queue.get_statistics()
        data = {
            "total_queued": stats.total_queued,
            "pending": stats.pending,
            "dispatched": stats.dispatched,
            "completed": stats.completed,
            "failed": stats.failed,
            "cancelled": stats.cancelled,
            "avg_priority": stats.avg_priority,
            "estimated_wait": stats.estimated_wait_seconds,
        }
        return DispatchQueryResult(
            query_type="dispatch statistics", data=data, count=1,
        )

    def _query_connector(self, params: Dict[str, Any]) -> DispatchQueryResult:
        connector_type = params.get("connector_type", "")
        session = self._dispatcher.create_session()
        b = ExecutionBuilder()
        req = ExecutionRequest(connector_type=connector_type or "file", action="read")
        plan = ExecutionPlan(requests=(req,))
        pkg = b.build(plan)
        context = self._dispatcher.build_dispatch(pkg, session)
        data = {
            "connector_type": connector_type,
            "ready": context.validated,
            "healthy": context.connector_healthy,
            "preview": context.preview,
        }
        return DispatchQueryResult(
            query_type="connector dispatch", data=data, count=1,
        )

    def _query_approval(self, params: Dict[str, Any]) -> DispatchQueryResult:
        items = self._queue.get_all()
        needs_approval = [
            {"request_id": i.request_id[:8], "priority": i.priority.value}
            for i in items
        ]
        data = {
            "total_in_queue": len(items),
            "needs_approval_count": len(needs_approval),
            "items": needs_approval[:10],
        }
        return DispatchQueryResult(
            query_type="approval status", data=data, count=len(needs_approval),
        )
