"""IP-4.1-001 - Provider Execution Foundation (WP-01..05) tests.

Real Execution - MISSION-4.1.
Menguji Credential Management, Credential Verification, Execution Session,
Provider Connection, dan Execution Context. Semua read-only/deterministik.
"""

from __future__ import annotations

import pytest

from sam.execution_runtime.execution_request import ExecutionRequest
from sam.execution_runtime.credential import (
    CredentialStatus,
    ExecutionCredentialManager,
    mask_secret,
    CREDENTIAL_REFERENCES,
)
from sam.execution_runtime.credential_verifier import CredentialVerifier
from sam.execution_runtime.execution_session import (
    ExecutionSessionManager,
    SessionState,
    deterministic_session_id,
)
from sam.execution_runtime.provider_connection import ProviderConnectionManager
from sam.execution_runtime.execution_context_manager import (
    ExecutionContextBuilder,
    GovernanceContext,
    ProviderContext,
)


# --------------------------------------------------------------------------
# WP-01 - Credential Management
# --------------------------------------------------------------------------


def test_credential_no_hardcoded_secret_in_source():
    import inspect
    import sam.execution_runtime.credential as mod
    src = inspect.getsource(mod)
    for secret in ("sk-", "ghp_", "AIza", "api-key-value"):
        assert secret not in src, f"hardcoded credential ditemukan: {secret}"


def test_credential_references_no_secret_values():
    # Referensi hanya berisi NAMA env var, bukan nilai secret.
    for pid, ref in CREDENTIAL_REFERENCES.items():
        assert ref.provider_id == pid
        if ref.env_var:
            assert ref.env_var.startswith(("OPENAI", "ANTHROPIC", "GEMINI",
                                           "DEEPSEEK", "OLLAMA", "OPENCLAW", "DOCKER"))


def test_mask_secret_deterministic():
    assert mask_secret("") == ""
    assert mask_secret("abcd") == "****"
    assert mask_secret("sk-test-value-1234") == "**************1234"
    # deterministik: dua kali sama
    assert mask_secret("abc123456789") == mask_secret("abc123456789")


def test_credential_manager_missing_env():
    mgr = ExecutionCredentialManager(environ={})
    r = mgr.resolve("openai")
    assert r.status == CredentialStatus.MISSING
    assert r.available is False
    assert r.missing_env == "OPENAI_API_KEY"


def test_credential_manager_available_env():
    mgr = ExecutionCredentialManager(environ={"OPENAI_API_KEY": "sk-fake-1234"})
    r = mgr.resolve("openai")
    assert r.status == CredentialStatus.OK
    assert r.available is True
    assert r.masked_value != "sk-fake-1234"  # dimasking


def test_credential_manager_non_auth():
    mgr = ExecutionCredentialManager(environ={})
    r = mgr.resolve("filesystem")
    assert r.available is True  # non-auth selalu tersedia


def test_credential_audit_recorded():
    mgr = ExecutionCredentialManager(environ={"OPENAI_API_KEY": "sk-fake-1234"})
    mgr.resolve("openai")
    mgr.verify("openai")
    assert len(mgr.audit_log()) >= 2
    for rec in mgr.audit_log():
        assert rec.provider_id == "openai"
        assert rec.accessed_at
        assert "OPENAI_API_KEY" in rec.env_var or rec.env_var == ""


# --------------------------------------------------------------------------
# WP-02 - Credential Verification
# --------------------------------------------------------------------------


def test_verifier_verified_when_env_present():
    mgr = ExecutionCredentialManager(environ={"DEEPSEEK_API_KEY": "sk-fake-9999"})
    v = CredentialVerifier(manager=mgr)
    r = v.verify("deepseek")
    assert r.verified is True
    assert r.status == "verified"


def test_verifier_missing_when_no_env():
    mgr = ExecutionCredentialManager(environ={})
    v = CredentialVerifier(manager=mgr)
    r = v.verify("anthropic")
    assert r.verified is False
    assert r.status == "missing"
    assert r.reason  # failure punya alasan


def test_verifier_rejects_too_short():
    mgr = ExecutionCredentialManager(environ={"OPENAI_API_KEY": "ab"})
    v = CredentialVerifier(manager=mgr)
    r = v.verify("openai")
    assert r.verified is False
    assert r.status == "invalid"


def test_verifier_can_execute_guard():
    mgr = ExecutionCredentialManager(environ={})
    v = CredentialVerifier(manager=mgr)
    # credential gagal -> can_execute False (tidak ada execution saat gagal)
    assert v.can_execute("openai") is False
    mgr2 = ExecutionCredentialManager(environ={"GEMINI_API_KEY": "sk-fake-1234"})
    v2 = CredentialVerifier(manager=mgr2)
    assert v2.can_execute("gemini") is True


