"""Session 01 - RuntimeAPI -> ExecutionRuntime (producer preview pertama).

Foundation Activation.
PreviewGateway + ExecutionPreviewProducer menyambungkan RuntimeAPI ke
ExecutionRuntime, menghasilkan producer preview pertama. Provider TIDAK
pernah dieksekusi (mode selalu 'preview', konsisten ADR-024). RuntimeService
tetap gateway (tidak mengimpor execution_runtime).
"""
from __future__ import annotations
import inspect

import pytest

from sam.runtime_service.api import (
    RuntimeAPI,
    APIRequest,
    PreviewGateway,
    PreviewRequestView,
    PreviewOutcomeView,
    wire_execution_preview,
)
from sam.execution_runtime.execution_engine import ExecutionEngine
from sam.execution_runtime.execution_request import ExecutionRequest


def _build_req(view: PreviewRequestView) -> ExecutionRequest:
    return ExecutionRequest(
        execution_id=view.execution_id,
        provider_id=view.provider_id,
        operation=view.operation,
        mode="preview",
    )


def _execute(engine):
    return lambda request: engine.execute(request)


@pytest.fixture
def wired():
    api = RuntimeAPI()
    engine = ExecutionEngine()
    gateway = wire_execution_preview(
        api,
        build_request=_build_req,
        execute=_execute(engine),
    )
    return api, gateway


def test_producer_preview_bound(wired):
    api, gateway = wired
    assert gateway.has_producer() is True
    assert api.has("execution.preview") is True


def test_preview_first_producer_executes_preview(wired):
    api, _ = wired
    resp = api.handle(APIRequest(
        action="execution.preview", request_id="r1",
        payload={"execution_id": "e1", "provider_id": "filesystem", "operation": "list"},
    ))
    assert resp.is_ok()
    assert resp.data["executed"] is False       # tidak ada eksekusi nyata
    assert resp.data["external_calls"] == 0     # no network / no provider call
    assert resp.data["mode"] == "preview"
    assert resp.data["status"] == "preview"
    assert "runtime_id" in resp.data


def test_preview_never_executes_even_if_mode_execute(wired):
    api, _ = wired
    # payload membawa mode='execute' TAPI gateway tetap paksa preview
    resp = api.handle(APIRequest(
        action="execution.preview", request_id="r2",
        payload={"execution_id": "e2", "provider_id": "shell",
                 "operation": "run", "mode": "execute"},
    ))
    assert resp.is_ok()
    assert resp.data["executed"] is False
    assert resp.data["mode"] == "preview"
    assert resp.data["external_calls"] == 0


def test_preview_requires_fields(wired):
    api, _ = wired
    resp = api.handle(APIRequest(
        action="execution.preview", request_id="r3", payload={}))
    assert resp.is_ok() is False
    assert "requires" in resp.error
    resp2 = api.handle(APIRequest(
        action="execution.preview", request_id="r4",
        payload={"execution_id": "e", "provider_id": "", "operation": "x"}))
    assert resp2.is_ok() is False


def test_preview_gateway_unknown_action(wired):
    api, _ = wired
    resp = api.handle(APIRequest(action="nope", request_id="r5"))
    assert resp.is_ok() is False
    assert "unknown" in resp.error


def test_preview_gateway_no_producer():
    api = RuntimeAPI()
    g = PreviewGateway(api)
    g.register()
    resp = api.handle(APIRequest(
        action="execution.preview", request_id="r6",
        payload={"execution_id": "e", "provider_id": "p", "operation": "o"}))
    assert resp.is_ok() is False
    assert "no preview producer" in resp.error


def test_outcome_view_immutable():
    v = PreviewOutcomeView(runtime_id="r", approved=False,
                           executed=False, external_calls=0, mode="preview")
    with pytest.raises(Exception):
        v.executed = True   # immutable
    d = v.as_dict()
    assert d["mode"] == "preview"
    assert d["executed"] is False


def test_runtime_service_module_does_not_import_execution():
    """Modul preview_gateway & execution_preview_wiring TIDAK mengimpor execution_runtime."""
    from sam.runtime_service.api import preview_gateway, execution_preview_wiring
    for mod in (preview_gateway, execution_preview_wiring):
        src = inspect.getsource(mod)
        import_lines = [l for l in src.splitlines()
                        if l.strip().startswith(("import", "from"))]
        joined = " ".join(import_lines).lower()
        assert "execution_runtime" not in joined
        assert "execution_engine" not in joined
        assert "providers" not in joined
