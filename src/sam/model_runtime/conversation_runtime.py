"""Conversation Runtime — bridge conversation <-> model runtime (Sprint 246).

Program B — Model Runtime Integration.
Read-only bridge; pipeline preview, no-network.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List

from .model_runtime import ModelRuntime, ModelRuntimeResult
from .model_session import ModelSessionStore
from .model_report import ModelReport


@dataclass(frozen=True)
class ConversationRuntimeResult:
    """Hasil runtime pada konteks percakapan (immutable)."""
    conversation_id: str
    result: ModelRuntimeResult
    preview_only: bool = True
    external_calls: int = 0

    def as_dict(self) -> dict:
        return {
            "conversation_id": self.conversation_id,
            "result": self.result.as_dict(),
            "preview_only": self.preview_only,
            "external_calls": self.external_calls,
        }


class ConversationRuntime:
    """Bridge conversation <-> model runtime. Read-only."""

    def __init__(
        self,
        runtime: ModelRuntime | None = None,
        session_store: ModelSessionStore | None = None,
    ) -> None:
        self._runtime = runtime or ModelRuntime()
        self._sessions = session_store or ModelSessionStore()

    def run(self, conversation_id: str, descriptor, request) -> ConversationRuntimeResult:
        result = self._runtime.run(descriptor, request)
        return ConversationRuntimeResult(
            conversation_id=conversation_id,
            result=result,
            preview_only=True,
            external_calls=0,
        )

    def runtime(self) -> ModelRuntime:
        return self._runtime
