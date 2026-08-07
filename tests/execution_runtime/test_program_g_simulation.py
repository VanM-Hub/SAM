"""Program G - Execution Evolution: Simulation Capability (2026-08-07).

Exec: Zara, Lead Implementation Engineer. Arah: Architect (2026-08-07).

Menguji Simulation V1 = metadata-based simulation (deterministik, no mock
engine, no external call). Cakupan:
  - SimulationEvidence: field & determinisme (same input -> same output).
  - SimulationEngine: produce evidence dari metadata governance.
  - Mode simulation valid di ExecutionRequest.
  - Preview mode: external_calls = 0, tanpa approval.
  - Dry Run via SimulationIntegration: pipeline aktif, external_calls = 0.
  - Evidence opsional untuk Approval (kontrak ApprovalGate tidak berubah).
"""

from __future__ import annotations

import pytest

from sam.execution_runtime.execution_request import ExecutionRequest
from sam.execution_runtime.simulation_evidence import SimulationEvidence
from sam.execution_runtime.simulation_engine import (
    SimulationEngine, SimulationReport,
)
from sam.execution_runtime.simulation_integration import (
    SimulationIntegration, SimulatedExecutionReport,
)
from sam.execution_runtime.approval_gate import ApprovalGate
from sam.execution_runtime.provider_dispatcher import KNOWN_PROVIDERS


def _req(provider="openai", mode="execute", approved=True, operation="chat",
         execution_id="e1", payload=None):
    return ExecutionRequest(
        execution_id=execution_id,
        provider_id=provider,
        operation=operation,
        payload=payload or {"prompt": "hi"},
        mode=mode,
        approved=approved,
        approver="tester" if approved else "",
        timeout_seconds=60,
    )


# ---------------------------------------------------------------------------
# 1. SimulationEvidence
# ---------------------------------------------------------------------------

def test_evidence_frozen_and_dict():
    e = SimulationEvidence(
        simulation_id="sim-e1", execution_id="e1",
        provider_id="openai", operation="chat",
    )
    # immutable
    with pytest.raises(Exception):
        e.estimated_cost = 5.0  # type: ignore[misc]
    d = e.as_dict()
    assert d["simulation_id"] == "sim-e1"
    assert d["estimated_external_calls"] == 0
    assert isinstance(d["side_effects"], list)
    assert isinstance(d["expected_audit_chain"], list)


# ---------------------------------------------------------------------------
# 2. SimulationEngine - evidence deterministik dari metadata
# ---------------------------------------------------------------------------

def test_engine_produces_evidence():
    eng = SimulationEngine()
    ev = eng.simulate(_req())
    assert isinstance(ev, SimulationEvidence)
    assert ev.execution_id == "e1"
    assert ev.provider_id == "openai"
    assert ev.capability_resolved is True
    assert ev.provider_selected == "openai"
    assert ev.simulation_id == "sim-e1"


def test_engine_deterministic_same_input_same_output():
    eng = SimulationEngine()
    a = eng.simulate(_req(provider="openai", operation="chat"))
    b = eng.simulate(_req(provider="openai", operation="chat"))
    assert a.as_dict() == b.as_dict()


def test_engine_no_external_call_in_simulation():
    """Simulation V1 tidak memanggil provider: external_calls diturunkan
    dari metadata, bukan dari eksekusi. Untuk provider local = 0."""
    eng = SimulationEngine()
    ev = eng.simulate(_req(provider="filesystem", operation="read"))
    assert ev.estimated_external_calls == 0
    assert ev.estimated_cost == 0.0


def test_engine_external_provider_flagged():
    eng = SimulationEngine()
    ev = eng.simulate(_req(provider="openai", operation="chat"))
    assert ev.estimated_external_calls == 1
    # external provider -> ada estimated cost > 0
    assert ev.estimated_cost > 0.0
    assert "external_call" in ev.side_effects


