"""Sprint 248 — Certification.

Program B — Model Runtime Integration.
7 dimensi: Structure, Integrity, Consistency, Completeness, Determinism,
Immutability, PreviewOnly.
"""
from __future__ import annotations
import pytest

from sam.model_runtime.model_score import ModelScore, ModelScoreSet
from sam.model_runtime.model_manifest import ModelManifest
from sam.model_runtime.model_cert_report import ModelCertificationReport
from sam.model_runtime.model_health import ModelCertHealth
from sam.model_runtime.model_quality import ModelQuality
from sam.model_runtime.model_certifier import ModelCertifier, DIMENSIONS
from sam.model_runtime.model_descriptor import ModelDescriptor
from sam.model_runtime.model_contract import ModelContract
from sam.model_runtime.model_metadata import ModelMetadata
from sam.model_runtime.conversation_certification import ConversationCertification
from sam.model_runtime.dashboard_certification import DashboardCertification


def make_manifest(descriptor_id="m1", operations=("preview", "chat")):
    desc = ModelDescriptor(id=descriptor_id, name="M", model_type="chat")
    contract = ModelContract(contract_id=f"c-{descriptor_id}", owner_id=descriptor_id,
                             operations=list(operations), external_calls=0)
    meta = ModelMetadata(owner_id=descriptor_id, source_runtime="model",
                         preview_only=True, no_inference=True, external_calls=0)
    return ModelManifest(manifest_id=f"man-{descriptor_id}", descriptor=desc,
                         contract=contract, metadata=meta)


def test_dimensions_seven():
    assert len(DIMENSIONS) == 7
    expected = {"structure", "integrity", "consistency", "completeness",
                "determinism", "immutability", "preview_only"}
    assert set(DIMENSIONS) == expected


def test_certifier_passes_all_dimensions():
    cert = ModelCertifier()
    report = cert.certify(make_manifest())
    assert isinstance(report, ModelCertificationReport)
    assert report.passed is True
    assert report.dimensions_total == 7
    assert report.dimensions_passed == 7
    assert report.dimensions_passed == report.dimensions_total


def test_certifier_fails_on_empty_operations():
    cert = ModelCertifier()
    report = cert.certify(make_manifest(operations=()))
    assert report.passed is False
    assert report.dimensions_passed < 7


def test_certifier_fails_on_external_calls():
    desc = ModelDescriptor(id="m1", name="M", model_type="chat")
    contract = ModelContract(contract_id="c-m1", owner_id="m1",
                             operations=["chat"], external_calls=1)
    meta = ModelMetadata(owner_id="m1", source_runtime="model", external_calls=1)
    manifest = ModelManifest(manifest_id="man-m1", descriptor=desc,
                             contract=contract, metadata=meta)
    report = ModelCertifier().certify(manifest)
    assert report.passed is False
    score = report.score_set.as_dict()["preview_only"]
    assert score["passed"] is False


def test_score_immutable():
    s = ModelScore("structure", score=1.0, passed=True)
    with pytest.raises(Exception):
        s.score = 0.5
    ss = ModelScoreSet(scores={"structure": s})
    assert ss.as_dict()["structure"]["passed"] is True


def test_health_and_quality():
    h = ModelCertHealth()
    assert h.healthy is True
    assert h.external_calls == 0
    q = ModelQuality(quality_id="q1", indicators={"reliability": 0.9}, overall=0.9)
    assert q.preview_only is True


def test_conversation_certification_bridge():
    conv = ConversationCertification()
    out = conv.certify("conv-1", make_manifest())
    assert out.external_calls == 0
    assert out.report.passed is True


def test_dashboard_certification_rows():
    dash = DashboardCertification()
    dash.add(ModelCertifier().certify(make_manifest("m1")))
    dash.add(ModelCertifier().certify(make_manifest("m2", operations=())))
    assert len(dash.rows()) == 2
    s = dash.summary()
    assert s["passed"] == 1
    assert s["failed"] == 1
    assert s["external_calls"] == 0


def test_no_forbidden_imports():
    import inspect
    import sam.model_runtime.model_certifier as mc
    src = inspect.getsource(mc)
    for banned in ("import socket", "requests", "httpx", "asyncio",
                   "threading", "subprocess"):
        assert banned not in src
