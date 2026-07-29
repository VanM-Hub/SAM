# OP-438 — Integration Adapter Pipeline
# Python 3.8, frozen DTO, synchronous, no real execution

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple
import uuid

from .execution_envelope import (
    ExecutionEnvelope, ExecutionEnvelopeBuilder, ExecutionEnvelopeMetadata,
)
from .adapter_protocol import (
    MockAdapter, AdapterMetadata, AdapterCapability, AdapterResult, AdapterHealth,
)
from .adapter_registry import AdapterRegistry, AdapterSelector
from .adapter_preview import PreviewAdapter, PreviewResult, PreviewSummary
from .adapter_validator import AdapterValidator, AdapterValidationReport
from .conversation_adapter import ConversationAdapterBridge, AdapterQueryResult
from .dashboard_adapter import AdapterDashboardBuilder, AdapterDashboard

from sam.execution.dispatch.dispatch_request import DispatchRequest


@dataclass(frozen=True)
class AdapterPipelineResult:
    pipeline_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    envelope: Optional[ExecutionEnvelope] = None
    validation: Optional[AdapterValidationReport] = None
    preview: Optional[PreviewResult] = None
    conversation_result: Optional[AdapterQueryResult] = None
    dashboard: Optional[AdapterDashboard] = None
    pipeline_complete: bool = False
    error: str = ""
    timestamp: datetime = field(default_factory=datetime.utcnow)


class AdapterIntegrationPipeline:
    """Pipeline: Dispatch → Envelope → Adapter → Validation → Preview → Guardian → Conversation → Dashboard.

    No real execution — produces envelope, validation, preview.
    """

    def __init__(
        self,
        registry: Optional[AdapterRegistry] = None,
        validator: Optional[AdapterValidator] = None,
        preview: Optional[PreviewAdapter] = None,
        conversation_bridge: Optional[ConversationAdapterBridge] = None,
        dashboard_builder: Optional[AdapterDashboardBuilder] = None,
    ) -> None:
        self._registry = registry or AdapterRegistry()
        self._validator = validator or AdapterValidator(self._registry)
        self._preview = preview or PreviewAdapter()
        self._conversation = conversation_bridge or ConversationAdapterBridge(
            self._registry, self._validator, self._preview,
        )
        self._dashboard_builder = dashboard_builder or AdapterDashboardBuilder()

    def run(
        self,
        dispatch: DispatchRequest,
        adapter_type: str = "mock",
        approval_valid: bool = False,
        guardian_passed: bool = False,
    ) -> AdapterPipelineResult:
        try:
            # Build envelope
            env = ExecutionEnvelopeBuilder.build(dispatch, adapter_type)

            # Validate
            report = self._validator.validate(
                env, adapter_type,
                approval_valid=approval_valid,
                guardian_passed=guardian_passed,
            )

            # Preview
            preview_result = self._preview.preview(env)

            # Conversation
            conv = self._conversation.query("adapter readiness")

            # Dashboard
            dash = self._dashboard_builder.build(
                self._registry, preview_result,
                validation_passed=report.passed,
                validation_errors=report.errors,
                validation_warnings=report.warnings,
            )

            return AdapterPipelineResult(
                envelope=env,
                validation=report,
                preview=preview_result,
                conversation_result=conv,
                dashboard=dash,
                pipeline_complete=True,
            )

        except Exception as e:
            return AdapterPipelineResult(
                pipeline_complete=False,
                error=str(e),
            )

    def ensure_registered(self) -> None:
        """Register MockAdapter if no adapters exist."""
        if self._registry.count == 0:
            self._registry.register(MockAdapter())