# --------------------------------------------------------------------------
# WP-03 - Execution Session
# --------------------------------------------------------------------------


def test_session_create_deterministic_id():
    m = ExecutionSessionManager()
    s1 = m.create("openai", "exec-1")
    s2 = m.create("openai", "exec-1")  # idempotent -> session sama
    assert s1.session_id == s2.session_id
    assert s1.session_id == deterministic_session_id("openai", "exec-1")
    assert s1.state == SessionState.CREATED


def test_session_lifecycle_valid():
    m = ExecutionSessionManager()
    s = m.create("deepseek", "exec-2")
    a = m.transition(s.session_id, SessionState.ACTIVE)
    assert a is not None and a.state == SessionState.ACTIVE
    c = m.transition(s.session_id, SessionState.COMPLETED)
    cl = m.transition(s.session_id, SessionState.CLOSED)
    assert cl is not None and cl.finalized is True


def test_session_immutable_after_final():
    m = ExecutionSessionManager()
    s = m.create("openai", "exec-3")
    m.transition(s.session_id, SessionState.CANCELLED)
    m.transition(s.session_id, SessionState.CLOSED)
    # transisi setelah final -> None
    assert m.transition(s.session_id, SessionState.ACTIVE) is None


def test_session_invalid_transition_none():
    m = ExecutionSessionManager()
    s = m.create("shell", "exec-4")
    # ACTIVE -> CANCELLED valid; tapi CREATED -> COMPLETED tidak valid (harus lewat ACTIVE)
    assert m.transition(s.session_id, SessionState.COMPLETED) is None


def test_session_auditable_events():
    m = ExecutionSessionManager()
    s = m.create("sqlite", "exec-5")
    m.transition(s.session_id, SessionState.ACTIVE)
    m.transition(s.session_id, SessionState.COMPLETED)
    m.transition(s.session_id, SessionState.CLOSED)
    finished = m.get(s.session_id)
    assert len(finished.events) == 4  # created, active, completed, closed


# --------------------------------------------------------------------------
# WP-04 - Provider Connection
# --------------------------------------------------------------------------


def test_connection_connected_when_credential_ok():
    mgr = ExecutionCredentialManager(environ={"OPENAI_API_KEY": "sk-fake-1234"})
    pcm = ProviderConnectionManager(verifier=CredentialVerifier(manager=mgr))
    c = pcm.connect("openai")
    assert c.connected is True
    assert c.health.healthy is True
    assert c.identity.known is True


def test_connection_not_connected_when_no_credential():
    mgr = ExecutionCredentialManager(environ={})
    pcm = ProviderConnectionManager(verifier=CredentialVerifier(manager=mgr))
    c = pcm.connect("anthropic")
    assert c.connected is False
    assert c.reason  # failure dapat dijelaskan


def test_connection_non_auth_connected():
    mgr = ExecutionCredentialManager(environ={})
    pcm = ProviderConnectionManager(verifier=CredentialVerifier(manager=mgr))
    assert pcm.connect("filesystem").connected is True


def test_connection_unknown_provider():
    pcm = ProviderConnectionManager()
    c = pcm.connect("ghost")
    assert c.connected is False
    assert c.identity.known is False


def test_connection_can_execute_guard():
    mgr = ExecutionCredentialManager(environ={})
    pcm = ProviderConnectionManager(verifier=CredentialVerifier(manager=mgr))
    assert pcm.can_execute("openai") is False  # no execute saat gagal connect
    assert pcm.can_execute("filesystem") is True  # non-auth


# --------------------------------------------------------------------------
# WP-05 - Execution Context
# --------------------------------------------------------------------------


def test_context_from_request():
    from sam.execution_runtime.execution_request import ExecutionRequest
    req = ExecutionRequest("e9", "openai", "chat", mode="execute", approved=True,
                           approver="van")
    b = ExecutionContextBuilder()
    ctx = b.from_request(req, approval_id="ap-1")
    assert ctx.provider.provider_id == "openai"
    assert ctx.provider.operation == "chat"
    assert ctx.provider.mode == "execute"
    assert ctx.governance.approver == "van"
    assert req.execution_id in ctx.trace_ref


def test_context_immutable_and_traceable():
    b = ExecutionContextBuilder()
    ctx = b.build(
        "ctx-1",
        governance=GovernanceContext(approval_id="ap-9", approver="van"),
        provider=ProviderContext(provider_id="deepseek", operation="chat"),
        trace_ref=("ref-a", "ref-b"),
    )
    assert ctx.context_id == "ctx-1"
    assert ctx.governance.approval_id == "ap-9"
    assert ctx.provider.provider_id == "deepseek"
    assert set(ctx.trace_ref) == {"ref-a", "ref-b"}


