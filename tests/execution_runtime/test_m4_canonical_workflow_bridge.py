# -*- coding: utf-8 -*-
"""Test M4 - Canonical Workflow Bridge (universal_workflow -> RealExecutionHarness).

Membuktikan orchestrator `universal_workflow` diarahkan ke jalur canonical
(RealExecutionHarness) sehingga setiap STEP dieksekusi NYATA (gated), bukan
`success=True` kosong; dan gagal-fast (no partial commit) bila satu step gagal.

Cara jalan:
    python -m pytest tests/execution_runtime/test_m4_canonical_workflow_bridge.py -v
"""
from __future__ import annotations

import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "src")))

from sam.execution_runtime.canonical_workflow_bridge import (
    CanonicalStepExecutor,
    build_universal_engine_executor,
    run_gated_workflow,
)
from sam.execution_runtime.real_harness import (
    AuditTrail,
    ExecutionMode,
    ExecutionRequest,
    RealExecutionHarness,
)


@pytest.fixture()
def target_file(tmp_path) -> str:
    p = tmp_path / "m4_source.txt"
    p.write_text("M4 workflow content", encoding="utf-8")
    return str(p)


@pytest.fixture()
def harness_with_tool():
    h = RealExecutionHarness(audit=AuditTrail())
    from sam.execution_runtime.canonical_tool_contract import (
        TOOL_KIND_READ,
        TOOL_KIND_EXECUTE,
        build_tool_contract,
        contract_to_registry_dict,
    )

    c = build_tool_contract(
        tool_id="wf_tool", contract_id="ct-wf",
        supported_kinds=(TOOL_KIND_READ, TOOL_KIND_EXECUTE),
        entry_points=("read", "meta"),
        requires_approval=True, requires_governance=True,
    )
    h.register_capability("tool", contract_to_registry_dict(c), c.to_contract_dict(), "ALLOW")
    return h


def test_m4_run_gated_workflow_read_chain(target_file, harness_with_tool):
    """Rantai meta -> read dieksekusi NYATA lewat canonical, semua verified."""
    audit = harness_with_tool._audit  # noqa: SLF001
    ok, outcomes = run_gated_workflow(
        [
            {"step_id": "s1", "operation": "tool/meta", "target": target_file,
             "approval_reason": "M4 meta", "correlation_id": "m4-meta"},
            {"step_id": "s2", "operation": "tool/read", "target": target_file,
             "approval_reason": "M4 read", "correlation_id": "m4-read"},
        ],
        harness=harness_with_tool,
        audit=audit,
    )
    assert ok is True
    assert len(outcomes) == 2
    assert outcomes[0].ok is True
    assert outcomes[1].ok is True
    # read step punya isi nyata file (bukan kosong/mock)
    assert "M4 workflow content" in str(outcomes[1].outcome.get("content", ""))
    # verification tercatat (bukan simulasi)
    assert outcomes[0].verification is not None
    assert outcomes[1].verification.get("checks", {}).get("not_simulated", True) is True


def test_m4_fail_fast_no_partial_commit(target_file, harness_with_tool):
    """Step pertama gagal (approval kosong) -> step kedua TIDAK jalan."""
    audit = harness_with_tool._audit  # noqa: SLF001
    ok, outcomes = run_gated_workflow(
        [
            # s1 TANPA approval_reason -> approval gate GAGAL -> BLOCKED
            {"step_id": "s1", "operation": "tool/read", "target": target_file,
             "approval_reason": "", "correlation_id": "m4-blocked"},
            # s2 seharusnya tidak pernah sampai dieksekusi (fail-fast)
            {"step_id": "s2", "operation": "tool/read", "target": target_file,
             "approval_reason": "M4 s2", "correlation_id": "m4-s2"},
        ],
        harness=harness_with_tool,
        audit=audit,
    )
    assert ok is False
    assert len(outcomes) == 1  # hanya s1 (fail-fast berhenti)
    assert outcomes[0].blocked is True
    assert outcomes[0].ok is False


def test_m4_universal_engine_executor_real(target_file, harness_with_tool):
    """WorkflowExecutionEngine universal_workflow pakai executor canonical -> real."""
    step_ids = ("meta_step", "read_step")
    inputs_map = {
        "meta_step": {"operation": "tool/meta", "target": target_file, "approval_reason": "M4 eng meta"},
        "read_step": {"operation": "tool/read", "target": target_file, "approval_reason": "M4 eng read"},
    }

    class _Engine:
        """Mimik WorkflowExecutionEngine.execute (contract universal_workflow)."""

        def execute(self, request_id, workflow_id, step_ids=(), inputs=None, require_approval=False, approved=False, executor=None):
            from types import SimpleNamespace

            approved_ok = (not require_approval) or approved
            results = []
            if approved_ok:
                for sid in step_ids:
                    if executor is None:
                        results.append(SimpleNamespace(step_id=sid, success=True, result={"step": sid}))
                    else:
                        step_inputs = (inputs or {}).get(sid, {})
                        results.append(executor(sid, step_inputs))
            return SimpleNamespace(request_id=request_id, workflow_id=workflow_id,
                                   approved=approved_ok, results=results,
                                   decisions=[], all=lambda: all(getattr(r, "success", False) for r in results))

    engine = _Engine()
    executor = build_universal_engine_executor(harness_with_tool, audit=harness_with_tool._audit)  # noqa: SLF001
    ctx = engine.execute("req-1", "wf-1", step_ids, inputs=inputs_map,
                         require_approval=True, approved=True, executor=executor)
    assert ctx.approved is True
    assert len(ctx.results) == 2
    # Kedua step sukses via canonical (bukan sukses palsu) -> isi nyata terbaca
    assert ctx.results[0].success is True
    assert ctx.results[1].success is True
    assert ctx.results[1].result["outcome"].get("content", "").startswith("M4 workflow content")


def test_m4_universal_engine_no_target_not_fake_success(harness_with_tool):
    """Step tanpa target nyata -> BLOCKED, BUKAN success palsu (default engine)."""
    executor = build_universal_engine_executor(harness_with_tool, audit=harness_with_tool._audit)  # noqa: SLF001
    res = executor("ghost_step", {})  # cadangan: tanpa target
    assert res.success is False  # default engine lama memberi success=True; bridge menolak


def test_m4_step_executor_maps_exception(target_file, harness_with_tool):
    """Operasi non-canonical (write fase 1) -> error ter-petakan, bukan crash."""
    ex = CanonicalStepExecutor(harness_with_tool, audit=harness_with_tool._audit)  # noqa: SLF001
    oc = ex.execute_step("w", "tool/write", target_file, {"content": "x"},
                         approval_reason="M4 write guard", timeout_seconds=10.0)
    # write bukan jalur canonical fase ini -> tidak sukses, tapi tidak crash
    assert oc.ok is False
    assert oc.error != "" or oc.blocked is True
