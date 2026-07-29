# OP-408 — Integration Runtime Pipeline
# Python 3.8, frozen DTO, synchronous, preview only

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any, Tuple
import uuid

from .contracts import IntegrationRequest, IntegrationResponse, IntegrationPreview
from .registry import IntegrationRegistry
from .provider import *
from .policy import IntegrationPolicyEngine, PolicyResult
from .planner import IntegrationPlanner, IntegrationPlan
from .conversation import ConversationIntegrationBridge, IntegrationQueryResult
from .dashboard import DashboardIntegrationBuilder, IntegrationDashboard


@dataclass(frozen=True)
class IntegrationPipelineResult:
    pipeline_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    plan: Optional[IntegrationPlan] = None
    preview: Optional[IntegrationResponse] = None
    policy: Optional[PolicyResult] = None
    conversation: Optional[IntegrationQueryResult] = None
    dashboard: Optional[IntegrationDashboard] = None
    pipeline_complete: bool = False; error: str = ""
    timestamp: datetime = field(default_factory=datetime.utcnow)


class IntegrationRuntime:
    """Pipeline: Registry → Provider → Policy → Planner → Conversation → Dashboard.

    No execution — preview only.
    """

    def __init__(self, registry: Optional[IntegrationRegistry] = None,
                 policy: Optional[IntegrationPolicyEngine] = None,
                 planner: Optional[IntegrationPlanner] = None,
                 conversation: Optional[ConversationIntegrationBridge] = None,
                 dashboard: Optional[DashboardIntegrationBuilder] = None):
        self._registry = registry or IntegrationRegistry()
        self._policy = policy or IntegrationPolicyEngine()
        self._planner = planner or IntegrationPlanner(self._registry)
        self._conversation = conversation or ConversationIntegrationBridge(
            self._registry, self._planner, self._policy)
        self._dashboard = dashboard or DashboardIntegrationBuilder()

    def ensure_registered(self) -> None:
        if self._registry.count == 0:
            for prov in [MockSlackIntegration(), MockDiscordIntegration(), MockEmailIntegration(),
                         MockWebhookIntegration(), MockRESTIntegration(), MockFilesystemIntegration()]:
                self._registry.register(prov)

    def execute_preview(self, request: IntegrationRequest) -> IntegrationPipelineResult:
        try:
            plan = self._planner.plan(request)

            providers = self._registry.find_by_type(request.integration_type)
            preview = providers[0].preview(request) if providers else None

            policy_result = self._policy.evaluate(
                integration_type=request.integration_type, action=request.action,
                risk_level=plan.aggregated_risk,
                provider_healthy=providers[0].descriptor.healthy if providers else False)

            conv = self._conversation.query("diagnostics")
            dash = self._dashboard.build(self._registry, self._policy)

            return IntegrationPipelineResult(plan=plan, preview=preview, policy=policy_result,
                conversation=conv, dashboard=dash, pipeline_complete=True)
        except Exception as e:
            return IntegrationPipelineResult(pipeline_complete=False, error=str(e))
