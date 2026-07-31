"""Sprint 267 - Runtime API.

Program D - Runtime Services & Deployment.
Internal API — belum HTTP.
"""
from __future__ import annotations
import pytest

from sam.runtime_service.api.request import APIRequest
from sam.runtime_service.api.response import APIResponse
from sam.runtime_service.api.status import APIStatus
from sam.runtime_service.api.health import APIHealth
from sam.runtime_service.api.runtime_api import RuntimeAPI


def test_request_immutable():
    r = APIRequest(action="execute")
    assert r.service == "runtime"
    with pytest.raises(Exception):
        r.action = "x"
    with pytest.raises(ValueError):
        APIRequest(action="")


def test_request_as_dict():
    r = APIRequest(action="preview", payload={"n": 1}, request_id="r1")
    ad = r.as_dict()
    assert ad["action"] == "preview"
    assert ad["request_id"] == "r1"
    assert ad["payload"] == {"n": 1}


def test_response_ok():
    resp = APIResponse(request_id="r1")
    assert resp.is_ok() is True
    assert resp.status == "ok"


def test_response_error():
    resp = APIResponse(request_id="r1", status="error", error="boom")
    assert resp.is_ok() is False


def test_response_immutable():
    resp = APIResponse(request_id="r1")
    with pytest.raises(Exception):
        resp.status = "error"


def test_response_as_dict():
    resp = APIResponse(request_id="r1", data={"x": 1})
    assert resp.as_dict()["data"] == {"x": 1}
    assert resp.as_dict()["error"] is None


def test_status_immutable():
    s = APIStatus(services={"exec": "ok"})
    assert s.healthy is True
    assert s.version == "27.0.0"
    with pytest.raises(Exception):
        s.healthy = False


def test_health_healthy():
    h = APIHealth(status="healthy", checks=["runtime"])
    assert h.is_healthy() is True


def test_health_unhealthy():
    h = APIHealth(status="unhealthy")
    assert h.is_healthy() is False


def test_api_register_handle():
    api = RuntimeAPI()
    def handler(req):
        return APIResponse(request_id=req.request_id,
                           data={"ok": True})
    api.register("ping", handler)
    assert api.has("ping")
    resp = api.handle(APIRequest(action="ping"))
    assert resp.is_ok()


def test_api_unknown_action():
    api = RuntimeAPI()
    resp = api.handle(APIRequest(action="nope"))
    assert resp.is_ok() is False
    assert "unknown" in resp.error


def test_api_handler_payload():
    api = RuntimeAPI()
    def echo(req):
        return APIResponse(request_id=req.request_id,
                           data={"got": req.payload.get("v")})
    api.register("echo", echo)
    resp = api.handle(APIRequest(action="echo", payload={"v": 42}))
    assert resp.data["got"] == 42


def test_api_status_report():
    api = RuntimeAPI()
    api.register("a", lambda req: APIResponse(req.request_id))
    s = api.status()
    assert "a" in s.services
    assert s.healthy is True


def test_api_health():
    api = RuntimeAPI()
    h = api.health()
    assert h.is_healthy() is False  # no handlers
    api.register("a", lambda req: APIResponse(req.request_id))
    h2 = api.health()
    assert h2.is_healthy() is True


def test_no_http_in_api():
    import inspect
    from sam.runtime_service.api import runtime_api
    src = inspect.getsource(runtime_api)
    assert "FastAPI" not in src
    assert "Flask" not in src
    assert "http.server" not in src
    assert "socket" not in src


def test_request_response_roundtrip():
    req = APIRequest(action="run", request_id="rid-9")
    resp = APIResponse(request_id=req.request_id, data={"echo": req.action})
    assert resp.as_dict()["request_id"] == "rid-9"
    assert resp.data["echo"] == "run"