def test_context_defaults():
    b = ExecutionContextBuilder()
    ctx = b.build("ctx-default")
    assert ctx.governance.approval_required is True
    assert ctx.provider.mode == "preview"
    assert ctx.created_at


# --------------------------------------------------------------------------
# WP-06/07 - Execution Request/Response Serializer
# --------------------------------------------------------------------------


def test_request_serializer_roundtrip():
    from sam.execution_runtime.execution_serializer import ExecutionRequestSerializer
    req = ExecutionRequest("rt-1", "openai", "chat", mode="execute",
                           approved=True, approver="van", timeout_seconds=30,
                           max_retries=1)
    d = ExecutionRequestSerializer.to_dict(req)
    assert d["execution_id"] == "rt-1"
    assert d["approved"] is True
    restored = ExecutionRequestSerializer.from_dict(d)
    assert restored == req


def test_request_serializer_json_deterministic():
    from sam.execution_runtime.execution_serializer import ExecutionRequestSerializer
    req = ExecutionRequest("rt-2", "deepseek", "chat", payload={"q": "hello"})
    a = ExecutionRequestSerializer.to_json(req)
    b = ExecutionRequestSerializer.to_json(req)
    assert a == b  # deterministik (sort_keys)


def test_request_serializer_rejects_invalid_mode():
    from sam.execution_runtime.execution_serializer import (
        ExecutionRequestSerializer, ExecutionSerializationError,
    )
    with pytest.raises(ExecutionSerializationError):
        ExecutionRequestSerializer.from_dict({
            "execution_id": "x", "provider_id": "y", "mode": "teleport",
        })


def test_response_serializer_roundtrip():
    from sam.execution_runtime.execution_serializer import ExecutionResponseSerializer
    from sam.execution_runtime.execution_response import ExecutionResponse
    resp = ExecutionResponse("e-1", "openai", "chat", status="completed",
                             mode="execute", external_calls=1)
    d = ExecutionResponseSerializer.to_dict(resp)
    restored = ExecutionResponseSerializer.from_dict(d)
    assert restored == resp
    assert restored.external_calls == 1


# --------------------------------------------------------------------------
# WP-08 - Execution Audit
# --------------------------------------------------------------------------


def test_audit_record_and_verify():
    from sam.execution_runtime.execution_audit import (
        ExecutionAudit, AuditTimelineStep,
    )
    audit = ExecutionAudit()
    rec = audit.record(
        "e-1", "openai", "chat", "execute", "completed",
        (AuditTimelineStep("request", "ok"), AuditTimelineStep("provider", "ok", external_calls=1)),
        approver="van", approval_id="ap-1",
    )
    assert audit.verify("e-1") is True
    assert rec.hash
    assert rec.approver == "van"


def test_audit_immutable_append_only():
    from sam.execution_runtime.execution_audit import ExecutionAudit, AuditTimelineStep
    audit = ExecutionAudit()
    audit.record("e-2", "deepseek", "chat", "execute", "completed",
                 (AuditTimelineStep("request", "ok"),))
    # mendaftar ulang id yang sama -> idempotent, tidak duplikasi
    again = audit.record("e-2", "deepseek", "chat", "execute", "completed",
                         (AuditTimelineStep("request", "ok"),))
    assert audit.summary().total == 1
    assert again is not None


def test_audit_deterministic_hash():
    from sam.execution_runtime.execution_audit import (
        AuditTimelineStep, audit_hash,
    )
    tl = (AuditTimelineStep("request", "ok"), AuditTimelineStep("provider", "ok", external_calls=1))
    h1 = audit_hash("e-3", "openai", "chat", "execute", "completed", tl)
    h2 = audit_hash("e-3", "openai", "chat", "execute", "completed", tl)
    assert h1 == h2


# --------------------------------------------------------------------------
# WP-09 - Execution Compliance
# --------------------------------------------------------------------------


def test_compliance_approval_gate_present():
    from sam.execution_runtime.execution_compliance import ExecutionComplianceChecker
    checker = ExecutionComplianceChecker()
    result = checker.check(subject="execution_runtime")
    assert result.passed is True
    assert result.total_checks >= 1


def test_compliance_governed_invariant_execute():
    from sam.execution_runtime.execution_compliance import ExecutionComplianceChecker
    from sam.execution_runtime.execution_request import ExecutionRequest
    checker = ExecutionComplianceChecker()
    # execute tanpa approval -> can_proceed False (Article V)
    req = ExecutionRequest("c-1", "openai", "chat", mode="execute", approved=False)
    inv = checker.verify_governed(req)
    assert inv.can_proceed is False
    assert "approval" in inv.reason
    # execute + approval + approver -> can_proceed True
    req2 = ExecutionRequest("c-2", "openai", "chat", mode="execute",
                            approved=True, approver="van")
    assert checker.verify_governed(req2).can_proceed is True


