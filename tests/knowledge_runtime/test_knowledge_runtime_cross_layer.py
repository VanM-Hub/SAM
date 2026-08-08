"""Knowledge Runtime — Cross-Layer Orchestration Suite (Dedicated).

WP-04 EA-004 / Program B — suite test DEDICATED untuk Knowledge Runtime.
Melengkapi gap EA-002-007: Knowledge diuji tersebar (sprint180-187), kini ada
folder test dedicated `tests/knowledge_runtime/`.

Fokus: orchestration lintas-lapisan (registry -> builder -> runtime pipeline ->
summary -> version/history). Read-only, deterministik, tanpa inference.
"""
import pytest

from sam.knowledge_runtime.foundation.knowledge_descriptor import KnowledgeDescriptor
from sam.knowledge_runtime.foundation.knowledge_capability import KnowledgeCapability
from sam.knowledge_runtime.foundation.knowledge_contract import KnowledgeContract
from sam.knowledge_runtime.foundation.knowledge_metadata import KnowledgeMetadata
from sam.knowledge_runtime.foundation.knowledge_registry import KnowledgeRegistry
from sam.knowledge_runtime.runtime.knowledge_runtime import KnowledgeRuntime
from sam.knowledge_runtime.runtime.knowledge_summary import KnowledgeSummarizer
from sam.knowledge_runtime.catalog.knowledge_version import KnowledgeVersionProvider
from sam.knowledge_runtime.catalog.knowledge_history import KnowledgeHistory, KnowledgeHistoryEntry
from sam.knowledge_runtime.builder.knowledge_builder import KnowledgeBuilder


def _built_registry():
    """Registry dengan 2 knowledge padat (cross-category)."""
    r = KnowledgeRegistry()
    r.register(KnowledgeDescriptor(
        "kn_domain", "Domain Knowledge", version="2.1.0", category="domain",
        description="domain knowledge", author="SAM", tags=["domain"],
    ))
    r.attach_capability(KnowledgeCapability(
        "cap_a", "kn_domain", "organize", operations=["fact", "relation"],
    ))
    r.attach_capability(KnowledgeCapability(
        "cap_b", "kn_domain", "retrieve", operations=["fact"],
    ))
    r.attach_contract(KnowledgeContract(
        "ct_a", "kn_domain", "knowledge-contract", guarantees=["no-inference"],
    ))
    r.attach_metadata(KnowledgeMetadata("kn_domain", author="SAM", readonly=True))

    r.register(KnowledgeDescriptor(
        "kn_general", "General Knowledge", version="1.0.0", category="general",
    ))
    return r


class TestCrossLayerOrchestration:
    """Urutan pipeline nyata: registry -> runtime -> summary -> version/history."""

    def test_registry_to_runtime_pipeline(self):
        r = _built_registry()
        rt = KnowledgeRuntime(r)
        res = rt.run("kn_domain")
        assert res.ok is True
        assert res.steps == 1
        # preview-only, tanpa inference / external call
        assert res.external_calls == 0
        assert "no inference" in res.detail

    def test_runtime_missing_knowledge(self):
        rt = KnowledgeRuntime(KnowledgeRegistry())
        res = rt.run("ghost")
        assert res.ok is False
        assert res.detail == "knowledge not registered"

    def test_builder_produces_valid(self):
        r = _built_registry()
        d = r.find("kn_domain")
        built = KnowledgeBuilder().build(d.id, name=d.name)
        assert built.valid is True

    def test_summary_aggregates_both(self):
        r = _built_registry()
        s = KnowledgeSummarizer(r).summary()
        assert s.total_knowledge == 2
        assert s.by_category["domain"] == 1
        assert s.by_category["general"] == 1
        assert s.external_calls == 0

    def test_conversation_runtime_bridge_summary(self):
        """Bridge conversation harus memakai runtime + summarizer konsisten."""
        from sam.knowledge_runtime.runtime.conversation_runtime import ConversationRuntimeBridge
        r = _built_registry()
        rt = KnowledgeRuntime(r)
        b = ConversationRuntimeBridge(rt)
        s = b.summary()
        assert s["total"] == 2
        assert s["external_calls"] == 0

    def test_conversation_runtime_bridge_run(self):
        from sam.knowledge_runtime.runtime.conversation_runtime import ConversationRuntimeBridge
        r = _built_registry()
        b = ConversationRuntimeBridge(KnowledgeRuntime(r))
        st = b.run_status("kn_domain")
        assert st["ok"] is True
        assert st["external_calls"] == 0


class TestVersionAndHistory:
    """Cakupan version & history (Sprint 184) — bagian lane cross-layer."""

    def test_version_of_present(self):
        r = _built_registry()
        p = KnowledgeVersionProvider(r)
        assert p.version_of("kn_domain") == "2.1.0"

    def test_version_of_missing_empty(self):
        p = KnowledgeVersionProvider(KnowledgeRegistry())
        assert p.version_of("ghost") == ""

    def test_version_info_stable(self):
        r = _built_registry()
        info = KnowledgeVersionProvider(r).info("kn_domain")
        assert info.version == "2.1.0"
        assert info.stable is True

    def test_version_info_missing_unstable(self):
        info = KnowledgeVersionProvider(KnowledgeRegistry()).info("ghost")
        assert info.version == ""
        assert info.stable is False

    def test_history_record_and_filter(self):
        h = KnowledgeHistory()
        assert h.count() == 0
        h.record(KnowledgeHistoryEntry("kn_domain", "register"))
        h.record(KnowledgeHistoryEntry("kn_domain", "query"))
        h.record(KnowledgeHistoryEntry("kn_general", "register"))
        assert h.count() == 3
        assert len(h.entries("kn_domain")) == 2
        assert len(h.entries()) == 3
        # immutable entry
        assert h.entries("kn_domain")[0].external_calls == 0

    def test_history_all_entries_readonly_external(self):
        h = KnowledgeHistory()
        for kid in ["a", "b"]:
            h.record(KnowledgeHistoryEntry(kid, "register", external_calls=0))
        assert all(e.external_calls == 0 for e in h.entries())
