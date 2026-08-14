"""M14-009 tests — Real OpenClaw Ward (observe+diagnose+recover).

Menguji logic ward OpenClaw dgn workspace temp + health.json nyata (file-based),
sedangkan recovery action di-stub (execute_fn/verify_fn diinjeksi) utk membuktikan
alur authority + loop. E2E real (OpenClaw runtime sungguhan) terpisah & jujur.
"""
import sys
import os
import json
import tempfile
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))


from sam.autonomy.models import AutonomyLevel
from sam.delegated_authority.authority import DelegationGrant
from sam.delegated_authority.real_openclaw_ward import OpenClawWard


def _grant_auto():
    return DelegationGrant(
        ward_id="openclaw", owner_id="owner", autonomy_level=AutonomyLevel.AUTONOMOUS,
        allowed_mutations=("protect",), requires_human_approval=False,
    )


def _make_ws(status="unhealthy", comp_status="unhealthy"):
    d = tempfile.mkdtemp(prefix="ocl_ward_")
    health_dir = os.path.join(d, ".openclaw")
    os.makedirs(health_dir, exist_ok=True)
    with open(os.path.join(health_dir, "health.json"), "w", encoding="utf-8") as f:
        json.dump({"components": [
            {"name": "Gateway", "status": comp_status, "message": "gateway down"},
        ]}, f)
    return d


class TestOpenClawWardDiagnose:
    async def test_diagnose_detects_unhealthy(self):
        ws = _make_ws("unhealthy", "unhealthy")
        ward = OpenClawWard(ws)
        diag = await ward.diagnose()
        assert diag.runtime_status == "unhealthy"
        assert diag.detections          # ada component_issue

    async def test_diagnose_healthy(self):
        # tanpa health.json -> fallback healthy simulation (Phase 1)
        d = tempfile.mkdtemp(prefix="ocl_healthy_")
        ward = OpenClawWard(d)
        diag = await ward.diagnose()
        assert diag.runtime_status == "healthy"


class TestOpenClawWardRecover:
    async def test_healthy_no_recovery(self):
        d = tempfile.mkdtemp(prefix="ocl_ok_")
        ward = OpenClawWard(d)
        res = await ward.recover(grant=_grant_auto())
        assert res.recovered is False
        assert "no recovery needed" in res.reason

    async def test_unhealthy_recover_when_authorized(self):
        ws = _make_ws("unhealthy", "unhealthy")
        ward = OpenClawWard(ws)
        res = await ward.recover(
            grant=_grant_auto(),
            execute_fn=lambda req: {"ok": True, "restarted": True},
            verify_fn=lambda req: {"ok": True, "verified": "openclaw recovered"},
        )
        assert res.recovered is True
        assert res.outcome.ok is True

    async def test_unhealthy_human_required_escalates(self):
        ws = _make_ws("unhealthy", "unhealthy")
        ward = OpenClawWard(ws)
        g = DelegationGrant(
            ward_id="openclaw", owner_id="owner",
            autonomy_level=AutonomyLevel.AUTONOMOUS,
            allowed_mutations=("protect",), requires_human_approval=True,
        )
        res = await ward.recover(
            grant=g,
            execute_fn=lambda req: {"ok": True},
            verify_fn=lambda req: {"ok": True},
        )
        assert res.recovered is False
        assert res.outcome.ok is False

    async def test_no_execute_fn_no_fake_success(self):
        ws = _make_ws("unhealthy", "unhealthy")
        ward = OpenClawWard(ws)
        res = await ward.recover(grant=_grant_auto(), execute_fn=None, verify_fn=None)
        assert res.recovered is False
        assert "no fake success" in res.reason
