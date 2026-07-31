"""Sprint 268 - Server Runtime.

Program D - Runtime Services & Deployment.
Menggabungkan Runtime, Connector, Provider, Execution.
Belum HTTP listening.
"""
from __future__ import annotations
import pytest

from sam.runtime_service.server.server_runtime import (
    ServerRuntime, ComponentStatus,
)
from sam.runtime_service.server.startup import ServerStartup
from sam.runtime_service.server.shutdown import ServerShutdown
from sam.runtime_service.server.status import ServerStatus
from sam.runtime_service.server.health import ServerHealth, build_server_health


def test_server_runtime_default():
    s = ServerRuntime()
    assert s.name == "sam-server"
    assert s.status == "created"
    assert s.started is False
    assert set(s.layers) == {"runtime", "connector", "provider", "execution"}


def test_server_register_component():
    s = ServerRuntime()
    s.register_component("connector")
    s.register_component("provider")
    assert len(s.components()) == 2


def test_server_duplicate_component():
    s = ServerRuntime()
    s.register_component("a")
    with pytest.raises(ValueError):
        s.register_component("a")


def test_server_mark_ready():
    s = ServerRuntime()
    s.register_component("connector")
    s.mark_ready("connector", detail="ok")
    assert s.all_ready() is True


def test_server_not_all_ready():
    s = ServerRuntime()
    s.register_component("a")
    s.register_component("b")
    s.mark_ready("a")
    assert s.all_ready() is False


def test_server_mark_unknown_component():
    s = ServerRuntime()
    s.register_component("a")
    with pytest.raises(KeyError):
        s.mark_ready("nope")


def test_server_empty_all_ready():
    s = ServerRuntime()
    assert s.all_ready() is True


def test_startup_run():
    s = ServerRuntime()
    su = ServerStartup(s)
    su.run()
    assert s.started is True
    assert su.done is True


def test_startup_idempotent():
    s = ServerRuntime()
    su = ServerStartup(s)
    su.run()
    su.run()  # kedua kali tidak reset
    assert s.started is True


def test_shutdown_run():
    s = ServerRuntime()
    s.set_started(True)
    sd = ServerShutdown(s)
    sd.run()
    assert s.started is False
    assert sd.done is True


def test_component_status_immutable():
    c = ComponentStatus(name="x", ready=True)
    assert c.ready is True
    with pytest.raises(Exception):
        c.ready = False


def test_server_status_dataclass():
    st = ServerStatus(name="srv", status="running", started=True)
    assert st.as_dict()["name"] == "srv"
    assert st.as_dict()["started"] is True
    assert st.version == "27.0.0"


def test_server_health_healthy():
    h = ServerHealth(status="healthy")
    assert h.is_healthy() is True


def test_server_health_degraded():
    h = ServerHealth(status="degraded")
    assert h.is_healthy() is False


def test_build_health_healthy():
    s = ServerRuntime()
    s.register_component("connector")
    s.mark_ready("connector")
    h = build_server_health(s)
    assert h.is_healthy() is True
    assert "connector" in h.checks


def test_build_health_degraded():
    s = ServerRuntime()
    s.register_component("a")
    s.register_component("b")
    s.mark_ready("a")
    h = build_server_health(s)
    assert h.is_healthy() is False


def test_no_http_listening_in_server():
    import inspect
    from sam.runtime_service.server import server_runtime
    src = inspect.getsource(server_runtime)
    assert "bind(" not in src
    assert "listen(" not in src
    assert "socket" not in src


def test_server_full_flow():
    s = ServerRuntime()
    for comp in ("connector", "provider", "execution"):
        s.register_component(comp)
    for comp in ("connector", "provider", "execution"):
        s.mark_ready(comp)
    su = ServerStartup(s)
    su.run()
    assert s.started is True
    assert s.all_ready() is True
    sd = ServerShutdown(s)
    sd.run()
    assert s.started is False
