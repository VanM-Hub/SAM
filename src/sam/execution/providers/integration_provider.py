# OP-448 — Integration Provider Pipeline
# Python 3.8, frozen DTO, synchronous, preview only

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple
import uuid

from .provider_protocol import ProviderRequest, ProviderResponse, BaseProvider
from .provider_registry import ProviderRegistry
from .provider_router import ProviderRouter, RouteDecision, RoutingSummary
from .provider_validator import ProviderValidator, ProviderValidationReport
from .conversation_provider import ConversationProviderBridge, ProviderQueryResult
from .dashboard_provider import ProviderDashboardBuilder, ProviderDashboard
from .mock_providers import *
from sam.execution.adapters.execution_envelope import ExecutionEnvelope, ExecutionEnvelopeBuilder
from sam.execution.dispatch.dispatch_request import DispatchRequest, DispatchTask


@dataclass(frozen=True)
class ProviderPipelineResult:
    pipeline_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    route_decision: Optional[RouteDecision] = None
    validation: Optional[ProviderValidationReport] = None
    preview: Optional[ProviderResponse] = None
    conversation_result: Optional[ProviderQueryResult] = None
    dashboard: Optional[ProviderDashboard] = None
    pipeline_complete: bool = False; error: str = ""
    timestamp: datetime = field(default_factory=datetime.utcnow)


class ProviderIntegrationPipeline:
    """Pipeline: Envelope → Adapter → Provider Registry → Router → Validator → Mock Provider → Guardian → Conversation → Dashboard

    No real execution — preview only.
    """

    def __init__(self, registry: Optional[ProviderRegistry] = None,
                 router: Optional[ProviderRouter] = None,
                 validator: Optional[ProviderValidator] = None,
                 conversation: Optional[ConversationProviderBridge] = None,
                 dashboard_builder: Optional[ProviderDashboardBuilder] = None):
        self._registry = registry or ProviderRegistry()
        self._router = router or ProviderRouter(self._registry)
        self._validator = validator or ProviderValidator(self._registry)
        self._conversation = conversation or ConversationProviderBridge(self._registry,self._router,self._validator)
        self._dashboard_builder = dashboard_builder or ProviderDashboardBuilder()

    def ensure_registered(self) -> None:
        if self._registry.count == 0:
            for prov in [MockFilesystemProvider(), MockProcessProvider(), MockHttpProvider(),
                         MockDatabaseProvider(), MockNotificationProvider()]:
                self._registry.register(prov)

    def run(self, envelope: ExecutionEnvelope,
            preferred_type: Optional[str] = None) -> ProviderPipelineResult:
        try:
            route = self._router.route(envelope, preferred_type)
            rep = self._validator.validate(envelope, route.selected_provider_type) if route.selected_provider_type else \
                ProviderValidator(self._registry).validate(envelope, "filesystem")
            preview = route.preview_response
            conv = self._conversation.query("provider summary")

            decisions = (route,)
            rs = self._router.get_summary(decisions)
            dash = self._dashboard_builder.build(self._registry, rs, preview)

            return ProviderPipelineResult(route_decision=route, validation=rep,
                preview=preview, conversation_result=conv, dashboard=dash, pipeline_complete=True)

        except Exception as e:
            return ProviderPipelineResult(pipeline_complete=False, error=str(e))

    def run_from_tasks(self, tasks, preferred_type: str = "filesystem") -> ProviderPipelineResult:
        d = DispatchRequest(tasks=tuple(tasks), requires_approval=False)
        env = ExecutionEnvelopeBuilder.build(d)
        return self.run(env, preferred_type)
