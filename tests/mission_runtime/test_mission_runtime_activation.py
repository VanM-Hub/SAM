# Copyright 2026 VanM-Hub. Licensed under Apache-2.0.
"""Mission Runtime — Deterministic Activation evidence suite (WP-B2, Program B).

Merealisasikan & membuktikan activation path Mission via jalur resmi
(AD-ENG-002 Activation Pattern Standard), paralel dengan Policy/Workflow/
Memory/Knowledge/Artifact/Audit:

  Conversation -> RuntimeService -> ExecutionRuntime(preview)
  -> MissionPreviewConsumer -> MissionRegistry -> ConversationMissionBridge -> STOP

Fase yang dibuktikan:
  B2-01  Deterministic Activation (activation entry/registration/validation)
  B2-02  Mission Lifecycle Publication (descriptor + metadata + lifecycle)
  B2-03  Mission Governance Publication (governance state + context + readiness)
  B2-04  Workflow Runtime Consumer path (tanpa coupling baru)
  B2-05  Policy Runtime Consumer path
  B2-06  Registry Publication (metadata ke Registry Runtime)
  B2-07  Presentation Integration (Presentation memperoleh Mission State)
  Phase 3  Boundary Verification (forbidden imports, dependency, runtime graph)
  Phase 4  Compliance Suite

Pure test — hanya membuktikan jalur melalui public API yang SUDAH ADA.
"""
from __future__ import annotations

import inspect

import pytest

from sam.runtime_service.api.mission_preview import (
    MissionPreviewConsumer,
    MissionPreview,
    build_mission_preview_consumer,
)
from sam.mission_runtime import (
    MissionRegistry,
    MissionDescriptor,
    ConversationMissionBridge,
)


def _mreg() -> MissionRegistry:
    reg = MissionRegistry()
    reg.register(MissionDescriptor(mission_id="m-1", name="Mission One",
                                   category="campaign"))
    reg.register(MissionDescriptor(mission_id="m-2", name="Mission Two",
                                   category="campaign",
                                   description="second mission",
                                   tags=("alpha", "beta")))
    return reg


@pytest.fixture
def mconsumer() -> MissionPreviewConsumer:
    return MissionPreviewConsumer(registry=_mreg())


# =====================================================================
# B2-01 — Deterministic Activation
# =====================================================================

class TestB201DeterministicActivation:
    def test_activation_entry_present(self):
        # activation entry: factory + consumer importable (registration point)
        assert callable(build_mission_preview_consumer)
        c = build_mission_preview_consumer()
        assert isinstance(c, MissionPreviewConsumer)

    def test_activation_registration_via_registry(self, mconsumer):
        # registration: mission terdaftar di registry & terlihat consumer
        ids = mconsumer.list_missions()
        assert "m-1" in ids and "m-2" in ids
        assert mconsumer.registry.count() == 2

    def test_deterministic_activation_resolve(self, mconsumer):
        # validation: resolve mission deterministik
        p = mconsumer.resolve_mission("m-1")
        assert p.found is True
        assert p.name == "Mission One"
        p2 = mconsumer.resolve_mission("ghost")
        assert p2.found is False

    def test_activation_no_runtime_model_change(self):
        # guardrail: tidak membuat runtime baru; pakai MissionRegistry existing
        from sam.runtime_service.api import mission_preview as mod
        src = inspect.getsource(mod)
        assert "MissionRegistry" in src
        assert "ConversationMissionBridge" in src

    def test_activation_empty_registry_default(self):
        c = build_mission_preview_consumer()
        assert c.list_missions() == []
        assert c.resolve_mission("ghost").found is False


# =====================================================================
# B2-02 — Mission Lifecycle Publication
# =====================================================================

