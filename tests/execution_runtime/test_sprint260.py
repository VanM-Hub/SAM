"""Sprint 260 - Real Provider Activation.

Program C - Real Execution Runtime.
Aktifkan provider nyata (di provider layer). Test via mock provider.
Cakupan: mock provider, integration mock, approval gate, cancellation,
timeout, rollback metadata, error propagation, provider unavailable.
"""
from __future__ import annotations
import pytest

from sam.execution_runtime.execution_request import ExecutionRequest
from sam.execution_runtime.execution_response import ExecutionResponse
from sam.execution_runtime.execution_pipeline import ExecutionPipeline
from sam.execution_runtime.execution_runtime import ExecutionRuntime
from sam.execution_runtime.provider_activation import ProviderActivationExecutor
from sam.execution_runtime.rollback_runtime import RollbackRuntime
from sam.execution_runtime.approval_gate import ApprovalGate
from sam.execution_runtime.execution_safety import ExecutionSafety
from sam.providers.execution.provider_executor import (
    ProviderExecutor, ProviderExecutionConfig, ProviderUnavailableError,
    PROVIDER_ENV,
)
from sam.providers.execution.real_provider_activation import (
    ProviderCancellation, enforce_timeout, ActivationReport,
)
from sam.execution_runtime.conversation_provider_activation import (
    ConversationProviderActivation, ConversationProviderActivationView,
)
from sam.execution_runtime.dashboard_provider_activation import (
    DashboardProviderActivation,
)


# ---------- Mock provider ----------

class MockRealProvider(ProviderExecutor):
    """Mock executor untuk test (sepenuhnya lokal, external_calls dihitung)."""

    def __init__(self, fail_on=None, calls_override=None) -> None:
        super().__init__()
        self.calls = 0
        self._fail = fail_on or []
        self._calls_override = calls_override

    def available(self, provider_id: str) -> bool:
        return True

    def execute(self, provider_id, operation, payload=None, timeout_seconds=60):
        self.calls += 1
        if provider_id in self._fail:
            raise ProviderUnavailableError(f"mock unavailable: {provider_id}")
        return {"provider_id": provider_id, "operation": operation,
                "status": "completed", "payload": dict(payload or {}),
                "external_calls": self._calls_override or 1}


def make_req(mode="execute", approved=True, provider="openai", op="chat",
             token=None, timeout=60, retries=2):
    return ExecutionRequest("e1", provider, op, mode=mode, approved=approved,
                            approver="van" if approved else "",
                            cancellation_token=token, timeout_seconds=timeout,
                            max_retries=retries)


def test_provider_executor_env_known_ten():
    assert len(PROVIDER_ENV) == 10
    assert "openai" in PROVIDER_ENV and "ollama" in PROVIDER_ENV


def test_provider_execution_config_no_hardcoded_credentials():
    # config tanpa api_key_env = non-auth (mis. filesystem) => available True
    cfg = ProviderExecutionConfig(provider_id="filesystem")
    assert cfg.api_key_env == ""
    assert cfg.has_credentials() is True


def test_no_hardcoded_secrets_in_provider_executor_source():
    import inspect
    import sam.providers.execution.provider_executor as pe
    src = inspect.getsource(pe)
    for secret_pattern in ("sk-", "ghp_", "Bearer ", "api-key-value", "AIza"):
        assert secret_pattern not in src, f"found hardcoded credential: {secret_pattern}"


def test_provider_executor_config_unknown_raises():
    ex = ProviderExecutor()
    with pytest.raises(ProviderUnavailableError):
        ex.config("ghost")


def test_provider_executor_available_non_auth():
    # filesystem non-auth => available True (tanpa key)
    ex = ProviderExecutor()
    assert ex.available("filesystem") is True


def test_provider_executor_requires_key_for_openai():
    ex = ProviderExecutor()
    # bila env tidak ada -> butuh key -> unavailable
    assert ex.available("openai") is False or bool(__import__("os").environ.get("OPENAI_API_KEY"))


def test_provider_executor_unavailable_raises_on_execute():
    ex = ProviderExecutor()
    with pytest.raises(ProviderUnavailableError):
        ex.execute("openai", "chat")  # tanpa kredensial


def test_provider_executor_non_auth_execute_ok():
    ex = ProviderExecutor()
    r = ex.execute("filesystem", "read", {"path": "/tmp"})
    assert r["status"] == "completed"
    assert r["external_calls"] == 1


def test_mock_provider_executes_and_counts():
    mock = MockRealProvider()
    assert mock.execute("openai", "chat", payload={"q": "hi"})["status"] == "completed"
    assert mock.calls == 1


# ---------- approval gate ----------

def test_activation_executor_blocks_preview():
    ex = ProviderActivationExecutor(real=MockRealProvider())
    resp = ex.call(make_req(mode="preview"))
    assert resp.status == "preview"
    assert resp.external_calls == 0


def test_activation_executor_blocks_unapproved():
    ex = ProviderActivationExecutor(real=MockRealProvider())
    resp = ex.call(make_req(mode="execute", approved=False))
    assert resp.status == "blocked"
    assert "approval" in resp.error
    assert resp.external_calls == 0


def test_activation_executor_provider_unavailable():
    mock = MockRealProvider(fail_on=["openai"])
    ex = ProviderActivationExecutor(real=mock)
    resp = ex.call(make_req(provider="openai"))
    assert resp.status == "failed"
    assert "unavailable" in resp.error
    assert resp.external_calls == 0


def test_activation_executor_success_execute():
    mock = MockRealProvider()
    ex = ProviderActivationExecutor(real=mock)
    resp = ex.call(make_req())
    assert resp.status == "completed"
    assert resp.external_calls == 1
    assert mock.calls == 1


