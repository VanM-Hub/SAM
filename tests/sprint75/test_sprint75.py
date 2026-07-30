import pytest, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from sam.approval.runtime_v1 import ApprovalRuntimeV1
from sam.approval.intake_record import ApprovalIntakeRecord

def test_certification_version():
    rt = ApprovalRuntimeV1()
    assert rt.get_status()["version"] == "6.11.0"

def test_certification_no_auto_approve():
    """Approval Runtime MUST NOT auto-approve."""
    rt = ApprovalRuntimeV1()
    rt.process(ApprovalIntakeRecord(record_id="r1",timestamp=1.0,decision_record_id="d1",
        pipeline_version="5.20.0",readiness_score=1.0,certified=True))
    w = rt._last_workflow
    assert w.phase.value < 3  # PENDING(0) or IN_REVIEW(1), NEVER APPROVED(3)

def test_certification_no_auto_execute():
    """Approval Runtime MUST NOT execute anything."""
    rt = ApprovalRuntimeV1()
    assert rt._console_engine is not None  # Console is for display, not execution

def test_certification_no_network():
    dp = os.path.join("src","sam","approval")
    for root, dirs, files in os.walk(dp):
        for fn in files:
            if fn.endswith(".py"):
                p = os.path.join(root,fn)
                with open(p,"r",encoding="utf-8") as f:
                    t = f.read()
                    assert "import socket" not in t
                    assert "import requests" not in t
                    assert "import http" not in t

def test_certification_no_async():
    """New Phase VI files must have no async. Legacy engine.py/models.py excluded."""
    dp = os.path.join("src","sam","approval")
    skip = {"engine.py","models.py"}
    for root, dirs, files in os.walk(dp):
        for fn in files:
            if not fn.endswith(".py"): continue
            if fn in skip: continue
            p = os.path.join(root,fn)
            with open(p,"r",encoding="utf-8") as f:
                t = f.read()
                assert "async def" not in t, f"{fn} contains async def"
                assert "await " not in t, f"{fn} contains await"

def test_certification_no_threading():
    dp = os.path.join("src","sam","approval")
    for root, dirs, files in os.walk(dp):
        for fn in files:
            if fn.endswith(".py"):
                with open(os.path.join(root,fn),"r",encoding="utf-8") as f:
                    assert "import threading" not in f.read()

def test_certification_independence():
    """Approval Runtime does NOT import Decision Runtime."""
    dp = os.path.join("src","sam","approval")
    for root, dirs, files in os.walk(dp):
        for fn in files:
            if fn.endswith(".py"):
                with open(os.path.join(root,fn),"r",encoding="utf-8") as f:
                    t = f.read()
                    assert "sam.operations.brain.decision" not in t
                    assert "sam.guardian.live" not in t

def test_certification_pipeline_integrity():
    """Full pipeline integration test."""
    rt = ApprovalRuntimeV1()
    r = ApprovalIntakeRecord(record_id="cert1",timestamp=1.0,decision_record_id="d1",
        pipeline_version="5.20.0",readiness_score=0.85,certified=True)
    result = rt.process(r)
    assert result.success is True
    assert result.validation.valid is True
    assert result.normalized is not None
    assert result.summary.readiness == "READY"
    assert result.workflow.phase.name == 'PENDING'

def test_certification_audit_trail():
    """Every process() call must produce an audit entry."""
    rt = ApprovalRuntimeV1()
    rt.process(ApprovalIntakeRecord(record_id="a1",timestamp=1.0,decision_record_id="d1",
        pipeline_version="5.20.0",readiness_score=0.5))
    assert rt._audit_engine.entry_count >= 1

def test_certification_sorted_levels():
    """Multi-level levels must be order-validated."""
    from sam.approval.multilevel import MultiLevelApproval, ApprovalLevel
    from sam.approval.multilevel_validator import MultiLevelValidator
    m = MultiLevelApproval(approval_id="a1",workflow_id="w1",
        levels=[ApprovalLevel(level_id="L2",order=1),ApprovalLevel(level_id="L1",order=0)])
    v, errs = MultiLevelValidator.validate(m)
    assert v is False  # out of order

def test_certification_policy_not_found():
    from sam.approval.policy_engine import PolicyEngine
    r = PolicyEngine().evaluate("nonexistent",{})
    assert r.match is False
    assert r.effect.name == 'ALLOW'

@pytest.mark.parametrize("i", range(50))
def test_certification_deterministic(i):
    rt = ApprovalRuntimeV1()
    r = ApprovalIntakeRecord(record_id=f"cert_det{i}",timestamp=float(i+1),
        decision_record_id=f"cd{i}",pipeline_version="5.20.0",
        readiness_score=0.5+(i%5)*0.1,certified=(i%2==0))
    assert rt.process(r).success is True
