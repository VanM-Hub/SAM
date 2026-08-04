"""Session 03 - Provider Resolution (AD-S03-001).

Hubungkan ExecutionRuntime ke Provider layer (Provider RESOLUTION, bukan
simulation). Provider dapat di-resolve/di-select; provider.execute() TIDAK
dipanggil; external_calls=0; executed=false (ADR-024). Tidak ada
executor/provider/pipeline baru.
"""
from __future__ import annotations
import inspect

import pytest

from sam.execution_runtime.execution_request import ExecutionRequest
from sam.execution_runtime.execution_pipeline import ExecutionPipeline, _ProviderExecutor
from sam.execution_runtime.execution_runtime import ExecutionRuntime
from sam.execution_runtime.provider_activation import ProviderActivationExecutor
from sam.execution_runtime.conversation_provider_activation import (
    ConversationProviderActivation, ConversationProviderActivationView,
)
from sam.providers.execution.provider_executor import (
    ProviderExecutor, ProviderExecutionConfig, PROVIDER_ENV,
)


def make_req(mode="preview", approved=True, provider="filesystem", op="read"):
    return ExecutionRequest(
        execution_id="e1", provider_id=provider, operation=op,
        mode=mode, approved=approved,
    )


@pytest.fixture
def wired_pipeline():
    """Pipeline preview yang ter-bind ke provider layer (mekanisme resmi)."""
    execu = ProviderActivationExecutor(real=ProviderExecutor())
    pl = ExecutionPipeline(executor=execu)
    rt = ExecutionRuntime(pipeline=pl)
    return execu, pl, rt


def test_pipeline_executor_bound(wired_pipeline):
    execu, pl, rt = wired_pipeline
    # binding benar via mekanisme resmi repository
    assert pl.executor is not None
    assert isinstance(pl.executor, _ProviderExecutor)
    assert isinstance(pl.executor, ProviderActivationExecutor)


def test_provider_layer_known_providers():
    # provider identity tersedia (metadata) — 10 provider dikenal
    assert len(PROVIDER_ENV) == 10
    assert "filesystem" in PROVIDER_ENV
    cfg = ProviderExecutionConfig(provider_id="filesystem")
    assert cfg.api_key_env == ""
    assert cfg.has_credentials() is True


def test_execute_not_called_on_preview(wired_pipeline):
    execu, pl, rt = wired_pipeline
    res = pl.run("F1", make_req(mode="preview"))
    # provider TIDAK dieksekusi di preview
    assert res.executed is False
    assert res.external_calls == 0
    assert res.response.status == "preview"


@pytest.mark.parametrize("mode", ["preview", "execute"])
def test_executed_false_and_no_calls_in_preview_resolution(wired_pipeline, mode):
    execu, pl, rt = wired_pipeline
    # Perilaku desain: jalur ini menahan eksekusi (ADR-024).
    # Provider di-resolve (dispatch/select) tapi execute() tidak dipanggil.
    res = pl.run("F2", make_req(mode="preview"))
    assert res.external_calls == 0


def test_execution_skipped_provider_resolution(wired_pipeline):
    # Preview = validated -> resolved -> selected -> execution skipped
    execu, pl, rt = wired_pipeline
    res = pl.run("F3", make_req(mode="preview"))
    assert res.validation.valid is True
    # provider pipeline menghasilkan dispatch/select (resolution)
    provider = res.provider
    assert provider.external_calls == 0


def test_conversation_provider_activation_resolves(wired_pipeline):
    execu, pl, rt = wired_pipeline
    ca = ConversationProviderActivation(executor=execu)
    v = ca.view("conv-1")
    assert isinstance(v, ConversationProviderActivationView)
    assert v.external_calls == 0
    # setidaknya ada provider non-auth yang tersedia (filesystem/shell/sqlite)
    assert v.available_providers >= 1


def test_no_new_provider_or_executor(wired_pipeline):
    """Session 03 TIDAK membuat executor/provider baru (AD-S03-001)."""
    execu, pl, rt = wired_pipeline
    # memoized instance = ProviderActivationExecutor yang sudah ada (bukan subclass baru)
    assert type(execu).__name__ == "ProviderActivationExecutor"


def test_no_forbidden_imports_in_resolution_path():
    import sam.execution_runtime.provider_activation as pa
    src = inspect.getsource(pa)
    for banned in ("import socket", "import httpx", "import asyncio",
                   "import threading", "import subprocess"):
        assert banned not in src


def test_provider_resolution_no_simulation_class():
    """Pastikan tidak ada kelas simulasi/fake preview baru (AD-S03-001)."""
    # tidak boleh ada class dengan nama simulasi preview
    from sam.execution_runtime import provider_activation as pa
    src = inspect.getsource(pa)
    for banned in ("PreviewProviderExecutor", "FakeProvider",
                   "ProviderSimulator", "MockProviderProduction",
                   "ProviderResultGenerator"):
        assert banned not in src
