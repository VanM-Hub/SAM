# OP-436 — Conversation Adapter Bridge
# Python 3.8, frozen DTO, synchronous, read-only

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple

from .execution_envelope import ExecutionEnvelope, ExecutionEnvelopeBuilder, ExecutionEnvelopeSummary
from .adapter_protocol import BaseAdapter, MockAdapter, AdapterMetadata, AdapterCapability, AdapterHealth
from .adapter_registry import AdapterRegistry, RegisteredAdapter, AdapterSelector
from .adapter_preview import PreviewAdapter, PreviewResult, PreviewSummary
from .adapter_validator import AdapterValidator, AdapterValidationReport


@dataclass(frozen=True)
class AdapterQueryResult:
    query_type: str = ""
    data: Any = None
    count: int = 0
    timestamp: datetime = field(default_factory=datetime.utcnow)


class ConversationAdapterBridge:
    """Read-only query bridge for adapter operations.

    Queries:
    - adapter list
    - adapter detail
    - adapter capability
    - execution envelope
    - preview execution
    - adapter validation
    - adapter readiness
    - adapter health
    - execution summary
    - resource impact
    """

    def __init__(
        self,
        registry: AdapterRegistry,
        validator: AdapterValidator,
        preview: PreviewAdapter,
    ) -> None:
        self._registry = registry
        self._validator = validator
        self._preview = preview

    def query(self, query_type: str,
              params: Optional[Dict[str, Any]] = None) -> AdapterQueryResult:
        params = params or {}
        handlers = {
            "adapter list": self._query_list,
            "adapter detail": self._query_detail,
            "adapter capability": self._query_capability,
            "execution envelope": self._query_envelope,
            "preview execution": self._query_preview,
            "adapter validation": self._query_validation,
            "adapter readiness": self._query_readiness,
            "adapter health": self._query_health,
            "execution summary": self._query_summary,
            "resource impact": self._query_resources,
        }
        handler = handlers.get(query_type.lower())
        if handler is None:
            return AdapterQueryResult(
                query_type=query_type,
                data={"error": f"Unknown: {query_type}"},
                count=0,
            )
        return handler(params)

    def _query_list(self, p: Dict) -> AdapterQueryResult:
        entries = self._registry.list()
        data = {
            "adapters": [
                {"name": e.name, "type": e.adapter_type, "version": e.version,
                 "capabilities": len(e.capability_names), "healthy": e.healthy}
                for e in entries
            ]
        }
        return AdapterQueryResult("adapter list", data, len(entries))

    def _query_detail(self, p: Dict) -> AdapterQueryResult:
        aid = p.get("adapter_id", "")
        entry = self._registry.find_entry(aid) if aid else None
        if not entry:
            return AdapterQueryResult("adapter detail", {"error": "Not found"}, 0)
        return AdapterQueryResult("adapter detail", {
            "name": entry.name, "type": entry.adapter_type,
            "version": entry.version, "capabilities": entry.capability_names,
            "healthy": entry.healthy,
        }, 1)

    def _query_capability(self, p: Dict) -> AdapterQueryResult:
        adapters = self._registry.list()
        all_caps: Dict[str, List[str]] = {}
        for a in adapters:
            for cap in a.capability_names:
                all_caps.setdefault(cap, []).append(a.name)
        data = {"capabilities": {k: {"adapters": v} for k, v in all_caps.items()}}
        return AdapterQueryResult("adapter capability", data, len(all_caps))

    def _query_envelope(self, p: Dict) -> AdapterQueryResult:
        from sam.execution.dispatch.dispatch_request import DispatchRequest, DispatchTask
        tasks = (DispatchTask(task_id="t1", name="read", action="read", target="test"),)
        dispatch = DispatchRequest(tasks=tasks, requires_approval=False)
        env = ExecutionEnvelopeBuilder.build(dispatch, p.get("adapter_type", "mock"))
        data = {
            "envelope_id": env.envelope_id[:8],
            "total_items": env.total_items,
            "requires_approval": env.requires_approval,
            "estimated_duration": env.estimated_duration_seconds,
        }
        return AdapterQueryResult("execution envelope", data, env.total_items)

    def _query_preview(self, p: Dict) -> AdapterQueryResult:
        from sam.execution.dispatch.dispatch_request import DispatchRequest, DispatchTask
        tasks = (DispatchTask(task_id="t1", name="read", action="read", target="test"),)
        dispatch = DispatchRequest(tasks=tasks, requires_approval=False)
        env = ExecutionEnvelopeBuilder.build(dispatch, p.get("adapter_type", "mock"))
        result = self._preview.preview(env)
        data = {
            "operations": result.total_operations,
            "total_duration": result.estimated_total_duration,
            "impact": result.overall_impact,
            "rollback": result.rollback_possible,
        }
        return AdapterQueryResult("preview execution", data, result.total_operations)

    def _query_validation(self, p: Dict) -> AdapterQueryResult:
        from sam.execution.dispatch.dispatch_request import DispatchRequest, DispatchTask
        tasks = (DispatchTask(task_id="t1", name="read", action="read"),)
        dispatch = DispatchRequest(tasks=tasks, requires_approval=False)
        env = ExecutionEnvelopeBuilder.build(dispatch)
        report = self._validator.validate(env, p.get("adapter_type", "mock"))
        data = {
            "passed": report.passed, "errors": report.errors,
            "warnings": report.warnings, "total": report.total_issues,
        }
        return AdapterQueryResult("adapter validation", data, report.total_issues)

    def _query_readiness(self, p: Dict) -> AdapterQueryResult:
        can_preview = self._registry.count > 0
        data = {
            "ready": can_preview,
            "adapters_registered": self._registry.count,
            "can_preview": can_preview,
        }
        return AdapterQueryResult("adapter readiness", data, 1)

    def _query_health(self, p: Dict) -> AdapterQueryResult:
        stats = self._registry.get_statistics()
        data = {
            "overall_healthy": stats.unhealthy == 0,
            "total": stats.total, "healthy": stats.healthy,
            "unhealthy": stats.unhealthy, "by_type": stats.by_type,
        }
        return AdapterQueryResult("adapter health", data, stats.total)

    def _query_summary(self, p: Dict) -> AdapterQueryResult:
        data = {
            "adapters": self._registry.count,
            "types": len(self._registry.get_statistics().by_type),
            "message": "Adapter layer ready. No real execution.",
        }
        return AdapterQueryResult("execution summary", data, 1)

    def _query_resources(self, p: Dict) -> AdapterQueryResult:
        from sam.execution.dispatch.dispatch_request import DispatchRequest, DispatchTask
        tasks = (DispatchTask(task_id="t1", name="read", action="read", target="test"),)
        dispatch = DispatchRequest(tasks=tasks, requires_approval=False)
        env = ExecutionEnvelopeBuilder.build(dispatch)
        result = self._preview.preview(env)
        data = {
            "estimated_affected": result.total_affected_resources,
            "operations": result.total_operations,
            "impact": result.overall_impact,
        }
        return AdapterQueryResult("resource impact", data, result.total_operations)