class TestB202LifecyclePublication:
    def test_lifecycle_descriptor_publication(self, mconsumer):
        p = mconsumer.resolve_mission("m-2")
        assert p.found is True
        assert p.mission_id == "m-2"
        assert p.category == "campaign"

    def test_metadata_publication(self, mconsumer):
        p = mconsumer.resolve_mission("m-2")
        assert p.description == "second mission"
        assert tuple(p.tags) == ("alpha", "beta")

    def test_lifecycle_status_published(self, mconsumer):
        # setiap mission yang ter-publish = status 'published' (read-only)
        for mid in mconsumer.list_missions():
            p = mconsumer.resolve_mission(mid)
            assert p.status == "published"
            assert p.found is True

    def test_publication_immutable_no_execute(self, mconsumer):
        p = mconsumer.resolve_mission("m-1")
        assert p.external_calls == 0
        d = p.as_dict()
        assert "executed" not in d
        assert "execution_id" not in d


# =====================================================================
# B2-03 — Mission Governance Publication
# =====================================================================

class TestB203GovernancePublication:
    def test_governance_summary(self, mconsumer):
        s = mconsumer.summary()
        assert isinstance(s, dict)
        assert s.get("missions", 0) == 2

    def test_governance_context_via_bridge(self):
        reg = _mreg()
        bridge = ConversationMissionBridge(reg)
        assert bridge.count() == 2
        assert "Mission One" in bridge.list_names()

    def test_readiness_exposed(self, mconsumer):
        # readiness: semua mission dapat di-resolve (integration_ok=True)
        for mid in mconsumer.list_missions():
            p = mconsumer.resolve_mission(mid)
            assert p.integration_ok is True


# =====================================================================
# B2-04 — Workflow Runtime Consumer path (tanpa coupling baru)
# =====================================================================

class TestB204WorkflowConsumer:
    def test_workflow_preview_consumer_still_works(self):
        from sam.runtime_service.api.workflow_preview import WorkflowPreviewConsumer
        from sam.workflow_runtime.foundation.workflow_registry import WorkflowRegistry
        from sam.workflow_runtime.foundation.workflow_descriptor import WorkflowDescriptor
        reg = WorkflowRegistry()
        reg.register(WorkflowDescriptor(id="wf-1", name="WF1"))
        c = WorkflowPreviewConsumer(registry=reg)
        p = c.resolve_workflow("wf-1")
        assert p.found is True
        assert p.name == "WF1"

    def test_mission_consumer_no_coupling_to_workflow(self, mconsumer):
        # Mission consumer TIDAK menambah coupling: tidak import workflow_runtime
        from sam.runtime_service.api import mission_preview as mod
        joined = " ".join(inspect.getsource(mod).splitlines()).lower()
        assert "workflow_runtime" not in joined


# =====================================================================
# B2-05 — Policy Runtime Consumer path
# =====================================================================

class TestB205PolicyConsumer:
    def test_policy_preview_consumer_still_works(self):
        from sam.runtime_service.api.policy_preview import PolicyPreviewConsumer
        from sam.policy_runtime.foundation.policy_registry import PolicyRegistry
        from sam.policy_runtime.foundation.policy_descriptor import PolicyDescriptor
        reg = PolicyRegistry()
        reg.register(PolicyDescriptor(id="pol-1", name="P1"))
        c = PolicyPreviewConsumer(registry=reg)
        assert c.resolve_policy("pol-1").found is True


# =====================================================================
# B2-06 — Registry Publication (metadata ke Registry Runtime)
# =====================================================================

class TestB206RegistryPublication:
    def test_mission_registry_publication(self, mconsumer):
        # Mission metadata dipublikasikan lewat MissionRegistry -> consumer
        assert mconsumer.registry.count() == 2
        assert "m-1" in mconsumer.registry.ids()

    def test_bridge_summary_matches_registry(self, mconsumer):
        assert mconsumer.summary().get("missions", 0) == mconsumer.registry.count()


# =====================================================================
# B2-07 — Presentation Integration
# =====================================================================