def test_engine_rollback_and_audit_chain():
    eng = SimulationEngine()
    ev = eng.simulate(_req(provider="sqlite", operation="write"))
    assert ev.rollback_possible is True
    assert "simulation" in ev.expected_audit_chain
    assert ev.expected_audit_chain == (
        "mission", "workflow", "policy", "simulation",
        "approval", "execution", "verification",
    )


def test_engine_confidence_bounded():
    eng = SimulationEngine()
    for p in KNOWN_PROVIDERS:
        ev = eng.simulate(_req(provider=p, operation="op"))
        assert 0.0 <= ev.confidence <= 1.0
        assert 0.0 <= ev.estimated_risk <= 1.0


def test_engine_run_returns_report():
    eng = SimulationEngine()
    report = eng.run(_req())
    assert isinstance(report, SimulationReport)
    assert report.evidence.execution_id == "e1"
    assert "external_calls" in report.summary


# ---------------------------------------------------------------------------
# 3. Mode simulation valid di ExecutionRequest
# ---------------------------------------------------------------------------

def test_simulation_mode_valid():
    r = _req(mode="simulation", approved=False)
    assert r.mode == "simulation"


def test_invalid_mode_rejected():
    with pytest.raises(ValueError):
        _req(mode="bogus")


# ---------------------------------------------------------------------------
# 4. Preview mode: external_calls = 0, tanpa approval
# ---------------------------------------------------------------------------

def test_integration_preview_no_approval_no_network():
    """Mode preview: TIDAK benar-benar memanggil provider (report
    external_calls = 0), tanpa approval. Estimasi metadata (ke provider
    external) boleh menunjukkan akan ada 1 call JIKA dieksekusi - tapi
    preview tidak mengeksekusinya."""
    integration = SimulationIntegration()
    r = _req(mode="preview", approved=False)
    out = integration.preview(r)
    assert isinstance(out, SimulatedExecutionReport)
    # TIDAK ada panggilan nyata -> report external_calls = 0
    assert out.external_calls == 0
    assert out.approval_applied is False
    # preview tidak mengeksekusi provider, jadi estimasi yang naik ke
    # report dibatasi juga tidak boleh menjadi call nyata


# ---------------------------------------------------------------------------
# 5. Dry Run via SimulationIntegration: pipeline aktif, network = 0
# ---------------------------------------------------------------------------

def test_integration_dry_run_keeps_network_zero():
    integration = SimulationIntegration()
    r = _req(mode="execute", approved=True, provider="openai")
    out = integration.dry_run(r)
    assert out.external_calls == 0  # dry-run: TIDAK benar-benar memanggil provider
    assert out.approval_applied is True
    assert out.simulation.evidence.provider_id == "openai"


# ---------------------------------------------------------------------------
# 6. Evidence opsional untuk Approval - kontrak ApprovalGate TIDAK berubah
# ---------------------------------------------------------------------------

def test_simulation_evidence_optional_for_approval():
    """ADR-001: Approval menghasilkan keputusan. Evidence memperkaya tapi
    tidak menjadi keharusan. ApprovalGate tetap menerima ExecutionRequest."""
    gate = ApprovalGate()
    # approval tetap jalan tanpa evidence (kontrak tidak berubah)
    ok = gate.may_execute(_req(mode="execute", approved=True, provider="openai"))
    assert ok is True
    no = gate.may_execute(_req(mode="execute", approved=False, provider="openai"))
    assert no is False
    # preview tidak butuh approval (sejalan perilaku existing)
    prev = gate.may_execute(_req(mode="simulation", approved=False, provider="openai"))
    assert prev is True


def test_evidence_can_be_attached_as_optional_input():
    """Evidence dihasilkan & tersedia untuk approval sebagai input opsional,
    tanpa mengubah signature ApprovalGate.evaluate()."""
    integration = SimulationIntegration()
    ev = integration.evidence_for_approval(_req(provider="openai", operation="chat"))
    assert isinstance(ev, SimulationEvidence)
    # evidence punya estimasi yang berguna untuk keputusan
    assert ev.estimated_external_calls >= 0
    assert ev.estimated_cost >= 0.0
    assert ev.approval_required in (True, False)
