"""Sprint 258 - Certification.

Program C - Real Execution Runtime.
7 dimensi: Structure, Integrity, Consistency, Determinism, Approval,
Rollback, Safety.
"""
from __future__ import annotations
import pytest

from sam.execution_runtime.execution_descriptor import ExecutionDescriptor
from sam.execution_runtime.execution_contract import ExecutionContract
from sam.execution_runtime.execution_metadata import ExecutionMetadata
from sam.execution_runtime.execution_manifest import ExecutionManifest
from sam.execution_runtime.execution_score import ExecutionScore, ExecutionScoreSet
from sam.execution_runtime.execution_validator import ExecutionValidator, ExecutionValidatorResult
from sam.execution_runtime.execution_cert_report import ExecutionCertReport
from sam.execution_runtime.execution_certifier import ExecutionCertifier, DIMENSIONS
from sam.execution_runtime.execution_request import ExecutionRequest


def make_manifest(mode="preview", approved=False, external_calls=0):
    desc = ExecutionDescriptor(id="e1", name="Exec", operation="chat", mode=mode)
    contract = ExecutionContract(contract_id="c-e1", owner_id="e1", external_calls=external_calls)
    meta = ExecutionMetadata(owner_id="e1", mode=mode,
                             approved=approved,
                             preview_only=(mode != "execute"),
                             external_calls=external_calls)
    return ExecutionManifest(manifest_id="man-e1", descriptor=desc,
                             contract=contract, metadata=meta)


def test_dimensions_seven():
    assert len(DIMENSIONS) == 7
    expected = {"structure", "integrity", "consistency", "determinism",
                "approval", "rollback", "safety"}
    assert set(DIMENSIONS) == expected


def test_certifier_passes_valid_preview():
    report = ExecutionCertifier().certify(make_manifest(mode="preview"))
    assert isinstance(report, ExecutionCertReport)
    assert report.passed is True
    assert report.dimensions_total == 7
    assert report.dimensions_passed == 7


def test_certifier_approval_dimension():
    # execute tanpa approval => approval dimension gagal
    report = ExecutionCertifier().certify(make_manifest(mode="execute", approved=False))
    score = report.score_set.as_dict()["approval"]
    assert score["passed"] is False
    assert report.passed is False
    assert report.dimensions_passed == 6


def test_certifier_structure_fails_empty_id():
    # descriptor menolak id kosong di level konstruksi => tidak pernah ada manifest tak-beridentitas
    with pytest.raises(ValueError):
        ExecutionDescriptor(id="", name="X", operation="chat", mode="preview")
    # untuk descriptor valid selalu struktur-pass
    report = ExecutionCertifier().certify(make_manifest())
    assert report.as_dict()["score_set"]["structure"]["passed"] is True


def test_certifier_consistency_bad_mode():
    report = ExecutionCertifier().certify(make_manifest(mode="execute", approved=True))
    # mode execute valid, semua harus pass
    assert report.passed is True


def test_score_immutable():
    s = ExecutionScore("structure", 1.0, True)
    with pytest.raises(Exception):
        s.score = 0.0
    ss = ExecutionScoreSet(scores={"structure": s})
    assert ss.all_passed() is True
    assert ss.as_dict()["structure"]["passed"] is True


def test_score_set_not_all_passed():
    ss = ExecutionScoreSet(scores={
        "a": ExecutionScore("a", 1.0, True),
        "b": ExecutionScore("b", 0.0, False),
    })
    assert ss.all_passed() is False


def test_validator_ok():
    v = ExecutionValidator().validate(ExecutionRequest("e1", "openai", "chat"))
    assert isinstance(v, ExecutionValidatorResult)
    assert v.valid is True
    assert v.errors == ()


def test_validator_empty_operation():
    v = ExecutionValidator().validate(ExecutionRequest("e1", "openai", ""))
    assert v.valid is False
    assert "operation required" in v.errors


def test_validator_bad_timeout():
    # request menolak timeout < 1 di level konstruksi (ditegakkan di __post_init__)
    with pytest.raises(ValueError):
        ExecutionRequest("e1", "openai", "x", timeout_seconds=0)
    # validator tetap memperbaiki request valid
    assert ExecutionValidator().validate(ExecutionRequest("e1", "openai", "x")).valid is True


def test_cert_report_as_dict():
    report = ExecutionCertifier().certify(make_manifest(mode="preview"))
    d = report.as_dict()
    assert d["passed"] is True
    assert d["dimensions_total"] == 7
    assert "score_set" in d


def test_manifest_as_dict():
    m = make_manifest()
    d = m.as_dict()
    assert d["manifest_id"] == "man-e1"
    assert d["descriptor"]["mode"] == "preview"


def test_manifest_immutable():
    m = make_manifest()
    with pytest.raises(Exception):
        m.metadata = ExecutionMetadata(owner_id="x")


def test_determinism_dimension():
    # determinism_check=True => pass
    report = ExecutionCertifier().certify(make_manifest())
    assert report.as_dict()["score_set"]["determinism"]["passed"] is True


def test_safety_dimension():
    report = ExecutionCertifier().certify(make_manifest())
    assert report.as_dict()["score_set"]["safety"]["passed"] is True


def test_rollback_dimension():
    report = ExecutionCertifier().certify(make_manifest())
    assert report.as_dict()["score_set"]["rollback"]["passed"] is True


def test_dimensions_score_keys_match():
    report = ExecutionCertifier().certify(make_manifest())
    keys = set(report.as_dict()["score_set"].keys())
    assert keys == set(DIMENSIONS)


def test_no_forbidden_imports_certifier():
    import inspect
    import sam.execution_runtime.execution_certifier as ec
    src = inspect.getsource(ec)
    for banned in ("import socket", "requests", "httpx", "asyncio",
                   "threading", "subprocess"):
        assert banned not in src
