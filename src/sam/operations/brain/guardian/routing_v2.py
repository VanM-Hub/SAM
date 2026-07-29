"""
OP-338 — Guardian Runtime V2 Integration

Menghubungkan seluruh pipeline:
  Guardian Runtime V2 → Snapshot → History → Trend → Summary → Dashboard DTO → Conversation DTO

Semua synchronous, read-only.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime


@dataclass(frozen=True)
class RoutingV2Result:
    """Hasil routing pipeline penuh."""
    success: bool
    pipeline_id: str = ""
    runtime_ok: bool = False
    snapshot_ok: bool = False
    history_ok: bool = False
    trend_ok: bool = False
    summary_ok: bool = False
    dashboard_ok: bool = False
    conversation_ok: bool = False
    errors: Tuple[str, ...] = field(default_factory=tuple)
    started_at: str = ""
    completed_at: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "pipeline_id": self.pipeline_id,
            "runtime_ok": self.runtime_ok,
            "snapshot_ok": self.snapshot_ok,
            "history_ok": self.history_ok,
            "trend_ok": self.trend_ok,
            "summary_ok": self.summary_ok,
            "dashboard_ok": self.dashboard_ok,
            "conversation_ok": self.conversation_ok,
            "errors": list(self.errors),
            "started_at": self.started_at,
            "completed_at": self.completed_at,
        }


class GuardianRoutingV2Integration:
    """Routing yang menghubungkan semua pipeline V2."""

    def __init__(
        self,
        runtime_v2: Any = None,
        snapshot_engine: Any = None,
        history: Any = None,
        trend: Any = None,
        summary_builder: Any = None,
        dashboard_v2: Any = None,
        conversation_v2: Any = None,
    ):
        self._runtime = runtime_v2
        self._snapshot = snapshot_engine
        self._history = history
        self._trend = trend
        self._summary = summary_builder
        self._dashboard = dashboard_v2
        self._conversation = conversation_v2
        self._results: List[RoutingV2Result] = []

    @property
    def result_count(self) -> int:
        return len(self._results)

    @property
    def last_result(self) -> Optional[RoutingV2Result]:
        return self._results[-1] if self._results else None

    def run(self, **kw: Any) -> RoutingV2Result:
        """Jalankan seluruh pipeline routing."""
        started_at = datetime.now().isoformat(timespec="seconds")
        pipeline_id = "rtv2-{}-{}".format(
            datetime.now().strftime("%H%M%S"), len(self._results),
        )
        errors: List[str] = []

        # Stage 1: Runtime V2 (10-stage)
        runtime_ok = False
        runtime_data: Dict[str, Any] = {}
        if self._runtime:
            try:
                runtime_result = self._runtime.run(**kw)
                runtime_ok = runtime_result.success
                runtime_data = runtime_result.pipeline_data
            except Exception as e:
                errors.append("RuntimeV2: {}".format(e))

        # Stage 2: Snapshot
        snapshot_ok = False
        if self._snapshot:
            try:
                kwargs = dict(kw)
                if runtime_data.get("health", {}).get("status"):
                    kwargs.setdefault("health_status", runtime_data["health"]["status"])
                if runtime_data.get("health", {}).get("score"):
                    kwargs.setdefault("health_score", runtime_data["health"]["score"])
                self._snapshot.collect(**kwargs)
                snapshot_ok = True
            except Exception as e:
                errors.append("Snapshot: {}".format(e))

        # Stage 3: History
        history_ok = False
        if self._history:
            try:
                health_data = runtime_data.get("health", {})
                self._history.append_event(
                    category="info",
                    severity="low",
                    message="Runtime V2 pipeline completed",
                    detail="Pipeline {} health: {}".format(
                        pipeline_id, health_data.get("status", "unknown"),
                    ),
                )
                history_ok = True
            except Exception as e:
                errors.append("History: {}".format(e))

        # Stage 4: Trend
        trend_ok = False
        if self._trend:
            try:
                self._trend.analyze(**kw)
                trend_ok = True
            except Exception as e:
                errors.append("Trend: {}".format(e))

        # Stage 5: Summary
        summary_ok = False
        if self._summary:
            try:
                self._summary.build(**kw)
                summary_ok = True
            except Exception as e:
                errors.append("Summary: {}".format(e))

        # Stage 6: Dashboard
        dashboard_ok = False
        if self._dashboard:
            try:
                self._dashboard.build_health_card()
                self._dashboard.build_policy_card()
                self._dashboard.build_trend_card()
                self._dashboard.build_recommendation_card()
                self._dashboard.build_risk_card()
                self._dashboard.build_summary_card()
                dashboard_ok = True
            except Exception as e:
                errors.append("Dashboard: {}".format(e))

        # Stage 7: Conversation
        conversation_ok = False
        if self._conversation:
            try:
                self._conversation.query_status()
                conversation_ok = True
            except Exception as e:
                errors.append("Conversation: {}".format(e))

        completed_at = datetime.now().isoformat(timespec="seconds")
        success = len(errors) == 0

        result = RoutingV2Result(
            success=success,
            pipeline_id=pipeline_id,
            runtime_ok=runtime_ok,
            snapshot_ok=snapshot_ok,
            history_ok=history_ok,
            trend_ok=trend_ok,
            summary_ok=summary_ok,
            dashboard_ok=dashboard_ok,
            conversation_ok=conversation_ok,
            errors=tuple(errors),
            started_at=started_at,
            completed_at=completed_at,
        )

        self._results.append(result)
        return result
