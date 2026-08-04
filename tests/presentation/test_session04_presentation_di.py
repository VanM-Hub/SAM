"""Session 04 - Presentation Layer menerima RuntimeService via DI (AD-S04).

Desktop = Presentation pertama yang memakai activation path resmi.
Presentation menerima RuntimeService via dependency injection; HANYA membaca
kontrak (lifecycle/status/descriptor/metadata/contract). BUKAN RuntimeCoordinator,
BUKAN ExecutionRuntime, BUKAN business logic di Presentation.
"""
from __future__ import annotations
import inspect


from sam.presentation import PresentationLayer
from sam.runtime_service import WebRuntimeService, RuntimeService


def _ready_service() -> WebRuntimeService:
    svc = WebRuntimeService()
    svc.initialize()
    return svc


def test_presentation_accepts_runtime_service_via_di():
    svc = _ready_service()
    layer = PresentationLayer(runtime_service=svc)
    assert layer.has_runtime_service is True
    assert isinstance(layer.runtime_service, RuntimeService)


def test_presentation_default_no_di_backward_compatible():
    # tanpa DI harus tetap bekerja (backward compatible)
    layer = PresentationLayer()
    assert layer.has_runtime_service is False
    assert layer.run() is not None  # komposisi berjalan normal
    assert layer.runtime_status()["available"] is False


def test_presentation_reads_runtime_status_from_contract():
    svc = _ready_service()
    layer = PresentationLayer(runtime_service=svc)
    rs = layer.runtime_status()
    assert rs["available"] is True
    assert rs["status"] == "ready"
    assert rs["initialized"] is True
    assert rs["contract"]["service"] == "web-runtime-service"
    assert rs["contract"]["network_allowed"] is False


def test_presentation_does_not_read_coordinator_internal():
    """runtime_status hanya kontrak service; tidak ada field internal coordinator."""
    svc = _ready_service()
    layer = PresentationLayer(runtime_service=svc)
    rs = layer.runtime_status()
    for banned in ("workspace_path", "adapter_name", "autonomous_enabled",
                   "session_manager", "manifest", "state_machine"):
        assert banned not in rs, f"Presentation baca internal coordinator: {banned}"


def test_presentation_does_not_know_execution():
    """PresentationLayer tidak mengimpor/mengetahui ExecutionRuntime."""
    import sam.presentation.presentation_layer as pl
    src = inspect.getsource(pl)
    import_lines = [l for l in src.splitlines()
                    if l.strip().startswith(("import", "from"))]
    joined = " ".join(import_lines).lower()
    assert "execution_runtime" not in joined
    assert "execution_engine" not in joined
    assert "runtime.coordinator" not in joined


def test_presentation_does_not_create_runtime_service():
    """Presentation TIDAK membuat RuntimeService sendiri; menerima via DI."""
    import sam.presentation.presentation_layer as pl
    src = inspect.getsource(pl)
    # PresentationLayer.__init__ tidak pernah instantiate WebRuntimeService
    assert "WebRuntimeService()" not in src
    assert "RuntimeCoordinator()" not in src


def test_presentation_runtime_status_immutable_dict():
    rs = _ready_service()
    layer = PresentationLayer(runtime_service=rs)
    d = layer.runtime_status()
    # kontrak immutable & deterministic (bisa diserialisasi)
    import json
    json.dumps(d)  # tidak error = serializable
    assert d["lifecycle"]["status"] == "ready"


def test_no_business_logic_in_presentation():
    """Presentation tidak menambah business logic (hanya baca kontrak)."""
    svc = _ready_service()
    layer = PresentationLayer(runtime_service=svc)
    # runtime_status hanya MIRROR kontrak service; tidak ada decision/calculate
    rs = layer.runtime_status()
    assert "decision" not in rs
    assert "orchestrate" not in rs
