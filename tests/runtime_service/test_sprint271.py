"""Sprint 271 - Integration.

Program D - Runtime Services & Deployment.
Pipeline akhir + RuntimeRegistry/Summary/Manifest/Report.
"""
from __future__ import annotations
import pytest

from sam.runtime_service.runtime_registry import RuntimeRegistry
from sam.runtime_service.runtime_summary import RuntimeSummary, build_runtime_summary
from sam.runtime_service.runtime_manifest import RuntimeManifest
from sam.runtime_service.runtime_report import RuntimeReport
from sam.runtime_service.runtime_pipeline import (
    RuntimePipeline, PipelineStageResult, PIPELINE_STAGES,
)
from sam.runtime_service.runtime_service import (
    RuntimeService, RuntimeServiceDescriptor,
    RuntimeServiceMetadata, RuntimeServiceContract,
)


def _make_service(name: str) -> RuntimeService:
    return RuntimeService(
        RuntimeServiceDescriptor(name=name),
        RuntimeServiceMetadata(service_id=name, name=name),
        RuntimeServiceContract(service=name),
    )


def test_pipeline_stages_full():
    assert "Mission" in PIPELINE_STAGES
    assert "Execution Runtime" in PIPELINE_STAGES
    assert "Runtime Service" in PIPELINE_STAGES
    assert "External Provider" in PIPELINE_STAGES


def test_pipeline_order():
    p = RuntimePipeline()
    st = p.stages
    assert st.index("Runtime Service") == st.index("Execution Runtime") + 1


def test_pipeline_validate():
    p = RuntimePipeline()
    assert p.validate() is True


def test_pipeline_count():
    p = RuntimePipeline()
    # Mission..External Provider = 14 tahap
    assert p.count() == len(PIPELINE_STAGES)


def test_pipeline_run_all_ok():
    p = RuntimePipeline()
    results = p.run()
    assert len(results) == p.count()
    assert p.all_ok() is True


def test_pipeline_result_freezing():
    r = PipelineStageResult(stage="Mission", ok=True)
    with pytest.raises(Exception):
        r.ok = False


def test_registry_register():
    reg = RuntimeRegistry()
    reg.register(_make_service("connector"))
    assert reg.count() == 1
    assert reg.has("connector")


def test_registry_duplicate():
    reg = RuntimeRegistry()
    reg.register(_make_service("a"))
    with pytest.raises(ValueError):
        reg.register(_make_service("a"))


def test_registry_names_sorted():
    reg = RuntimeRegistry()
    reg.register(_make_service("b"))
    reg.register(_make_service("a"))
    assert reg.names() == ["a", "b"]


def test_registry_all_ready():
    reg = RuntimeRegistry()
    svc = _make_service("s")
    svc.initialize()
    reg.register(svc)
    assert reg.all_ready() is True


def test_registry_empty_ready():
    reg = RuntimeRegistry()
    assert reg.all_ready() is True


def test_summary_build():
    reg = RuntimeRegistry()
    svc = _make_service("a")
    svc.initialize()
    reg.register(svc)
    s = build_runtime_summary(reg)
    assert s.count == 1
    assert s.services == ["a"]
    assert s.ready is True
    assert s.version == "27.0.0"


def test_summary_immutable():
    s = RuntimeSummary(services=["a"], count=1)
    with pytest.raises(Exception):
        s.count = 5


def test_manifest_immutable():
    m = RuntimeManifest(name="sam", layers=["runtime"])
    assert m.entry_point == "sam.runtime_service"
    with pytest.raises(Exception):
        m.name = "x"


def test_runtime_report_immutable():
    r = RuntimeReport(status="ready", services=["a"])
    with pytest.raises(Exception):
        r.status = "failed"


def test_report_as_dict():
    r = RuntimeReport(status="ready", metrics={"m": 1})
    ad = r.as_dict()
    assert ad["entry_point"] == "sam.runtime_service"
    assert ad["metrics"] == {"m": 1}


def test_integrated_flow():
    reg = RuntimeRegistry()
    pipeline = RuntimePipeline()
    svc = _make_service("runtime-service")
    svc.initialize()
    reg.register(svc)
    results = pipeline.run()
    assert pipeline.all_ok() is True
    summary = build_runtime_summary(reg)
    assert summary.ready is True
    manifest = RuntimeManifest(name="SAM", certifications=7)
    assert manifest.certifications == 7
    report = RuntimeReport(status="ready", services=reg.names(),
                           certified=True)
    assert report.status == "ready"
    assert report.certified is True
