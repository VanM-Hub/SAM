"""ENG-G-001 · G2 — Conversation: RuntimeService wiring.

Menghubungkan Conversation (presentation) ke jalur resmi runtime_service.
Gateway `ConversationPreviewGateway` (pada package runtime_service.api)
DITERIMA via dependency injection dari entry/web — presentation TIDAK
membuat gateway, TIDAK membangun RuntimeAPI, TIDAK mengakses Runtime /
Provider / Connector / Registry / ExecutionRuntime secara langsung.

Alur (sesuai Arch Package):
    Presentation -> Conversation -> runtime_service(ConversationPreviewGateway)
    -> RuntimeService (single entry) -> Existing Runtime Citizens (preview).

G2: pasang handler akses per-capability pada ConversationCommand, semua
mengarah ke gateway yang di-inject. Handler tetap composition — memanggil
gateway (jalur resmi), bukan runtime.
"""
from __future__ import annotations

from typing import Any, Callable, Dict, Optional

# Satu-satunya dependency keluar: package runtime_service (diizinkan Arch Package).
from sam.runtime_service.api import (
    ConversationPreviewGateway,
    ConversationExecutionContext,
    ConversationExecutionRequestBuilder,
)

from .viewmodel import ConversationViewModel
from .commands import ConversationCommand

__all__ = ["ConversationRuntimeWiring", "wire_conversation_runtime"]


def _make_handler(
    gateway: ConversationPreviewGateway,
    kind: str,
) -> Callable[..., Any]:
    """Factory handler composition — memanggil jalur gateway (runtime_service)."""
    if kind == "preview":

        def _preview(context, consumer, resource_id: str, execution_id: str):
            # Signature seragam (context, consumer, resource_id, execution_id).
            # consumer tidak dipakai preview (execution tidak memerlukan resolver).
            # executable context via builder (jalur resmi runtime_service)
            request = ConversationExecutionRequestBuilder().build(
                context=context,
                provider_id="filesystem",
                operation="conversation.preview",
                execution_id=execution_id,
            )
            return gateway.preview(context=context, execution_id=execution_id).as_dict()

        return _preview

    _dispatch = {
        "knowledge": "preview_with_knowledge",
        "workflow": "preview_with_workflow",
        "artifact": "preview_with_artifact",
        "memory": "preview_with_memory",
        "policy": "preview_with_policy",
        "audit": "preview_with_audit",
    }
    method = getattr(gateway, _dispatch.get(kind, ""), None)

    if kind == "knowledge":

        def _knowledge(context, consumer, knowledge_id, execution_id, memory_id=""):
            return gateway.preview_with_knowledge(
                context, consumer, knowledge_id, execution_id, memory_id
            )

        return _knowledge
    if kind == "workflow":

        def _workflow(context, consumer, workflow_id, execution_id, kc=None, kid=""):
            return gateway.preview_with_workflow(
                context, consumer, workflow_id, execution_id, kc, kid
            )

        return _workflow
    if kind == "artifact":

        def _artifact(context, consumer, artifact_name, execution_id):
            return gateway.preview_with_artifact(
                context, consumer, artifact_name, execution_id
            )

        return _artifact
    if kind == "memory":

        def _memory(context, consumer, memory_id, execution_id):
            return gateway.preview_with_memory(context, consumer, memory_id, execution_id)

        return _memory
    if kind == "policy":

        def _policy(context, consumer, policy_id, execution_id):
            return gateway.preview_with_policy(context, consumer, policy_id, execution_id)

        return _policy
    if kind == "audit":

        def _audit(context, consumer, audit_id, execution_id):
            return gateway.preview_with_audit(context, consumer, audit_id, execution_id)

        return _audit

    # mission belum ada jalur preview khusus di gateway -> handler placeholder
    # (untuk G3, mission akan memakai jalur yang sesuai; di sini composition saja).
    return lambda *_a, **_k: {"capability": kind, "status": "preview"}


class ConversationRuntimeWiring:
    """Wiring Conversation -> gateway runtime_service (injected). Read-only."""

    def __init__(
        self,
        gateway: ConversationPreviewGateway,
        command: ConversationCommand,
        viewmodel: ConversationViewModel,
    ) -> None:
        self._gateway = gateway
        self._command = command
        self._viewmodel = viewmodel
        for name in command.names():
            command.attach(name, _make_handler(gateway, name))

    @property
    def gateway(self) -> ConversationPreviewGateway:
        return self._gateway

    def attached(self) -> dict:
        return {name: self._command.has_handler(name) for name in self._command.names()}

    def as_dict(self) -> dict:
        return {
            "wired": True,
            "via": "runtime_service.api.ConversationPreviewGateway",
            "attached": self.attached(),
            "capabilities": self._viewmodel.as_dict()["capabilities"],
        }


def wire_conversation_runtime(
    gateway: ConversationPreviewGateway,
    command: ConversationCommand,
    viewmodel: Optional[ConversationViewModel] = None,
) -> ConversationRuntimeWiring:
    """Wire Conversation ke gateway (dependency injection dari entry)."""
    if viewmodel is None:
        viewmodel = ConversationViewModel()
    return ConversationRuntimeWiring(gateway, command, viewmodel)