class TestB207PresentationIntegration:
    def test_runtime_service_import_mission_consumer(self):
        # RuntimeService jalur wiring kini memuat MissionPreviewConsumer
        from sam.runtime_service.api import conversation_preview_wiring as w
        src = inspect.getsource(w)
        assert "MissionPreviewConsumer" in src

    def test_preview_gateway_has_mission_method(self):
        from sam.runtime_service.api import conversation_preview_wiring as w
        src = inspect.getsource(w)
        assert "preview_with_mission" in src

    def test_presentation_manifest_covers_mission(self):
        # Presentation mengakui mission_runtime dalam manifest integrasi
        from sam.presentation.integration import presentation_integ_manifest as m
        names = getattr(m, "INTEGRATED_RUNTIMES", None)
        if names is None:
            names = [n for n in dir(m) if "MISSION" in n.upper() or "RUNTIME" in n.upper()]
        # mission_runtime telah tercatat (dalam salah satu bentuk manifest)
        src = inspect.getsource(m)
        assert "mission_runtime" in src


# =====================================================================
# Phase 3 — Boundary Verification
# =====================================================================

class TestPhase3Boundary:
    def test_mission_consumer_no_forbidden_imports(self):
        # Mission PREVIEW tidak import Provider/Connector/Execution/Workflow
        from sam.runtime_service.api import mission_preview as mod
        src = inspect.getsource(mod)
        import_lines = [l for l in src.splitlines()
                        if l.strip().startswith(("import", "from"))]
        joined = " ".join(import_lines).lower()
        for banned in ("provider", "connector", "execution", "workflow",
                       "policy", "intelligence", "agent"):
            assert banned not in joined

    def test_mission_preview_uses_only_existing_bridge(self):
        from sam.runtime_service.api import mission_preview as mod
        src = inspect.getsource(mod)
        assert "MissionRegistry" in src
        assert "ConversationMissionBridge" in src
        # tidak menambah bridge/runtime baru
        assert "import " not in " ".join(
            [l for l in src.splitlines() if "mission_runtime" in l and "from sam." in l]).replace(
            "from sam.mission_runtime import MissionRegistry", "").replace(
            "from sam.mission_runtime import ConversationMissionBridge", "").replace(
            "from sam.mission_runtime import MissionDescriptor", "")

    def test_runtime_graph_mission_leaves_runtime_service(self):
        # Mission tetap berada di layer consumer: mission_preview hanya bungkus
        # MissionRegistry + ConversationMissionBridge; tidak memanggil execution.
        from sam.runtime_service.api import mission_preview as mod
        src = inspect.getsource(mod)
        assert "resolve_mission" in src
        assert "ExecutionEngine" not in src
        assert "PreviewGateway" not in src


# =====================================================================
# Phase 4 — Compliance Suite
# =====================================================================

class TestPhase4Compliance:
    def test_ownership_validation(self, mconsumer):
        # ownership: setiap mission punya identitas unik
        ids = mconsumer.list_missions()
        assert len(ids) == len(set(ids))

    def test_activation_validation_readonly(self, mconsumer):
        # activation: resolve tidak mengubah registry (read-only)
        before = mconsumer.registry.count()
        _ = mconsumer.resolve_mission("m-1")
        _ = mconsumer.resolve_mission("ghost")
        assert mconsumer.registry.count() == before

    def test_dependency_validation_no_new_runtime(self):
        # dependency: hanya MissionRegistry + ConversationMissionBridge
        from sam.runtime_service.api import mission_preview as mod
        src = inspect.getsource(mod)
        assert "MissionRegistry" in src and "ConversationMissionBridge" in src

    def test_lifecycle_validation_immutable_dto(self, mconsumer):
        # lifecycle: MissionPreview frozen (immutable daftar publikasi)
        import dataclasses
        assert dataclasses.is_dataclass(MissionPreview)
        assert MissionPreview.__dataclass_params__.frozen is True

    def test_publication_validation_as_dict(self, mconsumer):
        p = mconsumer.resolve_mission("m-2")
        d = p.as_dict()
        assert set(d.keys()) == {
            "mission_id", "found", "name", "category", "description",
            "tags", "status", "integration_ok", "external_calls",
        }

    def test_governance_validation_no_execute(self, mconsumer):
        s = mconsumer.summary()
        assert isinstance(s, dict)
        assert "executed" not in s
