"""Test IP-4.6-002 - End-to-End Operations (MISSION-4.6).

Coverage: WP-11..WP-20 - Ask SAM, investigation/explanation/recommendation/
approval/execution/verification/learning experiences, flow compliance, e2e.

Menggunakan mock callbacks yang mensimulasikan kapabilitas MISSION-4.1..4.5.
"""
import os
import sys


sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "src")))

from sam.operational_workspace.end_to_end_flow import (
    EndToEndFlow,
    FlowStage,
)
from sam.operational_workspace.flow_compliance import OperationalFlowCompliance


def _flow():
    def investigate(q):
        return {"conclusion": "root cause identified", "evidence": ["e1"]}

    def explain(inv):
        return {"explanation": "service degraded", "chain": inv["evidence"]}

    def recommend(expl):
        return {"action": "restart service", "confidence": 0.9}

    def execute(rec):
        return {"status": "completed", "executed": rec["action"]}

    def verify(exec_result):
        return {"verified": True, "of": exec_result["executed"]}

    def learn(ver):
        return {"lesson": "restart helped", "stored": True}

    return EndToEndFlow(
        investigate=investigate, explain=explain, recommend=recommend,
        execute=execute, verify=verify, learn=learn,
    )


# ---------------------------------------------------------------------------
# WP-11 Ask SAM
# ---------------------------------------------------------------------------

class TestAskSAM:
    def test_ask_creates_flow(self):
        flow = _flow()
        flow_id = flow.ask("why is it slow?", intent="investigate")
        f = flow.get(flow_id)
        assert f.question == "why is it slow?"
        assert f.steps[0].stage == FlowStage.ASK


# ---------------------------------------------------------------------------
# WP-12..18 Experience stages (via run)
# ---------------------------------------------------------------------------

class TestEndToEndStages:
    def test_full_flow_with_approval(self):
        flow = _flow()
        flow_id = flow.ask("why is it slow?")
        f = flow.run(flow_id, require_approval=True, approved=True)
        stages = f.completed_stages
        assert stages == tuple(FlowStage.SEQUENCE)
        assert f.evidence_count == len(stages)

    def test_flow_blocks_without_approval(self):
        flow = _flow()
        flow_id = flow.ask("why?")
        f = flow.run(flow_id, require_approval=True, approved=False)
        stages = f.completed_stages
        # Berhenti setelah recommend, sebelum execute (menunggu approval)
        assert FlowStage.EXECUTE not in stages
        assert FlowStage.RECOMMEND in stages

    def test_flow_no_approval_required(self):
        flow = _flow()
        flow_id = flow.ask("why?")
        f = flow.run(flow_id, require_approval=False, approved=False)
        assert FlowStage.LEARN in f.completed_stages

    def test_every_stage_has_evidence(self):
        flow = _flow()
        flow_id = flow.ask("why?")
        f = flow.run(flow_id, require_approval=False)
        assert all(s.evidence for s in f.steps)
        assert f.evidence_count == len(f.completed_stages)


# ---------------------------------------------------------------------------
# WP-19 Operational Flow Compliance
# ---------------------------------------------------------------------------

class TestOperationalFlowCompliance:
    def test_certify_with_approval(self):
        flow_engine = _flow()
        compliance = OperationalFlowCompliance()
        flow_id = flow_engine.ask("why?")
        f = flow_engine.run(flow_id, require_approval=True, approved=True)
        cert = compliance.certify(f)
        assert cert["certified"] is True

    def test_execution_requires_approval(self):
        flow_engine = _flow()
        compliance = OperationalFlowCompliance()
        flow_id = flow_engine.ask("why?")
        # require_approval=False -> approve tidak direkam sebelum eksekusi
        f = flow_engine.run(flow_id, require_approval=False)
        cert = compliance.certify(f)
        # execute tercapai tanpa tahap approval -> pelanggaran Article V
        approval_check = next(
            c for c in cert["checks"] if c["code"] == "APPROVAL_BEFORE_EXECUTION"
        )
        assert approval_check["passed"] is False


# ---------------------------------------------------------------------------
# WP-20 Integration & Certification (end-to-end)
# ---------------------------------------------------------------------------

class TestEndToEndOperationsCert:
    def test_end_to_end_operations_full(self):
        flow = _flow()
        compliance = OperationalFlowCompliance()

        flow_id = flow.ask("operator: investigate high latency")
        result = flow.run(flow_id, require_approval=True, approved=True)
        assert result.evidence_count >= 7

        stages = result.completed_stages
        # Tidak ada tahapan terputus (urutan lengkap)
        assert stages == tuple(FlowStage.SEQUENCE)

        # Compliance
        cert = compliance.certify(result)
        assert cert["certified"] is True

    def test_investigation_halted_awaiting_approval(self):
        flow = _flow()
        compliance = OperationalFlowCompliance()
        flow_id = flow.ask("critical issue")
        result = flow.run(flow_id, require_approval=True, approved=False)
        # Alur tertunda approval; belum eksekusi
        assert FlowStage.EXECUTE not in result.completed_stages
        cert = compliance.certify(result)
        assert cert["passed"] is True  # alur tak lengkap tapi tanpa pelanggaran
