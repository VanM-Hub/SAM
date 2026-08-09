"""Preview Gateway (Session 01 - Foundation Activation).

Program D - Runtime Services & Deployment.
Gateway PREVIEW eksekusi untuk RuntimeAPI -> ExecutionRuntime.

Menghubungkan RuntimeAPI (gateway kontrak) dengan ExecutionRuntime sebagai
producer preview pertama, TANPA menjadikan RuntimeService executor:

- Modul ini TIDAK mengimpor execution_runtime / execution apapun.
- Handler preview menerima callable producer yang di-inject dari luar
  (dependency injection) — sehingga RuntimeService tetap gateway.
- Hanya mode="preview": tidak network, tidak execute, approval pre-aware.
  Provider tidak pernah dieksekusi (mode preview bukan execute).
- Konsisten ADR-008 sec 12 (preview-only) & D0-001 (RuntimeService = gateway).
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Callable, Optional

from .request import APIRequest
from .response import APIResponse
from .runtime_api import RuntimeAPI


@dataclass(frozen=True)
class PreviewRequestView:
    """View request preview (immutable). Provider tidak dieksekusi."""
    execution_id: str
    provider_id: str
    operation: str
    mode: str = "preview"
    preview: bool = True


@dataclass(frozen=True)
class PreviewOutcomeView:
    """Outcome preview (immutable). Tidak ada eksekusi nyata."""
    runtime_id: str
    approved: bool = False
    executed: bool = False
    external_calls: int = 0
    mode: str = "preview"
    status: str = "preview"

    def as_dict(self) -> dict:
        return {
            "runtime_id": self.runtime_id,
            "approved": self.approved,
            "executed": self.executed,
            "external_calls": self.external_calls,
            "mode": self.mode,
            "status": self.status,
        }


class PreviewGateway:
    """Gateway preview eksekusi (RuntimeAPI -> ExecutionRuntime preview).

    Handler preview didaftarkan ke RuntimeAPI. Produksi request preview
    dilakukan oleh callable yang di-inject (dependency injection) di wiring,
    sehingga modul ini tidak bergantung ke implementation execution.
    """

    def __init__(self, api: RuntimeAPI) -> None:
        self._api = api
        # placeholder producer — di-bind saat wiring
        self._producer: Optional[Callable[[PreviewRequestView], PreviewOutcomeView]] = None

    @property
    def api(self) -> RuntimeAPI:
        return self._api

    def bind_producer(self, producer: Callable[[PreviewRequestView], PreviewOutcomeView]) -> None:
        """Suntik producer preview (dependency injection)."""
        self._producer = producer

    def has_producer(self) -> bool:
        return self._producer is not None

    def register(self) -> None:
        """Daftarkan handler 'execution.preview' ke RuntimeAPI."""
        self._api.register("execution.preview", self._handle_preview)

    def _handle_preview(self, request: APIRequest) -> APIResponse:
        payload = request.payload
        try:
            view = PreviewRequestView(
                execution_id=str(payload.get("execution_id", "")),
                provider_id=str(payload.get("provider_id", "")),
                operation=str(payload.get("operation", "")),
                mode="preview",
                preview=True,
            )
        except Exception as exc:  # pragma: no cover
            return APIResponse(request_id=request.request_id, status="error", error=str(exc))
        if not view.execution_id or not view.provider_id or not view.operation:
            return APIResponse(
                request_id=request.request_id, status="error",
                error="preview requires execution_id, provider_id, operation",
            )
        if self._producer is None:
            return APIResponse(
                request_id=request.request_id, status="error",
                error="no preview producer bound",
            )
        outcome = self._producer(view)
        return APIResponse(
            request_id=request.request_id,
            status="ok",
            data=outcome.as_dict(),
        )
