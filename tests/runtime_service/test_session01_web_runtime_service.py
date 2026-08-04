"""Session 01 - WebRuntimeService (consumer pertama RuntimeService).

Foundation Activation.
WebRuntimeService = gateway kontrak & lifecycle untuk Web Runtime/Lifecycle/Status
endpoint. BUKAN executor/coordinator. Tidak menyentuh provider/approval/execution.
"""
from __future__ import annotations
import inspect
import re

from sam.runtime_service import (
    WebRuntimeService,
    RuntimeServiceContract,
)


def test_web_runtime_service_exposed_public():
    """WebRuntimeService ekspor dari package root (API publik)."""
    from sam import runtime_service
    assert hasattr(runtime_service, "WebRuntimeService")
    assert hasattr(runtime_service, "WebRuntimeServiceDescriptor")


def test_web_runtime_service_initial_created():
    s = WebRuntimeService()
    assert s.name == "web-runtime-service"
    assert s.status == "created"
    assert s.is_initialized is False


def test_web_runtime_service_initialize_ready():
    s = WebRuntimeService()
    s.initialize()
    assert s.is_initialized is True
    assert s.status == "ready"


def test_web_runtime_service_contract_valid():
    s = WebRuntimeService()
    assert s.contract.validate() is True
    assert isinstance(s.contract, RuntimeServiceContract)
    assert s.contract.network_allowed is False
    assert s.contract.approval_required is True
    assert s.contract.preview_first is True
    assert s.contract.synchronous is True
    assert s.contract.deterministic is True


def test_web_runtime_service_capabilities():
    s = WebRuntimeService()
    assert "web" in s.metadata.capabilities
    assert "runtime" in s.metadata.capabilities
    assert "lifecycle" in s.metadata.capabilities
    assert "status" in s.metadata.capabilities


def test_web_runtime_service_status_dict():
    s = WebRuntimeService()
    s.initialize()
    d = s.status_dict()
    assert d["name"] == "web-runtime-service"
    assert d["status"] == "ready"
    assert d["initialized"] is True
    assert d["started"] is False


def test_web_runtime_service_descriptor():
    s = WebRuntimeService()
    # Descriptor dipakai pola RuntimeService base (konsisten Conversation/Dashboard).
    d = s.descriptor.as_dict()
    assert d["name"] == "web-runtime-service"
    assert "web" in d["tags"]
    assert "runtime-service" in s.contract.layers


def test_web_runtime_service_not_executor():
    """RuntimeService TIDAK boleh menjadi executor — tidak ada jalur eksekusi."""
    s = WebRuntimeService()
    assert not hasattr(s, "execute")
    assert not hasattr(s, "dispatch")
    assert not hasattr(s, "decide")
    assert not hasattr(s, "run_workflow")


def test_web_runtime_service_is_gateway():
    """Modul WebRuntimeService tidak mengimpor coordinator/execution/provider."""
    from sam.runtime_service import web_runtime_service as mod
    src = inspect.getsource(mod)
    # hanya periksa baris import / from — bukan docstring
    import_lines = [l for l in src.splitlines()
                    if l.strip().startswith(("import", "from"))]
    joined = " ".join(import_lines).lower()
    assert "coordinator" not in joined
    assert "execution" not in joined
    assert "provider" not in joined
    assert re.search(r"\bexecution_runtime\b", joined) is None
