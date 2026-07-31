"""Sprint 261 - Runtime Service Foundation.

Program D - Runtime Services & Deployment.
"""
from __future__ import annotations
import pytest

from sam.runtime_service.descriptor import RuntimeServiceDescriptor
from sam.runtime_service.metadata import RuntimeServiceMetadata
from sam.runtime_service.contract import RuntimeServiceContract
from sam.runtime_service.configuration import RuntimeServiceConfiguration
from sam.runtime_service.service_registry import RuntimeServiceRegistry
from sam.runtime_service.runtime_service import RuntimeService, RuntimeServiceState
from sam.runtime_service.conversation_runtime_service import (
    ConversationRuntimeService, ConversationRuntimeServiceDescriptor,
)
from sam.runtime_service.dashboard_runtime_service import DashboardRuntimeService


def test_descriptor_immutable_and_type():
    d = RuntimeServiceDescriptor(name="svc-a", service_type="runtime")
    assert d.service_type == "runtime"
    assert d.version == "27.0.0"
    with pytest.raises(Exception):
        d.name = "x"
    with pytest.raises(ValueError):
        RuntimeServiceDescriptor(name="svc", service_type="bogus")


def test_descriptor_as_dict():
    d = RuntimeServiceDescriptor(name="svc-b", tags=["t1"])
    ad = d.as_dict()
    assert ad["name"] == "svc-b"
    assert ad["requires_configuration"] is True
    assert ad["tags"] == ["t1"]


def test_metadata_immutable():
    m = RuntimeServiceMetadata(service_id="s1", name="SVC")
    assert m.version == "27.0.0"
    assert m.architecture == "runtime-service"
    with pytest.raises(Exception):
        m.name = "x"
    with pytest.raises(ValueError):
        RuntimeServiceMetadata(service_id="", name="x")


def test_metadata_labels_capabilities():
    m = RuntimeServiceMetadata(
        service_id="s2", name="SVC2", labels={"a": "1"},
        capabilities=["runtime", "preview"],
    )
    assert m.as_dict()["labels"] == {"a": "1"}
    assert m.as_dict()["capabilities"] == ["runtime", "preview"]


def test_contract_validation():
    c = RuntimeServiceContract(service="svc")
    assert c.validate() is True
    assert c.immutable and c.synchronous and c.deterministic
    assert c.network_allowed is False


def test_contract_rejects_network():
    with pytest.raises(ValueError):
        RuntimeServiceContract(service="svc", network_allowed=True)


def test_contract_as_dict():
    c = RuntimeServiceContract(service="svc", layers=["runtime"])
    ad = c.as_dict()
    assert ad["service"] == "svc"
    assert ad["preview_first"] is True
    assert ad["approval_required"] is True


def test_configuration_immutable_and_defaults():
    cfg = RuntimeServiceConfiguration(service="svc")
    assert cfg.profile == "default"
    assert cfg.enabled is True
    assert cfg.timeout_seconds == 30
    with pytest.raises(Exception):
        cfg.enabled = False
    with pytest.raises(ValueError):
        RuntimeServiceConfiguration(service="svc", max_retries=-1)


def test_configuration_get():
    cfg = RuntimeServiceConfiguration(service="svc", options={"port": 8080})
    assert cfg.get("port") == 8080
    assert cfg.get("missing", "fallback") == "fallback"
    assert cfg.as_dict()["profile"] == "default"


def test_registry_register_get_list():
    reg = RuntimeServiceRegistry()
    d1 = RuntimeServiceDescriptor(name="svc-1")
    d2 = RuntimeServiceDescriptor(name="svc-2")
    reg.register(d1, order=2)
    reg.register(d2, order=1)
    assert reg.has("svc-1")
    assert reg.count() == 2
    assert reg.names() == ["svc-2", "svc-1"]  # sorted by order
    assert reg.get("svc-2").name == "svc-2"


def test_registry_duplicate_rejected():
    reg = RuntimeServiceRegistry()
    reg.register(RuntimeServiceDescriptor(name="dup"))
    with pytest.raises(ValueError):
        reg.register(RuntimeServiceDescriptor(name="dup"))


def test_registry_disabled_excluded():
    reg = RuntimeServiceRegistry()
    reg.register(RuntimeServiceDescriptor(name="a"), enabled=False)
    reg.register(RuntimeServiceDescriptor(name="b"), enabled=True)
    assert reg.names() == ["b"]


def test_runtime_service_initialize():
    d = RuntimeServiceDescriptor(name="rs")
    m = RuntimeServiceMetadata(service_id="rs", name="RS")
    c = RuntimeServiceContract(service="rs")
    svc = RuntimeService(d, m, c)
    assert svc.status == "created"
    svc.initialize()
    assert svc.is_initialized is True
    assert svc.status == "ready"


def test_runtime_service_bad_contract():
    d = RuntimeServiceDescriptor(name="bad")
    m = RuntimeServiceMetadata(service_id="bad", name="Bad")
    c = RuntimeServiceContract(service="bad", network_allowed=False)
    # force invalid contract
    c = RuntimeServiceContract(service="bad")
    svc = RuntimeService(d, m, c)
    svc.initialize()  # contract valid -> ready
    assert svc.status == "ready"


def test_runtime_service_status_dict():
    d = RuntimeServiceDescriptor(name="rs2")
    m = RuntimeServiceMetadata(service_id="rs2", name="RS2")
    c = RuntimeServiceContract(service="rs2")
    svc = RuntimeService(d, m, c)
    sd = svc.status_dict()
    assert sd["name"] == "rs2"
    assert sd["status"] == "created"
    assert sd["initialized"] is False


def test_conversation_service():
    svc = ConversationRuntimeService(channels=("whatsapp",))
    assert svc.name == "conversation-runtime-service"
    assert svc.descriptor.description
    svc.initialize()
    assert svc.status == "ready"
    assert "conversation" in svc.metadata.capabilities


def test_conversation_descriptor_defaults():
    d = RuntimeServiceDescriptor(name="c", service_type="runtime")
    assert d.service_type == "runtime"


def test_dashboard_service():
    svc = DashboardRuntimeService(views=("mission", "execution"))
    assert svc.name == "dashboard-runtime-service"
    assert "dashboard" in svc.metadata.capabilities
    svc.initialize()
    assert svc.is_initialized


def test_runtime_state_frozen():
    s = RuntimeServiceState(name="x", status="ready")
    assert s.status == "ready"
    with pytest.raises(Exception):
        s.status = "running"
