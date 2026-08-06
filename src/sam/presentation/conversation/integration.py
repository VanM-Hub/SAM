"""ENG-G-001 · G10 — Conversation Integration.

Mengintegrasikan capability Conversation yang telah selesai menjadi satu
alur presentasi sederhana. Service composition-only: menggabungkan hasil
dari command (yang sudah ter-wire ke jalur resmi runtime_service.api) —
TANPA bypass, TANPA akses langsung Runtime/Provider/Connector/Registry/
ExecutionRuntime, TANPA business logic eksekusi.

Cakupan G10 (8 capability selesai):
  workflow · policy · audit · preview · knowledge · memory · artifact · approval-status(pass-through)
Mission (G3) = dibekukan (pending Architecture Decision) — tidak dijalankan di sini.

Desain composition:
  - command (wiring G2) memegang handler yang memanggil ConversationPreviewGateway.
  - 'consumers' (resolver knowledge/workflow/artifact/memory/policy/audit) dan
    'approval_status' DITERIMA via dependency injection dari entry/web — sama
    seperti gateway. Presentation TIDAK membuat resolver sendiri, cukup
    menyusunnya. Tanpa consumer di-inject, capability dilaporkan 'unwired' dan
    tidak dipanggil (tidak memalsukan result).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Optional

from .viewmodel import ConversationViewModel
from .commands import ConversationCommand

__all__ = ["ConversationResult", "ConversationIntegration"]


@dataclass(frozen=True)
class ConversationResult:
    """Hasil terintegrasi satu alur conversation (immutable, composition)."""

    conversation_id: str = "conversation"
    mode: str = "preview"
    execution: dict = field(default_factory=dict)
    capability_results: Dict[str, Any] = field(default_factory=dict)
    capability_status: Dict[str, str] = field(default_factory=dict)
    approval: Optional[dict] = None
    mission: Optional[dict] = None  # dibekukan (pending Architecture Decision)

    def executed(self) -> bool:
        return bool(self.execution.get("executed", False))

    def as_dict(self) -> dict:
        return {
            "conversation_id": self.conversation_id,
            "mode": self.mode,
            "execution": self.execution,
            "capability_results": dict(self.capability_results),
            "capability_status": dict(self.capability_status),
            "approval": self.approval,
            "mission": self.mission,
        }


class ConversationIntegration:
    """Integrasi conversation — menggabungkan hasil command (composition-only).

    'consumers' & 'approval_status' di-inject dari entry (bukan dibuat di
    presentation). 'context_factory' membangun ConversationExecutionContext.
    """

    # Capability G10 yang dijalankan (Mission dibekukan G3).
    ACTIVE_CAPABILITIES = (
        "workflow",
        "policy",
        "audit",
        "preview",
        "knowledge",
        "memory",
        "artifact",
    )

    def __init__(
        self,
        viewmodel: ConversationViewModel,
        command: ConversationCommand,
        context_factory: Callable[[str], Any],
        consumers: Optional[Dict[str, Any]] = None,
        approval_status: Optional[Callable[[], dict]] = None,
    ) -> None:
        self._viewmodel = viewmodel
        self._command = command
        self._context_factory = context_factory
        self._consumers = consumers or {}
        self._approval_status = approval_status

    def run(self, request: str, execution_id: str) -> ConversationResult:
        """Jalankan alur conversation terintegrasi (preview, no-execute)."""
        context = self._context_factory(request)

        results: Dict[str, Any] = {}
        status: Dict[str, str] = {}
        for name in self.ACTIVE_CAPABILITIES:
            handler = self._command._handlers.get(name)
            consumer = self._consumers.get(name)
            if handler is None:
                status[name] = "unwired"
            elif name == "preview":
                # preview tidak memerlukan consumer (execution via gateway, no resolve)
                try:
                    results[name] = handler(context, None, f"{name}_1", execution_id)
                    status[name] = "ok"
                except Exception as exc:  # noqa: BLE001 — composition boundary
                    status[name] = f"error: {type(exc).__name__}"
            elif consumer is None:
                status[name] = "no_consumer"
            else:
                try:
                    results[name] = handler(context, consumer, f"{name}_1", execution_id)
                    status[name] = "ok"
                except Exception as exc:  # noqa: BLE001 — composition boundary
                    status[name] = f"error: {type(exc).__name__}"

        execution = results.get("preview")
        if not isinstance(execution, dict):
            execution = {"mode": "preview", "executed": False}

        approval = None
        if self._approval_status is not None:
            try:
                approval = self._approval_status()
            except Exception as exc:  # noqa: BLE001
                approval = {"status": f"error: {type(exc).__name__}"}

        return ConversationResult(
            conversation_id=self._viewmodel.conversation_id,
            mode="preview",
            execution=execution,
            capability_results=results,
            capability_status=status,
            approval=approval,
            mission=None,
        )
