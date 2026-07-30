import pytest, os, sys
from dataclasses import FrozenInstanceError
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from sam.approval.intake_record import ApprovalIntakeRecord, IntakeMetadata, IntakeSource
from sam.approval.intake_validator import IntakeValidator, ValidationResult
from sam.approval.intake_normalizer import IntakeNormalizer, NormalizedApprovalRecord
from sam.approval.intake_registry import IntakeRegistry
from sam.approval.intake_summary import IntakeSummaryBuilder, ApprovalIntakeSummary
from sam.approval.runtime_v1 import ApprovalRuntimeV1, ApprovalRuntimeResult

# --- DTO frozen ---
def test_record_frozen():
    r = ApprovalIntakeRecord(record_id="r1", timestamp=10.0)
    with pytest.raises(FrozenInstanceError):
        r.record_id = "x"

def test_metadata_frozen():
    m = IntakeMetadata()
    with pytest.raises(FrozenInstanceError):
        m.version = "x"

def test_result_frozen():
    rs = ApprovalRuntimeResult(success=True)
    with pytest.raises(FrozenInstanceError):
        rs.success = False

# --- Validator ---
def test_validator_init():
    assert IntakeValidator() is not None

def test_validator_valid():
    v = IntakeValidator()
    r = ApprovalIntakeRecord(record_id="r1", timestamp=100.0, decision_record_id="d1",
                              pipeline_version="5.20.0", readiness_score=0.9, certified=True)
    res = v.validate(r)
    assert res.valid is True

def test_validator_missing_fields():
    v = IntakeValidator()
    r = ApprovalIntakeRecord(record_id="", timestamp=0.0, decision_record_id="",
                              pipeline_version="", readiness_score=1.5)
    res = v.validate(r)
    assert res.valid is False
    assert len(res.errors) >= 3

# --- Normalizer ---
def test_normalizer_init():
    assert IntakeNormalizer() is not None

def test_normalizer_normalize():
    n = IntakeNormalizer()
    r = ApprovalIntakeRecord(record_id="r1", timestamp=100.0, decision_record_id="d1",
                              pipeline_version="5.20.0", readiness_score=0.9, certified=True)
    nr = n.normalize(r)
    assert nr.normalized_id == "norm_r1"
    assert nr.category == "manual"

def test_normalizer_decision_source():
    n = IntakeNormalizer()
    r = ApprovalIntakeRecord(record_id="r1", timestamp=100.0, decision_record_id="d1",
                              pipeline_version="5.20.0",
                              metadata=IntakeMetadata(source=IntakeSource.DECISION_RUNTIME))
    nr = n.normalize(r)
    assert nr.category == "decision"

# --- Registry ---
def test_registry_init():
    assert IntakeRegistry() is not None

def test_registry_register():
    reg = IntakeRegistry()
    r = ApprovalIntakeRecord(record_id="r1", timestamp=100.0)
    nr = NormalizedApprovalRecord(normalized_id="norm_r1")
    reg.register(r, nr)
    assert reg.count == 1
    assert reg.exists("r1") is True

def test_registry_get():
    reg = IntakeRegistry()
    r = ApprovalIntakeRecord(record_id="r1", timestamp=100.0)
    nr = NormalizedApprovalRecord(normalized_id="norm_r1")
    reg.register(r, nr)
    assert reg.get("r1") is not None
    assert reg.get("nonexistent") is None

# --- Summary ---
def test_summary_init():
    assert IntakeSummaryBuilder() is not None

def test_summary_build():
    r = ApprovalIntakeRecord(record_id="r1", timestamp=100.0, decision_record_id="d1",
                              pipeline_version="5.20.0", readiness_score=0.9, certified=True)
    v = ValidationResult(valid=True)
    s = IntakeSummaryBuilder.build(r, v)
    assert s.readiness == "READY"
    assert s.certified is True

# --- Runtime ---
def test_runtime_init():
    assert ApprovalRuntimeV1() is not None

def test_runtime_process():
    rt = ApprovalRuntimeV1()
    r = ApprovalIntakeRecord(record_id="r1", timestamp=100.0, decision_record_id="d1",
                              pipeline_version="5.20.0", readiness_score=0.9, certified=True)
    result = rt.process(r)
    assert result.success is True

def test_runtime_process_invalid():
    rt = ApprovalRuntimeV1()
    r = ApprovalIntakeRecord(record_id="", timestamp=0.0, decision_record_id="",
                              pipeline_version="", readiness_score=-1.0)
    result = rt.process(r)
    assert result.success is False

def test_runtime_status():
    rt = ApprovalRuntimeV1()
    r = ApprovalIntakeRecord(record_id="r1", timestamp=100.0, decision_record_id="d1",
                              pipeline_version="5.20.0", readiness_score=0.9)
    rt.process(r)
    s = rt.get_status()
    assert s["intake_count"] == 1

# --- Conversation / Dashboard ---
def test_conversation():
    rt = ApprovalRuntimeV1()
    assert rt.conversation_intake.query_count == 10

def test_dashboard():
    rt = ApprovalRuntimeV1()
    assert rt.dashboard_intake.card_count == 6

# --- Forbidden imports ---
def test_forbidden():
    dp = os.path.join("src", "sam", "approval")
    for pat in ["import threading", "import asyncio", "async def", "await ", "import socket"]:
        for fn in ["intake_record.py","intake_validator.py","intake_normalizer.py",
                    "intake_registry.py","intake_summary.py","conversation_intake.py",
                    "dashboard_intake.py","runtime_v1.py","__init__.py"]:
            p = os.path.join(dp, fn)
            if os.path.exists(p):
                with open(p, "r", encoding="utf-8") as f:
                    assert pat not in f.read(), f"{pat} in {fn}"

def test_no_async():
    dp = os.path.join("src", "sam", "approval")
    for fn in ["intake_record.py","intake_validator.py","intake_normalizer.py",
                "intake_registry.py","intake_summary.py","conversation_intake.py",
                "dashboard_intake.py","runtime_v1.py","__init__.py"]:
        p = os.path.join(dp, fn)
        if os.path.exists(p):
            with open(p, "r", encoding="utf-8") as f:
                t = f.read()
                assert "async def" not in t
                assert "await " not in t

# --- Deterministic ---
@pytest.mark.parametrize("i", range(100))
def test_deterministic_intake(i):
    rt = ApprovalRuntimeV1()
    r = ApprovalIntakeRecord(record_id=f"r{i}", timestamp=float(i+1),
                              decision_record_id=f"d{i}", pipeline_version="5.20.0",
                              readiness_score=0.5 + (i%5)*0.1, certified=(i%2==0))
    result = rt.process(r)
    assert result.success is True
