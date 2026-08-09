"""Execution Preview Wiring (Session 01 - Foundation Activation).

Program D - Runtime Services & Deployment.
Menyambungkan RuntimeAPI ke ExecutionRuntime (producer preview pertama).

PENTING (batas Session 01):
- Modul ini menerima ExecutionEngine via dependency injection (parameter),
  TIDAK mengimpor execution_runtime/execution apapun. Dengan begitu
  RuntimeService tetap gateway; ia tidak mengetahui provider/execution.
- Producer menghasilkan ExecutionRequest(mode="preview") dan memanggil
  engine.execute(). Provider TIDAK dieksekusi (mode preview bukan execute),
  no network, approval pre-aware. Konsisten ADR-008 sec 12.
- Alur: RuntimeAPI(action="execution.preview")
         -> PreviewGateway -> producer (dari wiring)
         -> ExecutionRequest(mode="preview")
         -> ExecutionRuntime.run() -> outcome preview
"""
from __future__ import annotations
from typing import Any, Callable

from .preview_gateway import PreviewGateway, PreviewRequestView, PreviewOutcomeView
from .runtime_api import RuntimeAPI


class ExecutionPreviewProducer:
    """Producer preview ExecutionRuntime (dipasok ke PreviewGateway via DI).

    Caller menyuntikkan build_request + execute (implementasi execution)
    dari luar; modul ini hanya orkestrasi tipis untuk mode preview.
    Provider tidak pernah dieksekusi.
    """

    def __init__(self,
                 build_request: Callable[[PreviewRequestView], Any],
                 execute: Callable[[Any], Any]) -> None:
        self._build_request = build_request
        self._execute = execute

    def __call__(self, view: PreviewRequestView) -> PreviewOutcomeView:
        request = self._build_request(view)
        outcome = self._execute(request)
        # MAPPING OUTCOME -> PREVIEW VIEW (hanya metadata preview)
        return self._to_outcome_view(outcome)

    def _to_outcome_view(self, outcome: Any) -> PreviewOutcomeView:
        # outcome: ExecutionOutcome (execution_runtime) dengan as_dict()
        data = getattr(outcome, "as_dict", lambda: {})()
        return PreviewOutcomeView(
            runtime_id=str(data.get("runtime_id", "")),
            approved=bool(data.get("approved", False)),
            executed=bool(data.get("executed", False)),
            external_calls=int(data.get("external_calls", 0)),
            mode="preview",
            status="preview",
        )


def wire_execution_preview(api: RuntimeAPI,
                           build_request: Callable[[PreviewRequestView], Any],
                           execute: Callable[[Any], Any]) -> PreviewGateway:
    """Wiring RuntimeAPI -> ExecutionRuntime preview.

    Menerima ExecutionEngine sudah dibangun di luar (via build_request/execute).
    """
    gateway = PreviewGateway(api)
    producer = ExecutionPreviewProducer(build_request, execute)
    gateway.bind_producer(producer)
    gateway.register()
    return gateway
