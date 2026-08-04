"""Runtime API (Sprint 267 + Session 01).

Program D - Runtime Services & Deployment.
Internal API — belum HTTP. Request/response/status/health.

Session 01 (Foundation Activation): tambah PreviewGateway & ExecutionPreviewProducer
sebagai jalur producer preview pertama (RuntimeAPI -> ExecutionRuntime preview).
Tetap sync, deterministic, no network; provider tidak pernah dieksekusi (preview).
"""
from __future__ import annotations

from .request import APIRequest
from .response import APIResponse
from .status import APIStatus
from .health import APIHealth
from .runtime_api import RuntimeAPI
from .preview_gateway import PreviewGateway, PreviewRequestView, PreviewOutcomeView
from .execution_preview_wiring import (
    ExecutionPreviewProducer,
    wire_execution_preview,
)
from .conversation_execution_builder import (
    ConversationExecutionContext,
    ConversationExecutionRequestBuilder,
)
from .conversation_preview_wiring import (
    ConversationPreviewGateway,
    ConversationPreviewResult,
    wire_conversation_preview,
    build_conversation_preview_gateway,
)

API_VERSION = "27.0.0"

__all__ = [
    "API_VERSION",
    "APIRequest",
    "APIResponse",
    "APIStatus",
    "APIHealth",
    "RuntimeAPI",
    "PreviewGateway",
    "PreviewRequestView",
    "PreviewOutcomeView",
    "ExecutionPreviewProducer",
    "wire_execution_preview",
    "ConversationExecutionContext",
    "ConversationExecutionRequestBuilder",
    "ConversationPreviewGateway",
    "ConversationPreviewResult",
    "wire_conversation_preview",
    "build_conversation_preview_gateway",
]
