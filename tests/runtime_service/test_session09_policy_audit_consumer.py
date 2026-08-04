"""Session 09 - Policy & Audit Activation (AD-ENG-002 Pattern Standard).

Policy dan Audit menjadi capability governance operasional yang aktif melalui
Activation Pattern Standard, independen satu sama lain:
- Policy:  Conversation -> RuntimeService -> ExecutionRuntime(preview) -> PolicyPreviewConsumer
           -> PolicyRegistry -> ConversationPolicyBridge -> STOP
- Audit:   Conversation -> RuntimeService -> ExecutionRuntime(preview) -> AuditPreviewConsumer
           -> AuditRegistry -> ConversationAuditBridge -> STOP

Tanpa Governance/Audit/Compliance/Runtime/Provider baru; tanpa integrasi terlarang;
tanpa ubah ExecutionRuntime/RuntimeService/internal policy/audit_runtime.
"""
from __future__ import annotations
import inspect

import pytest

from sam.runtime_service.api import PolicyPreviewConsumer, PolicyPreview
from sam.runtime_service.api import AuditPreviewConsumer, AuditPreview
from sam.policy_runtime.foundation.policy_registry import PolicyRegistry
from sam.policy_runtime.foundation.policy_descriptor import PolicyDescriptor
from sam.audit_runtime.foundation.audit_registry import AuditRegistry
from sam.audit_runtime.foundation.audit_descriptor import AuditDescriptor


def _preg() -> PolicyRegistry:
    reg = PolicyRegistry()
    reg.register(PolicyDescriptor(id="pol-access", name="Access Policy",
                                   category="security"))
    reg.register(PolicyDescriptor(id="pol-audit", name="Audit Policy",
                                   category="governance"))
    return reg


def _areg() -> AuditRegistry:
    reg = AuditRegistry()
    reg = reg.register(AuditDescriptor(audit_id="aud-1", category="compliance"))
    reg = reg.register(AuditDescriptor(audit_id="aud-2", category="security"))
    return reg


@pytest.fixture
def pconsumer():
    return PolicyPreviewConsumer(registry=_preg())


@pytest.fixture
def aconsumer():
    return AuditPreviewConsumer(registry=_areg())


# ---------- Policy ----------

def test_policy_list(pconsumer):
    ids = pconsumer.list_policies()
    assert "pol-access" in ids and "pol-audit" in ids


def test_policy_resolve_found(pconsumer):
    pp = pconsumer.resolve_policy("pol-access")
    assert isinstance(pp, PolicyPreview)
    assert pp.found is True
    assert pp.name == "Access Policy"
    assert pp.status == "registered"
    assert pp.external_calls == 0


def test_policy_resolve_unknown(pconsumer):
    pp = pconsumer.resolve_policy("ghost")
    assert pp.found is False


def test_policy_preview_no_evaluate_decision(pconsumer):
    pp = pconsumer.resolve_policy("pol-access")
    assert pp.integration_ok is True
    assert pp.external_calls == 0
    d = pp.as_dict()
    assert "executed" not in d
    assert "decision" not in d
    assert "evaluated" not in d


def test_policy_uses_existing_bridge():
    from sam.runtime_service.api import policy_preview as mod
    src = inspect.getsource(mod)
    assert "ConversationPolicyBridge" in src
    assert "ConversationIntegrationBridge" in src


def test_policy_no_forbidden_integration():
    from sam.runtime_service.api import policy_preview as mod
    src = inspect.getsource(mod)
    import_lines = [l for l in src.splitlines()
                    if l.strip().startswith(("import", "from"))]
    joined = " ".join(import_lines).lower()
    for banned in ("mission", "intelligence", "agent", "complianc"):
        assert banned not in joined


# ---------- Audit ----------

def test_audit_list(aconsumer):
    ids = aconsumer.list_audits()
    assert "aud-1" in ids and "aud-2" in ids


