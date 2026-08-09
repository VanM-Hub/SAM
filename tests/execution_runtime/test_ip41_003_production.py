"""IP-4.1-003 - Production Execution (WP-21..30) tests.

Real Execution - MISSION-4.1.
Menguji Production Execution: multi-provider readiness, retry, timeout,
failure/rollback verification, metrics, production compliance, e2e.
"""

from __future__ import annotations

from sam.execution_runtime.execution_request import ExecutionRequest
from sam.execution_runtime.execution_response import ExecutionResponse
from sam.execution_runtime.execution_pipeline import ExecutionPipeline
from sam.execution_runtime.execution_runtime import ExecutionRuntime
from sam.execution_runtime.governed_execution import GovernedExecution
from sam.execution_runtime.production_execution import ProductionExecution
from sam.execution_runtime.production_compliance import ProductionComplianceChecker
from sam.execution_runtime.credential import ExecutionCredentialManager
from sam.execution_runtime.credential_verifier import CredentialVerifier
from sam.execution_runtime.provider_connection import ProviderConnectionManager


# --------------------------------------------------------------------------
# Helper: pipeline dengan mock provider (deterministik, bisa gagal)
# --------------------------------------------------------------------------


def _pipeline_with_result(status, calls=1, error=None):
    pipeline = ExecutionPipeline()
    pipeline.executor.bind(lambda r: ExecutionResponse(
        execution_id=r.execution_id, provider_id=r.provider_id,
        operation=r.operation, status=status, mode=r.mode,
        external_calls=calls if status == "completed" else 0, error=error,
    ))
    return pipeline


def _governed_with(pipeline):
    return GovernedExecution(runtime=ExecutionRuntime(pipeline=pipeline))


# --------------------------------------------------------------------------
# WP-21 - Multi Provider Execution readiness
# --------------------------------------------------------------------------


def test_production_multi_provider_readiness():
    mgr = ExecutionCredentialManager(environ={"OPENAI_API_KEY": "sk-fake-1234",
                                              "DEEPSEEK_API_KEY": "sk-fake-9999"})
    verifier = CredentialVerifier(manager=mgr)
    conn = ProviderConnectionManager(verifier=verifier)
    ready = conn.connected_providers()
    assert "openai" in ready
    assert "deepseek" in ready
    # provider non-auth tersedia tanpa credential
    assert "filesystem" in ready


# --------------------------------------------------------------------------
# WP-22/23 - Reliability & Retry Policy
# --------------------------------------------------------------------------


def test_production_retry_on_failure():
    # Pipeline yang selalu gagal -> ProductionExecution mencoba retry sampai limit
    pipeline = _pipeline_with_result("failed", calls=0, error="boom")
    gov = _governed_with(pipeline)
    pe = ProductionExecution(governed=gov, max_retries_default=2)
    req = ExecutionRequest("p-1", "openai", "chat", mode="execute", approved=True,
                           approver="van", max_retries=2)
    result = pe.run(req)
    assert result.succeeded is False
    assert len(result.attempts) == 3  # 1 percobaan + 2 retry


def test_production_succeeds_without_retry():
    pipeline = _pipeline_with_result("completed")
    gov = _governed_with(pipeline)
    pe = ProductionExecution(governed=gov)
    req = ExecutionRequest("p-2", "openai", "chat", mode="execute", approved=True,
                           approver="van")
    result = pe.run(req)
    assert result.succeeded is True
    assert result.final_status == "completed"
    assert len(result.attempts) == 1
    assert result.metrics is not None


def test_production_metrics_recorded():
    pipeline = _pipeline_with_result("completed")
    gov = _governed_with(pipeline)
    pe = ProductionExecution(governed=gov)
    req = ExecutionRequest("p-3", "openai", "chat", mode="execute", approved=True,
                           approver="van", payload={"q": "hello"})
    result = pe.run(req)
    assert result.metrics.execution_id == "p-3"
    assert result.metrics.retries == 0
    assert result.metrics.external_calls == 1
    assert result.metrics.size_payload > 0


