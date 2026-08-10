"""P3 - Wire MCR -> MissionBuilder (keputusan Chief Architect 2026-08-11).

Bukti runtime bahwa Mission Cognitive Runtime (MCR) TIDAK membangun plan sendiri,
melainkan hanya INVOKE MissionBuilder, CONSUME structured plan, dan HANDOFF plan
ke Governance Kernel.

Target flow (bukan manual plan construction):
    MCR.run_cycle()
        -> Reason
        -> MissionBuilder  (invoke, bukan manual)
        -> Structured Mission Plan  (consume)
        -> Governance  (handoff plan)
        -> Execution

Guardrail yang diuji:
- MCR invoke MissionBuilder.build_default (spy), bukan membuat MissionPlan sendiri.
- Plan di-result terisi (consume): plan_id + step_count + runtimes.
- Plan di-handoff ke governance via decision graph.
- Plan invalid -> siklus BLOCKED (tidak mengeksekusi dengan plan cacat).
- reasoning/engine.py tetap tidak diaktifkan oleh MCR (guardrail).
"""
import asyncio

import sam.agent.planner.mission_builder as mb
from sam.agent.planner.mission_builder import MissionBuilder
from sam.mission_cognition import MissionCognitiveRuntime, MissionCycleStatus

PIPELINE_ROUTE_LEN = 11


def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


class _PlanSpy:
    """Spy: mencatat apakah build_default di-invoke (bukti MCR invoke, bukan manual)."""

    def __init__(self):
        self.calls = 0
        self._orig = None

    def install(self):
        self._orig = mb.MissionBuilder.build_default

        def wrapper(self_builder, plan_id, mission_id):
            self.calls += 1
            return self._orig(self_builder, plan_id, mission_id)

        mb.MissionBuilder.build_default = wrapper

    def restore(self):
        mb.MissionBuilder.build_default = self._orig


class _GovRecorder:
    """Governance engine fiktif: mencatat graph yang di-handoff (bukti handoff plan)."""

    def __init__(self):
        self.received_graphs = []

    async def evaluate(self, graph, _ctx):
        self.received_graphs.append(graph)
        return type("V", (), {"decision": "allow", "reason": "ok"})

    def __call__(self, *a, **k):
        return self.evaluate(*a, **k)


class TestP3MCRInvokesMissionBuilder:
    """MCR invoke MissionBuilder, bukan manual plan construction."""

    def test_mcr_invoke_mission_builder_build_default(self) -> None:
        spy = _PlanSpy()
        spy.install()
        try:
            mcr = MissionCognitiveRuntime(
                governance_engine=None, governance_required=False
            )
            res = _run(mcr.run_cycle("mission x", evidences=()))
            assert res.status is MissionCycleStatus.COMPLETED
            assert spy.calls >= 1, "MCR harus invoke MissionBuilder.build_default"
        finally:
            spy.restore()

    def test_mcr_tidak_membangun_plan_manual(self) -> None:
        """MCR tidak import/membuat MissionPlan atau MissionStep sendiri."""
        import sam.mission_cognition.runtime as mcr_mod
        src = open(mcr_mod.__file__, encoding="utf-8").read()
        # MCR hanya memakai MissionBuilder (invoke); tidak instanisasi plan manual.
        assert "MissionBuilder" in src
        assert "build_default" in src
        # Plan object TIDAK diinstansiasi manual di MCR (harus lewat builder).
        # MissionPlan/MissionStep hanya muncul di sini sebagai import builder.
        assert "MissionPlan(" not in src
        assert "MissionStep(" not in src


class TestP3MCRConsumesPlan:
    """MCR consume structured plan (plan_id, step_count, runtimes)."""

    def test_plan_di_result_terisi_setelah_cycle(self) -> None:
        mcr = MissionCognitiveRuntime(
            governance_engine=None, governance_required=False
        )
        res = _run(mcr.run_cycle("mission consume", evidences=()))
        assert res.plan_id.startswith("plan-")
        assert res.plan_step_count == PIPELINE_ROUTE_LEN
        assert len(res.plan_runtimes) == PIPELINE_ROUTE_LEN
        # urutan pipeline lengkap, bukan rencana manual/acak
        assert res.plan_runtimes[0] == "mission"
        assert res.plan_runtimes[-1] == "provider"


class TestP3MCRHandoffPlanToGovernance:
    """MCR handoff plan ke Governance (decision graph memuat plan)."""

    def test_governance_menerima_plan(self) -> None:
        gov = _GovRecorder()
        mcr = MissionCognitiveRuntime(
            governance_engine=gov, governance_required=True
        )
        res = _run(mcr.run_cycle("mission handoff", evidences=()))
        assert res.status is MissionCycleStatus.COMPLETED
        assert gov.received_graphs, "governance harus dipanggil"
        graph = gov.received_graphs[0]
        assert "plan" in graph, "decision graph harus memuat plan (handoff)"
        assert graph["plan"]["step_count"] == PIPELINE_ROUTE_LEN
        assert graph["plan"]["plan_id"] == res.plan_id


class TestP3Guardrail:
    """Guardrail P3: plan invalid -> blocked; reasoning/engine.py tidak diaktifkan."""

    def test_plan_invalid_blokir_siklus(self) -> None:
        class _BadBuilder:
            def build_default(self, plan_id, mission_id):
                return type("R", (), {"valid": False, "plan": None, "reason": "nope"})()

        mcr = MissionCognitiveRuntime(
            mission_builder=_BadBuilder(),
            governance_engine=None,
            governance_required=False,
        )
        res = _run(mcr.run_cycle("mission bad", evidences=()))
        assert res.status is MissionCycleStatus.BLOCKED
        assert "plan invalid" in res.error

    def test_mcr_tidak_mengaktifkan_reasoning_engine_lama(self) -> None:
        """MCR memakai StructuredReasoningEngine (panci B), bukan reasoning/engine.py lama."""
        import sam.mission_cognition.runtime as mcr_mod
        src = open(mcr_mod.__file__, encoding="utf-8").read()
        assert "governed_reasoning.structured_reasoning" in src
        # Bukan dari reasoning/engine.py lama (world lama / dead according AD-ENG-002).
        assert "sam.reasoning.engine" not in src