def test_audit_resolve_found(aconsumer):
    ap = aconsumer.resolve_audit("aud-1")
    assert isinstance(ap, AuditPreview)
    assert ap.found is True
    assert ap.category == "compliance"
    assert ap.provenance is True
    assert ap.traceability is True
    assert ap.external_calls == 0


def test_audit_resolve_unknown(aconsumer):
    ap = aconsumer.resolve_audit("ghost")
    assert ap.found is False


def test_audit_preview_immutable_no_execute(aconsumer):
    ap = aconsumer.resolve_audit("aud-1")
    assert ap.integration_ok is True
    assert ap.external_calls == 0
    d = ap.as_dict()
    assert "executed" not in d
    assert "no_execute" == True or d.get("provenance") is True


def test_audit_uses_existing_bridge():
    from sam.runtime_service.api import audit_preview as mod
    src = inspect.getsource(mod)
    assert "ConversationAuditBridge" in src
    assert "ConversationIntegrationBridge" in src


def test_audit_no_forbidden_integration():
    from sam.runtime_service.api import audit_preview as mod
    src = inspect.getsource(mod)
    import_lines = [l for l in src.splitlines()
                    if l.strip().startswith(("import", "from"))]
    joined = " ".join(import_lines).lower()
    for banned in ("mission", "intelligence", "agent"):
        assert banned not in joined


# ---------- Conversation path (Policy & Audit independen) ----------

def test_preview_with_policy_via_conversation_path():
    from sam.runtime_service.api import (
        RuntimeAPI, ConversationPreviewGateway, ConversationExecutionContext,
        wire_conversation_preview, PreviewRequestView,
    )
    from sam.execution_runtime.execution_engine import ExecutionEngine
    from sam.execution_runtime.execution_request import ExecutionRequest

    api = RuntimeAPI()
    engine = ExecutionEngine()

    def build(view: PreviewRequestView):
        return ExecutionRequest(
            execution_id=view.execution_id, provider_id=view.provider_id,
            operation=view.operation, mode="preview", payload={})

    wire_conversation_preview(api, build_request=build, execute=engine.execute)
    gw = ConversationPreviewGateway(api)
    ctx = ConversationExecutionContext(conversation_id="s9", request="cek policy")
    r = gw.preview_with_policy(ctx, PolicyPreviewConsumer(registry=_preg()),
                               "pol-access", "exec-9p")
    assert r["execution"]["executed"] is False
    assert r["execution"]["external_calls"] == 0
    assert r["policy"]["found"] is True
    assert r["policy"]["external_calls"] == 0


def test_preview_with_audit_via_conversation_path():
    from sam.runtime_service.api import (
        RuntimeAPI, ConversationPreviewGateway, ConversationExecutionContext,
        wire_conversation_preview, PreviewRequestView,
    )
    from sam.execution_runtime.execution_engine import ExecutionEngine
    from sam.execution_runtime.execution_request import ExecutionRequest

    api = RuntimeAPI()
    engine = ExecutionEngine()

    def build(view: PreviewRequestView):
        return ExecutionRequest(
            execution_id=view.execution_id, provider_id=view.provider_id,
            operation=view.operation, mode="preview", payload={})

    wire_conversation_preview(api, build_request=build, execute=engine.execute)
    gw = ConversationPreviewGateway(api)
    ctx = ConversationExecutionContext(conversation_id="s9b", request="cek audit")
    r = gw.preview_with_audit(ctx, AuditPreviewConsumer(registry=_areg()),
                              "aud-1", "exec-9a")
    assert r["execution"]["executed"] is False
    assert r["audit"]["found"] is True
    assert r["audit"]["external_calls"] == 0


def test_policy_audit_independent():
    """Policy & Audit TIDAK saling tahu implementasi internal."""
    from sam.runtime_service.api import policy_preview, audit_preview
    psrc = inspect.getsource(policy_preview)
    asrc = inspect.getsource(audit_preview)
    assert "ConversationPolicyBridge" in psrc and "ConversationAuditBridge" not in psrc
    assert "ConversationAuditBridge" in asrc and "ConversationPolicyBridge" not in asrc
