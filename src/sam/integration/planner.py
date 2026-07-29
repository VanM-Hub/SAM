# OP-405 — Integration Planner
# Python 3.8, frozen DTO, synchronous

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Tuple
import uuid

from .contracts import IntegrationRequest, IntegrationPreview
from .registry import IntegrationRegistry


@dataclass(frozen=True)
class IntegrationStep:
    step_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    action: str = ""; target: str = ""
    integration_type: str = ""
    estimated_duration: int = 0
    requires_approval: bool = True
    risk_level: str = "low"


@dataclass(frozen=True)
class IntegrationPlan:
    plan_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    steps: Tuple[IntegrationStep, ...] = field(default_factory=tuple)
    total_steps: int = 0
    estimated_duration: int = 0
    requires_approval: bool = True
    aggregated_risk: str = "low"
    rollback_reference: str = ""


class IntegrationPlanner:
    """Creates IntegrationPlan from requests. No execution."""

    def __init__(self, registry: IntegrationRegistry):
        self._registry = registry

    def plan(self, request: IntegrationRequest) -> IntegrationPlan:
        providers = self._registry.find_by_type(request.integration_type)
        provider = providers[0] if providers else None

        risk = self._estimate_risk(request.action)
        duration = self._estimate_duration(request.action)
        requires_appr = risk in ("medium", "high", "critical")

        step = IntegrationStep(action=request.action, target=request.target,
            integration_type=request.integration_type,
            estimated_duration=duration, requires_approval=requires_appr, risk_level=risk)

        return IntegrationPlan(steps=(step,), total_steps=1,
            estimated_duration=duration, requires_approval=requires_appr,
            aggregated_risk=risk,
            rollback_reference=f"rollback://{request.integration_type}/{request.action}")

    def plan_multi(self, requests: Tuple[IntegrationRequest, ...]) -> IntegrationPlan:
        steps: List[IntegrationStep] = []
        total_dur = 0; risks = set()
        for req in requests:
            risk = self._estimate_risk(req.action)
            risks.add(risk)
            duration = self._estimate_duration(req.action)
            step = IntegrationStep(action=req.action, target=req.target,
                integration_type=req.integration_type,
                estimated_duration=duration,
                requires_approval=risk in ("medium","high","critical"),
                risk_level=risk)
            steps.append(step)
            total_dur += duration

        risk_order = {"low":0,"medium":1,"high":2,"critical":3}
        max_risk = max((risk_order.get(r,0) for r in risks), default=0)
        reverse_map = {v:k for k,v in risk_order.items()}
        agg_risk = reverse_map.get(max_risk, "low")
        requires_appr = max_risk >= 1

        return IntegrationPlan(steps=tuple(steps), total_steps=len(steps),
            estimated_duration=total_dur, requires_approval=requires_appr,
            aggregated_risk=agg_risk)

    @staticmethod
    def _estimate_risk(action: str) -> str:
        risk_map = {"read":"low","search":"low","monitor":"low","notify":"low",
                     "write":"medium","create":"medium","delete":"high","execute":"high"}
        return risk_map.get(action, "medium")

    @staticmethod
    def _estimate_duration(action: str) -> int:
        duration_map = {"read":1,"search":2,"monitor":3,"notify":1,"write":2,"create":3,"delete":2,"execute":5}
        return duration_map.get(action, 2)
