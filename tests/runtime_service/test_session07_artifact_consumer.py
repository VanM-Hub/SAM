"""Session 07 - Artifact Runtime Activation (AD-ENG-002 Pattern Standard).

Artifact menjadi capability operasional yang aktif melalui Activation Pattern
Standard: Conversation -> RuntimeService -> ExecutionRuntime(preview) ->
ArtifactPreviewConsumer -> ArtifactRegistry -> ConversationArtifactBridge -> STOP.

Tanpa ArtifactEngine/Generator/Runtime baru; tanpa integrasi Mission/Contract/
Dashboard/Intelligence; tanpa ubah ExecutionRuntime/RuntimeService.
"""
from __future__ import annotations
import inspect

import pytest

from sam.runtime_service.api import ArtifactPreviewConsumer, ArtifactPreview
from sam.artifact_runtime.foundation.artifact_registry import ArtifactRegistry
from sam.artifact_runtime.foundation.artifact_descriptor import ArtifactDescriptor


def _areg() -> ArtifactRegistry:
    reg = ArtifactRegistry()
    reg = reg.register(ArtifactDescriptor(name="build-report", category="report"))
    reg = reg.register(ArtifactDescriptor(name="audit-trail", category="audit"))
    return reg


@pytest.fixture
def consumer():
    return ArtifactPreviewConsumer(registry=_areg())


def test_artifact_list(consumer):
    names = consumer.list_artifacts()
    assert "build-report" in names and "audit-trail" in names


def test_artifact_resolve_found(consumer):
    ap = consumer.resolve_artifact("build-report")
    assert isinstance(ap, ArtifactPreview)
    assert ap.found is True
    assert ap.category == "report"
    assert ap.external_calls == 0


def test_artifact_resolve_unknown(consumer):
    ap = consumer.resolve_artifact("ghost")
    assert ap.found is False


def test_artifact_preview_no_generate(consumer):
    ap = consumer.resolve_artifact("build-report")
    assert ap.integration_ok is True
    assert ap.external_calls == 0
    assert "executed" not in ap.as_dict()
    assert "generated" not in ap.as_dict()


def test_artifact_uses_existing_bridge():
    from sam.runtime_service.api import artifact_preview as ap
    src = inspect.getsource(ap)
    assert "ConversationArtifactBridge" in src
    assert "ConversationIntegrationBridge" in src


def test_artifact_no_mis_dash_intel():
    from sam.runtime_service.api import artifact_preview as mod
    src = inspect.getsource(mod)
    import_lines = [l for l in src.splitlines()
                    if l.strip().startswith(("import", "from"))]
    joined = " ".join(import_lines).lower()
    for banned in ("mission", "contract", "dashboard", "intelligence", "agent"):
        assert banned not in joined, f"artifact terhubung ke {banned}"


def test_artifact_no_new_engine():
    from sam.runtime_service.api import artifact_preview as ap
    src = inspect.getsource(ap)
    import_lines = [l for l in src.splitlines()
                    if l.strip().startswith(("import", "from"))]
    joined = " ".join(import_lines)
    for banned in ("ArtifactEngine", "Generator", "artifact_runtime.runtime"):
        assert banned not in joined


def test_prefix_with_artifact_via_conversation_path():
    """Conversation -> RuntimeService -> ExecutionRuntime -> Artifact (AD-ENG-002)."""
    from sam.runtime_service.api import (
        RuntimeAPI,
        ConversationPreviewGateway,
        ConversationExecutionContext,
        wire_conversation_preview,
        PreviewRequestView,
    )
    from sam.execution_runtime.execution_engine import ExecutionEngine
    from sam.execution_runtime.execution_request import ExecutionRequest

    api = RuntimeAPI()
    engine = ExecutionEngine()

    def build(view: PreviewRequestView):
        return ExecutionRequest(
            execution_id=view.execution_id, provider_id=view.provider_id,
            operation=view.operation, mode="preview",
            payload={"conversation": {"conversation_id": "c", "request": "x"}},
        )

    wire_conversation_preview(api, build_request=build, execute=engine.execute)
    gw = ConversationPreviewGateway(api)
    ac = ArtifactPreviewConsumer(registry=_areg())
    ctx = ConversationExecutionContext(conversation_id="s7", request="buat laporan")
    r = gw.preview_with_artifact(ctx, ac, "build-report", "exec-7")
    assert r["execution"]["executed"] is False
    assert r["execution"]["external_calls"] == 0
    assert r["artifact"]["found"] is True
    assert r["artifact"]["category"] == "report"
    assert r["artifact"]["external_calls"] == 0
