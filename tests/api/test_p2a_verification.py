"""P2A Verification - Bukti aktual MissionBuilder CALLED dari jalur HTTP produksi.

Melengkapi test_p2a_rest_mission dengan TRACE AKTUAL: menempelkan detector pada
MissionBuilder.build_default untuk membuktikan ia BENAR-BENAR dipanggil saat HTTP
request masuk ke /mission/{id}, dan bahwa plan yang dibangun VALID + berisi 11
steps pipeline (MISSION-REACHABLE).

Catatan: AgentRunResult hanya mengekspos `steps` (count) + `detail`; objek plan
tidak terekspos pada respons HTTP. Karena itu bukti isi plan (11 steps) ditangkap
DI DALAM spy build_default, bukan dari respons HTTP.
"""
import re

import sam.agent.planner.mission_builder as mb
from fastapi.testclient import TestClient

from sam.api.server import app

PIPELINE_ROUTE_LEN = 11  # mission..provider (mission_route.py)


class _BuildSpy:
    """Mencatat pemanggilan build_default + isi plan yang dihasilkan (spy)."""

    def __init__(self):
        self.calls = 0
        self.captured_steps = []  # list[int]: step count per call

    def install(self):
        self._orig = mb.MissionBuilder.build_default

        def wrapper(self_builder, plan_id, mission_id):
            self.calls += 1
            result = self._orig(self_builder, plan_id, mission_id)
            plan = getattr(result, "plan", None)
            self.captured_steps.append(
                len(getattr(plan, "steps", []) or []) if plan is not None else 0
            )
            return result

        mb.MissionBuilder.build_default = wrapper

    def restore(self):
        mb.MissionBuilder.build_default = self._orig


class TestP2AVerificationTrace:
    """Trace aktual: MissionBuilder terpanggil dari jalur HTTP (CALLED + REACHABLE)."""

    def test_build_default_dipanggil_dari_http(self) -> None:
        """Bukti CALLED aktual: detector build_default terpicu oleh HTTP request."""
        spy = _BuildSpy()
        spy.install()
        try:
            client = TestClient(app)
            resp = client.post("/mission/mis-p2a-trace-1", json={"provider_id": "openai"})
            assert resp.status_code == 200, resp.text
            assert spy.calls >= 1, "MissionBuilder.build_default harus terpanggil dari HTTP"
        finally:
            spy.restore()

    def test_plan_valid_dan_11_steps_di_dalam_build(self) -> None:
        """Bukti MISSION-REACHABLE: saat dipanggil via HTTP, plan punya 11 steps."""
        spy = _BuildSpy()
        spy.install()
        try:
            client = TestClient(app)
            resp = client.post("/mission/mis-p2a-trace-2", json={"provider_id": "openai"})
            assert resp.status_code == 200, resp.text
            assert spy.captured_steps, "build_default harus terekam saat HTTP request"
            assert all(n == PIPELINE_ROUTE_LEN for n in spy.captured_steps), \
                f"plan harus punya {PIPELINE_ROUTE_LEN} steps, dapat {spy.captured_steps}"
        finally:
            spy.restore()

    def test_route_tidak_bypass_build_default(self) -> None:
        """Route adalah adapter: tidak memanggil build_default di kode aktif (di luar docstring)."""
        import sam.api.routes.mission as mission_route
        src = open(mission_route.__file__, encoding="utf-8").read()
        # Buang docstring (antara dua kumpulan triple-quote) agar hanya cek kode aktif.
        body = re.sub(r'""".*?"""', "", src, flags=re.DOTALL)
        calls = re.findall(r"\b(?:[A-Za-z_]\w*\.)+build_default\(", body)
        assert calls == [], f"route tidak boleh memanggil build_default: {calls}"
        # Route mengandalkan llm_agent_bridge (application use case) - P4A: MCR path.
        assert "llm_agent_bridge" in src
        # Route TIDAK memanggil use case legacy AgentRuntime orchestration di kode aktif
        # (jalur production kini memakai run_mission_cognitive -> MCR single owner).
        assert "run_mission_cognitive" in src
