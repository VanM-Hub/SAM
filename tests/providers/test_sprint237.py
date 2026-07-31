"""Test Sprint 237 — Execution Preview Integration (Program A).
Pipeline eksplisit Preview -> Approval -> Execute. Approval-gated,
preview-first, external_calls=0. Tanpa approval -> BLOCKED.
"""
import pytest

from sam.providers.execution.execution_preview import (
    ExecutionRequest,
    ExecutionApproval,
    ExecutionResult,
    ExecutionState,
    ExecutionPipeline,
)

FROZEN_DTOS = [ExecutionRequest, ExecutionApproval, ExecutionResult]


class TestExecutionPipeline:
    def test_preview_awaits_approval(self):
        pipe = ExecutionPipeline()
        req = ExecutionRequest(
            execution_id="e1", provider_id="openai", operation="generate"
        )
        res = pipe.preview(req)
        assert res.state == ExecutionState.AWAITING_APPROVAL
        assert res.external_calls == 0
        assert res.preview is True
        assert pipe.pending_count() == 1

    def test_approve_then_execute(self):
        pipe = ExecutionPipeline()
        req = ExecutionRequest("e2", "gemini", "generate")
        pipe.preview(req)
        appr = pipe.approve(ExecutionApproval("e2", True, "ok"))
        assert appr.state == ExecutionState.APPROVED
        assert appr.external_calls == 0
        done = pipe.execute("e2")
        assert done.state == ExecutionState.COMPLETED
        assert done.ok is True

    def test_execute_without_approval_blocked(self):
        pipe = ExecutionPipeline()
        pipe.preview(ExecutionRequest("e3", "ollama", "generate"))
        res = pipe.execute("e3")
        assert res.state == ExecutionState.BLOCKED
        assert res.ok is False
        assert res.external_calls == 0
        assert "belum ada approval" in res.detail

    def test_reject_blocks_execution(self):
        pipe = ExecutionPipeline()
        pipe.preview(ExecutionRequest("e4", "openai", "generate"))
        rej = pipe.approve(ExecutionApproval("e4", False, "tidak diizinkan"))
        assert rej.state == ExecutionState.REJECTED
        assert rej.ok is False
        res = pipe.execute("e4")
        assert res.state == ExecutionState.BLOCKED

    def test_unknown_execution(self):
        pipe = ExecutionPipeline()
        res = pipe.approve(ExecutionApproval("nope", True))
        assert res.state == ExecutionState.BLOCKED
        assert res.execution_id == "nope"

    def test_status(self):
        pipe = ExecutionPipeline()
        pipe.preview(ExecutionRequest("e5", "deepseek", "generate"))
        pipe.approve(ExecutionApproval("e5", True))
        pipe.execute("e5")
        st = pipe.status("e5")
        assert st.state == ExecutionState.COMPLETED

    def test_external_calls_always_zero(self):
        pipe = ExecutionPipeline()
        pipe.preview(ExecutionRequest("e6", "openai", "generate"))
        pipe.approve(ExecutionApproval("e6", True))
        done = pipe.execute("e6")
        assert done.external_calls == 0


class TestExecutionImmutability:
    @pytest.mark.parametrize("cls", FROZEN_DTOS)
    def test_dto_frozen(self, cls):
        assert cls.__dataclass_params__.frozen is True
