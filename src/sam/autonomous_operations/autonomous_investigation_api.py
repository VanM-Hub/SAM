"""Autonomous Investigation API - WP-07 (MISSION-4.5 / IP-4.5-001).

Antarmuka standar untuk Autonomous Investigation. API konsisten, read-only,
dapat diintegrasikan, tidak melakukan authority escalation.
"""
from __future__ import annotations

from typing import Any, Dict, Optional, Tuple

from .autonomous_investigation import AutonomousInvestigationEngine
from .context_collection import ContextCollector
from .investigation_trigger import TriggerEvaluationEngine
from .verification import (
    ProviderVerificationEngine,
    RuntimeVerificationEngine,
)
from .investigation_planning import InvestigationPlanner, InvestigationPlan


class TriggerAPI:
    """API trigger (read-only)."""

    def __init__(self, engine: TriggerEvaluationEngine) -> None:
        self._engine = engine

    def audit(self) -> Tuple[Dict[str, Any], ...]:
        return tuple(e.as_dict() for e in self._engine.audit())


class ContextAPI:
    """API konteks (read-only)."""

    def __init__(self, collector: ContextCollector) -> None:
        self._collector = collector

    def snapshot(self) -> Dict[str, Any]:
        snap = self._collector.last_snapshot()
        return snap.as_dict() if snap else {}


class VerificationAPI:
    """API verifikasi (read-only)."""

    def __init__(
        self,
        runtime: RuntimeVerificationEngine,
        provider: ProviderVerificationEngine,
    ) -> None:
        self._runtime = runtime
        self._provider = provider

    def runtime_report(self) -> Tuple[Dict[str, Any], ...]:
        return tuple(e.as_dict() for e in self._runtime.report())

    def provider_report(self) -> Tuple[Dict[str, Any], ...]:
        return tuple(e.as_dict() for e in self._provider.report())


class PlanningAPI:
    """API perencanaan (read-only)."""

    def __init__(self, planner: InvestigationPlanner) -> None:
        self._planner = planner

    def plan(self, plan: InvestigationPlan) -> Dict[str, Any]:
        return plan.as_dict()

    def explain(self, plan: InvestigationPlan) -> Dict[str, Any]:
        return self._planner.explain(plan).as_dict()


class AutonomousInvestigationAPI:
    """Facade read-only untuk Autonomous Investigation."""

    def __init__(
        self,
        *,
        engine: AutonomousInvestigationEngine,
        trigger: TriggerEvaluationEngine,
        context: ContextCollector,
        runtime_verify: RuntimeVerificationEngine,
        provider_verify: ProviderVerificationEngine,
        planner: InvestigationPlanner,
    ) -> None:
        self._engine = engine
        self.trigger = TriggerAPI(trigger)
        self.context = ContextAPI(context)
        self.verification = VerificationAPI(runtime_verify, provider_verify)
        self.planning = PlanningAPI(planner)

    def list_investigations(self) -> Tuple[Dict[str, Any], ...]:
        return tuple(i.as_dict() for i in self._engine.all())

    def get_investigation(self, investigation_id: str) -> Optional[Dict[str, Any]]:
        inv = self._engine.get(investigation_id)
        return inv.as_dict() if inv else None

    def metrics(self) -> Dict[str, Any]:
        return self._engine.metrics()
