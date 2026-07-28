"""
OP-298 — Operational Dashboard Integration

DTO untuk dashboard reasoning.
Dashboard hanya membaca DTO — tidak memanggil provider.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime


@dataclass(frozen=True)
class ReasoningWidget:
    title: str
    value: str
    icon: str = "🧠"
    status: str = "info"  # ok, warning, error, info
    detail: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "value": self.value,
            "icon": self.icon,
            "status": self.status,
            "detail": self.detail,
        }


@dataclass(frozen=True)
class ProviderStatus:
    name: str
    healthy: bool
    circuit_breaker_open: bool
    priority: int
    latency_ms: float
    last_error: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "healthy": self.healthy,
            "circuit_breaker_open": self.circuit_breaker_open,
            "priority": self.priority,
            "latency_ms": self.latency_ms,
            "last_error": self.last_error,
        }


@dataclass(frozen=True)
class ReasoningStatus:
    active_sessions: int
    total_reasonings: int
    total_tokens: int
    validation_pass_rate: float
    average_confidence: float
    average_latency_ms: float
    providers: Tuple[ProviderStatus, ...] = ()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "active_sessions": self.active_sessions,
            "total_reasonings": self.total_reasonings,
            "total_tokens": self.total_tokens,
            "validation_pass_rate": self.validation_pass_rate,
            "average_confidence": self.average_confidence,
            "average_latency_ms": self.average_latency_ms,
            "providers": [p.to_dict() for p in self.providers],
        }


@dataclass(frozen=True)
class ReasoningHistoryView:
    recent_items: Tuple[Dict[str, Any], ...] = ()
    total_count: int = 0
    by_template: Dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "recent_items": list(self.recent_items),
            "total_count": self.total_count,
            "by_template": self.by_template,
        }


class DashboardReasoningService:
    """
    Membaca state reasoning untuk dashboard.
    Tidak memanggil provider — hanya membaca DTO.
    """

    def __init__(self, pipeline: Any, scheduler: Any):
        self._pipeline = pipeline
        self._scheduler = scheduler

    def get_status(self) -> ReasoningStatus:
        session = self._pipeline.session
        provider_health = self._scheduler.health_report()

        providers: list[ProviderStatus] = []
        for name in self._scheduler.providers:
            slot = self._scheduler.get_slot(name)
            cb_open = False
            providers.append(ProviderStatus(
                name=name,
                healthy=provider_health.get(name, False),
                circuit_breaker_open=cb_open,
                priority=slot.priority if slot else 100,
                latency_ms=0.0,
            ))

        total_records = session.reasoning_count
        tokens = session.tokens_used
        confidence_sum = sum(
            r.confidence for r in session.history.records
        ) if total_records > 0 else 1.0

        return ReasoningStatus(
            active_sessions=1 if session.is_active else 0,
            total_reasonings=total_records,
            total_tokens=tokens,
            validation_pass_rate=1.0,
            average_confidence=round(
                confidence_sum / max(total_records, 1), 2
            ),
            average_latency_ms=0.0,
            providers=tuple(providers),
        )

    def get_widgets(self) -> Tuple[ReasoningWidget, ...]:
        status = self.get_status()
        return (
            ReasoningWidget(
                title="Sessions",
                value=str(status.active_sessions),
                status="ok" if status.active_sessions > 0 else "info",
            ),
            ReasoningWidget(
                title="Reasonings",
                value=str(status.total_reasonings),
                status="ok",
            ),
            ReasoningWidget(
                title="Confidence",
                value=f"{status.average_confidence:.0%}",
                detail="Average confidence across all reasonings",
            ),
            ReasoningWidget(
                title="Tokens",
                value=str(status.total_tokens),
                status="info",
            ),
            ReasoningWidget(
                title="Providers",
                value=f"{sum(1 for p in status.providers if p.healthy)}/{len(status.providers)}",
                status="ok" if any(p.healthy for p in status.providers) else "error",
                detail="Healthy / Total providers",
            ),
        )

    def get_history_view(self) -> ReasoningHistoryView:
        records = self._pipeline.session.history.records
        by_template: Dict[str, int] = {}
        for r in records:
            by_template[r.template_name] = by_template.get(r.template_name, 0) + 1

        return ReasoningHistoryView(
            recent_items=tuple(r.to_dict() for r in records[-10:]),
            total_count=len(records),
            by_template=by_template,
        )