def test_compliance_no_bypass_source():
    from sam.execution_runtime.execution_compliance import ExecutionComplianceChecker
    checker = ExecutionComplianceChecker()
    bad = """def f():
    grant_privilege('admin')
    return 1
"""
    checks = list(checker.scan_source(bad))
    assert any(not c.passed for c in checks)
    clean = """def f():
    return 'ok'
"""
    assert list(checker.scan_source(clean)) == []


# --------------------------------------------------------------------------
# WP-10 - Integration & Certification (end-to-end IP-4.1-001)
# --------------------------------------------------------------------------


def test_integration_full_governed_execution_path():
    """Alur utuh IP-4.1-001: credential -> verifier -> connection -> session
    -> request/response -> audit -> compliance, untuk eksekusi yang disetujui.
    """
    from sam.execution_runtime.execution_audit import (
        ExecutionAudit, AuditTimelineStep,
    )
    from sam.execution_runtime.execution_compliance import ExecutionComplianceChecker
    from sam.execution_runtime.execution_response import ExecutionResponse
    from sam.execution_runtime.execution_serializer import (
        ExecutionRequestSerializer, ExecutionResponseSerializer,
    )
    from sam.execution_runtime.credential_verifier import CredentialVerifier
    from sam.execution_runtime.execution_session import ExecutionSessionManager
    from sam.execution_runtime.provider_connection import ProviderConnectionManager

    mgr = ExecutionCredentialManager(environ={"OPENAI_API_KEY": "sk-fake-1234"})
    verifier = CredentialVerifier(manager=mgr)
    conn = ProviderConnectionManager(verifier=verifier)
    sessions = ExecutionSessionManager()
    audit = ExecutionAudit()
    checker = ExecutionComplianceChecker()

    # 1) verifikasi + koneksi
    assert verifier.can_execute("openai")
    assert conn.can_execute("openai")

    # 2) request approved (Article V)
    req = ExecutionRequest("int-1", "openai", "chat", mode="execute",
                           approved=True, approver="van")
    inv = checker.verify_governed(req)
    assert inv.can_proceed is True

    # 3) session
    session = sessions.create("openai", "int-1", source="integration_test")
    assert session.state == SessionState.CREATED

    # 4) serializer round-trip request
    restored = ExecutionRequestSerializer.from_dict(ExecutionRequestSerializer.to_dict(req))
    assert restored == req

    # 5) response (immutable) + serializer
    resp = ExecutionResponse("int-1", "openai", "chat", status="completed",
                             mode="execute", external_calls=1)
    resp_restored = ExecutionResponseSerializer.from_dict(
        ExecutionResponseSerializer.to_dict(resp))
    assert resp_restored.external_calls == 1

    # 6) audit seluruh jalur (timeline lengkap)
    timeline = (
        AuditTimelineStep("request", "ok"),
        AuditTimelineStep("validation", "ok"),
        AuditTimelineStep("approval", "ok", detail="approved"),
        AuditTimelineStep("provider", "ok", external_calls=1),
        AuditTimelineStep("response", "ok"),
    )
    audit.record("int-1", "openai", "chat", "execute", "completed", timeline,
                 approver="van", approval_id="ap-int-1")
    assert audit.verify("int-1") is True  # audit terverifikasi & immutable

    # 7) compliance penuh terhadap the path
    compliance = checker.check(
        subject="integration",
        source_blocks=["def run():\n    return 'ok'\n"],
        requests=[req],
    )
    assert compliance.passed is True


def test_integration_blocked_without_approval():
    """Approval wajib: execute tanpa approval -> compliance menolak, tidak
    ada jalur yang diteruskan (Article V).
    """
    from sam.execution_runtime.execution_compliance import ExecutionComplianceChecker
    checker = ExecutionComplianceChecker()
    req = ExecutionRequest("int-2", "openai", "chat", mode="execute", approved=False)
    inv = checker.verify_governed(req)
    assert inv.can_proceed is False
    assert "approval" in inv.reason
    result = checker.check(
        subject="integration-blocked", source_blocks=[], requests=[req])
    assert result.passed is False


def test_integration_credential_gate_blocks_provider():
    """Tanpa credential -> provider tidak bisa dijalankan (guarding)."""
    from sam.execution_runtime.credential_verifier import CredentialVerifier
    from sam.execution_runtime.provider_connection import ProviderConnectionManager
    mgr = ExecutionCredentialManager(environ={})
    verifier = CredentialVerifier(manager=mgr)
    conn = ProviderConnectionManager(verifier=verifier)
    assert verifier.can_execute("openai") is False
    assert conn.can_execute("openai") is False
    # provider non-auth tetap boleh
    assert conn.can_execute("filesystem") is True