# --------------------------------------------------------------------------
# WP-25 - Failure Verification
# --------------------------------------------------------------------------


def test_production_failure_verification():
    # Gagal -> rollback outcome menyatakan kegagalan, no success
    pipeline = _pipeline_with_result("failed", calls=0, error="timeout")
    gov = _governed_with(pipeline)
    pe = ProductionExecution(governed=gov, max_retries_default=0)
    req = ExecutionRequest("p-4", "openai", "chat", mode="execute", approved=True,
                           approver="van", max_retries=0)
    result = pe.run(req)
    assert result.succeeded is False
    assert result.rollback.rollback_requested is True


# --------------------------------------------------------------------------
# WP-26 - Rollback Verification
# --------------------------------------------------------------------------


def test_production_rollback_evaluation():
    # Sukses -> rollback tidak perlu
    pipeline = _pipeline_with_result("completed")
    gov = _governed_with(pipeline)
    pe = ProductionExecution(governed=gov, max_retries_default=0)
    req = ExecutionRequest("p-5", "openai", "chat", mode="execute", approved=True,
                           approver="van", max_retries=0)
    result = pe.run(req)
    assert result.rollback.rollback_requested is False
    assert result.rollback.reversible is True


def test_production_blocked_no_approval_no_rollback():
    # Tanpa approval -> blocked, tidak ada eksekusi, tidak ada side-effect rollback
    pipeline = _pipeline_with_result("completed")
    gov = _governed_with(pipeline)
    pe = ProductionExecution(governed=gov, max_retries_default=0)
    req = ExecutionRequest("p-6", "openai", "chat", mode="execute", approved=False,
                           max_retries=0)
    result = pe.run(req)
    assert result.succeeded is False
    assert result.final_status in ("blocked", "failed")
    assert result.rollback.rollback_requested is True


# --------------------------------------------------------------------------
# WP-27 - Operational Metrics (subset, via ProductionExecutionResult.metrics)
# --------------------------------------------------------------------------


def test_production_elapsed_time_non_negative():
    pipeline = _pipeline_with_result("completed")
    gov = _governed_with(pipeline)
    pe = ProductionExecution(governed=gov)
    req = ExecutionRequest("p-7", "openai", "chat", mode="execute", approved=True,
                           approver="van")
    result = pe.run(req)
    assert result.elapsed_ms >= 0


# --------------------------------------------------------------------------
# WP-28 - Production Compliance
# --------------------------------------------------------------------------


def test_production_compliance_passes_clean():
    checker = ProductionComplianceChecker()
    result = checker.check(subject="production", source_blocks=["def run():\n    return 'ok'\n"])
    assert result.passed is True


def test_production_compliance_detects_auto_approve():
    checker = ProductionComplianceChecker()
    bad = "def go():\n    auto_approve('x')\n    return 1\n"
    result = checker.check(subject="prod-bad", source_blocks=[bad])
    assert result.detail  # gagal atau terindikasi


def test_production_compliance_approval_invariant():
    from sam.execution_runtime.execution_request import ExecutionRequest
    checker = ProductionComplianceChecker()
    # execute tanpa approval -> compliance menolak
    req = ExecutionRequest("c-1", "openai", "chat", mode="execute", approved=False)
    result = checker.check(subject="prod-approved", source_blocks=[], requests=[req])
    assert result.passed is False


# --------------------------------------------------------------------------
# WP-29/30 - End-to-End Certification & Baseline
# --------------------------------------------------------------------------


def test_production_end_to_end_with_mock():
    """Jalur produksi end-to-end: approved + execute success -> metrics + no rollback."""
    pipeline = _pipeline_with_result("completed")
    gov = _governed_with(pipeline)
    pe = ProductionExecution(governed=gov, max_retries_default=1)
    req = ExecutionRequest("e2e-prod", "openai", "chat", mode="execute", approved=True,
                           approver="van")
    result = pe.run(req)
    assert result.succeeded is True
    assert result.final_status == "completed"
    assert result.metrics.external_calls >= 1
    assert result.rollback.rollback_requested is False
    assert result.rollback.reversible is True
