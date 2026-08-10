"""T3 - Execution contract: MCR serah ke jalur resmi (ADR-008) (keputusan CA 2026-08-11).

Sebelum T3: MCR memanggil method khayalan `invoke(mission, conclusion=...)` /
`execute(mission, ...)` via getattr longgar. Jalur resmi (ExecutionEngine /
ExecutionRuntime) TIDAK punya method itu -> jika engine nyata di-inject, MCR
SILENT NO-OP (summary tanpa hasil eksekusi, tak ada penanda).

Setelah T3: MCR membangun `ExecutionRequest` (immutable, mode='preview', ADR-008
section 12: provider TIDAK dieksekusi, external_calls=0) dan menyerahkan ke jalur
resmi via execute(request) (ExecutionEngine) atau run(runtime_id, request)
(ExecutionRuntime). Jika engine ada tapi tak punya method resmi -> ditandai
eksplisit "no-execution-method" (bukan silent).

Guardrail:
- Jalur resmi ExecutionRuntime/ExecutionEngine/ExecutionRequest TIDAK diubah.
- MCR tetap orkestrator (tidak mengeksekusi sendiri / bukan God Object).
- Mode tetap preview (provider tidak dieksekusi) - ADR-008.
"""
import asyncio

from sam.execution_runtime.execution_engine import ExecutionEngine
from sam.execution_runtime.execution_runtime import ExecutionRuntime
from sam.execution_runtime.execution_request import ExecutionRequest
from sam.mission_cognition import MissionCognitiveRuntime, MissionCycleStatus


def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


class _ExecuteSpy:
    """Test double punya `execute(request)` (seperti ExecutionEngine) + catcher."""

    def __init__(self):
        self.requests = []
        self.outcome = type(
            "O", (), {"as_dict": lambda self: {"status": "preview", "executed": False, "external_calls": 0}}
        )()

    def execute(self, request):
        self.requests.append(request)
        return self.outcome


class _RunSpy:
    """Test double punya `run(runtime_id, request)` (seperti ExecutionRuntime)."""

    def __init__(self):
        self.calls = []

    def run(self, runtime_id, request):
        self.calls.append((runtime_id, request))
        return type("O", (), {"as_dict": lambda self: {"status": "preview"}})()


class _NoMethodEngine:
    """Engine TANPA method resmi execute/run - memicu "no-execution-method"."""


class TestT3ExecutionContract:
    """T3: MCR serah eksekusi ke jalur resmi dengan contract yang benar."""

    def test_mcr_membangun_execution_request_preview(self) -> None:
        """MCR membangun ExecutionRequest: mode=preview, payload berisi konteks."""
        spy = _ExecuteSpy()
        mcr = MissionCognitiveRuntime(
            governance_engine=None, governance_required=False, execution_runtime=spy
        )
        res = _run(mcr.run_cycle("mission A", evidences=()))
        assert spy.requests, "MCR harus memanggil execute(request)"
        req = spy.requests[0]
        assert isinstance(req, ExecutionRequest)
        assert req.mode == "preview"  # ADR-008: provider tidak dieksekusi
        assert req.operation == "mission_execute"
        assert req.payload["mission"] == "mission A"
        assert req.payload["conclusion"]
        # cycle_id ikut serta dalam request (audit trail)
        assert res.cycle_id
        assert res.status is MissionCycleStatus.COMPLETED

    def test_mcr_pakai_execute_dan_ringkas_hasil(self) -> None:
        """Hasil eksekusi nyata dirangkum ke execution_summary (bukan silent)."""
        spy = _ExecuteSpy()
        mcr = MissionCognitiveRuntime(
            governance_engine=None, governance_required=False, execution_runtime=spy
        )
        res = _run(mcr.run_cycle("mission", evidences=()))
        assert "result:" in res.execution_summary
        assert "executed" in res.execution_summary  # dari as_dict outcome

    def test_mcr_support_jalur_run(self) -> None:
        """MCR mendukung jalur `run(runtime_id, request)` (ExecutionRuntime)."""
        spy = _RunSpy()
        mcr = MissionCognitiveRuntime(
            governance_engine=None, governance_required=False, execution_runtime=spy
        )
        res = _run(mcr.run_cycle("mission", evidences=()))
        assert spy.calls, "MCR harus memanggil run(runtime_id, request)"
        runtime_id, req = spy.calls[0]
        assert isinstance(req, ExecutionRequest)
        assert str(runtime_id).startswith("mc-")
        assert res.status is MissionCycleStatus.COMPLETED

    def test_engine_tanpa_method_resmi_ditandai(self) -> None:
        """Engine tanpa execute/run -> "no-execution-method" (bukan silent no-op)."""
        mcr = MissionCognitiveRuntime(
            governance_engine=None,
            governance_required=False,
            execution_runtime=_NoMethodEngine(),
        )
        res = _run(mcr.run_cycle("mission", evidences=()))
        assert "no-execution-method" in res.execution_summary
        assert res.status is MissionCycleStatus.COMPLETED

    def test_integrasi_engine_nyata_preview(self) -> None:
        """MCR + ExecutionEngine nyata (filesystem) -> completed, preview, ec=0."""
        engine = ExecutionEngine(runtime=ExecutionRuntime())
        mcr = MissionCognitiveRuntime(
            governance_engine=None, governance_required=False, execution_runtime=engine
        )
        res = _run(mcr.run_cycle("mission", evidences=()))
        assert res.status is MissionCycleStatus.COMPLETED
        assert "result:" in res.execution_summary
        # preview -> provider tidak dieksekusi (ADR-008): external_calls=0
        assert "external_calls" in res.execution_summary

    def test_foundation_execution_runtime_tidak_diubah(self) -> None:
        """Jalur resmi (signature run/execute/ExecutionRequest) tidak berubah T3."""
        import inspect
        # ExecutionRuntime.run(runtime_id, request)
        sig_run = inspect.signature(ExecutionRuntime.run)
        assert "runtime_id" in sig_run.parameters and "request" in sig_run.parameters
        # ExecutionEngine.execute(request)
        sig_exec = inspect.signature(ExecutionEngine.execute)
        assert "request" in sig_exec.parameters
        # ExecutionRequest tetap mode preview valid
        r = ExecutionRequest(
            execution_id="x", provider_id="filesystem", operation="op", mode="preview"
        )
        assert r.mode == "preview"