def test_error_propagation():
    class Boom(MockRealProvider):
        def execute(self, provider_id, operation, payload=None, timeout_seconds=60):
            raise RuntimeError("boom")
    ex = ProviderActivationExecutor(real=Boom())
    resp = ex.call(make_req())
    assert resp.status == "failed"
    assert "boom" in resp.error


# ---------- cancellation ----------

def test_cancellation_token():
    req = make_req(token="tok-A")
    ex = ProviderActivationExecutor(real=MockRealProvider())
    ex.cancel_token("tok-A")
    resp = ex.call(req)
    assert resp.status == "cancelled"
    assert resp.external_calls == 0


def test_not_cancelled_executes():
    req = make_req(token="tok-B")
    ex = ProviderActivationExecutor(real=MockRealProvider())
    resp = ex.call(req)
    assert resp.status == "completed"


def test_provider_cancellation_class():
    c = ProviderCancellation("t1")
    assert c.is_cancelled is False
    assert c.token == "t1"
    c.cancel()
    assert c.is_cancelled is True


# ---------- timeout ----------

def test_enforce_timeout():
    assert enforce_timeout(5000, 3) is True   # 5s > 3s
    assert enforce_timeout(2000, 3) is False  # 2s <= 3s


def test_timeout_boundary():
    assert enforce_timeout(3000, 3) is False  # sama -> tidak timeout


# ---------- rollback metadata ----------

def test_rollback_after_execution_metadata():
    rr = RollbackRuntime()
    rr.capture_metadata("exec-1", {"state": "done"})
    out = rr.run(__import__("sam.execution_runtime.rollback_request",
                            fromlist=["RollbackRequest"]).RollbackRequest(
                            rollback_id="rb1", execution_id="e1"))
    assert "exec-1" in out.report.restored_metadata
    assert out.external_calls == 0  # rollback tidak menyentuh external world


def test_rollback_does_not_undo_external():
    # menjamin rollback scope metadata, bukan external world
    rr = RollbackRuntime()
    out = rr.run(__import__("sam.execution_runtime.rollback_request",
                            fromlist=["RollbackRequest"]).RollbackRequest(
                            rollback_id="rb2", execution_id="e2"))
    assert out.plan.scope == "metadata"


# ---------- integration pipeline with real activation ----------

def test_full_pipeline_execute_with_mock():
    mock = MockRealProvider()
    ex = ProviderActivationExecutor(real=mock)
    pl = ExecutionPipeline(executor=ex)
    req = make_req()
    res = pl.run("F1", req)
    assert res.executed is True
    assert res.external_calls == 1
    assert res.report.status == "completed"


def test_full_pipeline_preview_no_call():
    mock = MockRealProvider()
    ex = ProviderActivationExecutor(real=mock)
    pl = ExecutionPipeline(executor=ex)
    res = pl.run("F2", make_req(mode="preview"))
    assert res.executed is False
    assert res.external_calls == 0
    assert mock.calls == 0  # tidak ada panggilan provider


def test_runtime_with_activation():
    mock = MockRealProvider()
    ex = ProviderActivationExecutor(real=mock)
    pl = ExecutionPipeline(executor=ex)
    rt = ExecutionRuntime(pipeline=pl)
    out = rt.run("R1", make_req())
    assert out.executed is True
    assert out.external_calls == 1


def test_safety_blocks_unapproved_even_with_mock():
    safety = ExecutionSafety()
    verdict = safety.assess(make_req(approved=False))
    assert verdict.allowed is False


# ---------- bridges ----------

def test_conversation_provider_activation_view():
    ex = ProviderActivationExecutor(real=MockRealProvider())
    conv = ConversationProviderActivation(executor=ex)
    v = conv.view("conv-1")
    assert isinstance(v, ConversationProviderActivationView)
    assert v.external_calls == 0


def test_dashboard_provider_activation_rows():
    dash = DashboardProviderActivation(executor=ProviderExecutor())
    rows = dash.rows()
    assert len(rows) == 10
    s = dash.summary()
    assert s["total"] == 10
    assert s["external_calls"] == 0


# ---------- non-provider-specific constraint ----------

def test_agent_mission_do_not_know_provider():
    # pastikan execution_runtime TIDAK berisi logic provider-specific
    import inspect
    import sam.execution_runtime.provider_activation as pa
    src = inspect.getsource(pa)
    assert "def _openai_specific" not in src
    assert "def _gemini_specific" not in src


def test_no_forbidden_imports_activation():
    import inspect
    import sam.execution_runtime.provider_activation as pa
    src = inspect.getsource(pa)
    for banned in ("import socket", "import httpx", "import asyncio",
                   "import threading", "import subprocess"):
        assert banned not in src


def test_no_forbidden_imports_provider_executor():
    # provider layer BOLEH network (requests/httpx) TAPI tidak di file helper
    import inspect
    import sam.providers.execution.real_provider_activation as rp
    src = inspect.getsource(rp)
    for banned in ("import asyncio", "import threading"):
        assert banned not in src


def test_network_only_on_execute():
    # preview TIDAK pernah memicu executor (external_calls=0)
    mock = MockRealProvider()
    ex = ProviderActivationExecutor(real=mock)
    pl = ExecutionPipeline(executor=ex)
    res = pl.run("N1", make_req(mode="preview"))
    assert res.external_calls == 0
    assert mock.calls == 0


def test_external_calls_positive_only_with_approval():
    mock = MockRealProvider()
    ex = ProviderActivationExecutor(real=mock)
    pl = ExecutionPipeline(executor=ex)
    res_ok = pl.run("C1", make_req(approved=True))
    assert res_ok.external_calls == 1
    res_no = pl.run("C2", make_req(approved=False))
    assert res_no.external_calls == 0
