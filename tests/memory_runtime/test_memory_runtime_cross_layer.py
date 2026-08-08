"""Memory Runtime — Cross-Layer Orchestration Suite (Evidence, WP-B1).

Program B / EA-004 — suite test DEDICATED Memory Runtime.
Melengkapi gap EA-002-007 (P3): Memory diuji tersebar (sprint172-179 +
runtime_service/test_session08). Folder dedicated `tests/memory_runtime/`
mendefinisikan perilaku OPERATIONAL yang diharapkan.

Fokus: orchestration lintas-lapisan (registry -> builder -> runtime pipeline ->
summary -> version/history) lewat API publik & kontrak yang ada.
Read-only, deterministik, preview-only (tanpa storage/retrieval/inference).
"""
import pytest

from sam.memory.foundation.memory_descriptor import MemoryDescriptor
from sam.memory.foundation.memory_capability import MemoryCapability
from sam.memory.foundation.memory_contract import MemoryContract
from sam.memory.foundation.memory_metadata import MemoryMetadata
from sam.memory.foundation.memory_registry import MemoryRegistry
from sam.memory.runtime.memory_runtime import MemoryRuntime
from sam.memory.runtime.memory_summary import MemorySummarizer
from sam.memory.catalog.memory_version import MemoryVersionProvider
from sam.memory.catalog.memory_history import MemoryHistory, MemoryHistoryEntry
from sam.memory.builder.memory_builder import MemoryBuilder


def _built_registry():
    r = MemoryRegistry()
    r.register(MemoryDescriptor(
        "mem_session", "Session Memory", version="2.0.0", category="session",
        scopes=["session", "conversation"],
    ))
    r.attach_capability(MemoryCapability(
        "cap_a", "mem_session", name="organize", operations=["record", "reference"],
    ))
    r.attach_capability(MemoryCapability(
        "cap_b", "mem_session", name="retrieve", operations=["record"],
    ))
    r.attach_contract(MemoryContract(
        "ct_a", "mem_session", "memory-contract", guarantees=["no-inference"],
    ))
    r.attach_metadata(MemoryMetadata("mem_session", author="SAM", readonly=True))

    r.register(MemoryDescriptor(
        "mem_mission", "Mission Memory", version="1.0.0", category="mission",
    ))
    return r


class TestCrossLayerOrchestration:
    """Urutan pipeline nyata: registry -> runtime -> summary -> version/history."""

    def test_registry_to_runtime_pipeline(self):
        r = _built_registry()
        rt = MemoryRuntime(r)
        res = rt.run("mem_session")
        assert res.ok is True
        assert res.steps == 1
        # preview-only, tanpa external call
        assert res.external_calls == 0
        assert "preview" in res.detail

    def test_runtime_missing_memory(self):
        rt = MemoryRuntime(MemoryRegistry())
        res = rt.run("ghost")
        assert res.ok is False
        assert res.detail == "memory not registered"

    def test_builder_produces_valid(self):
        r = _built_registry()
        d = r.find("mem_session")
        built = MemoryBuilder().build(d.id, name=d.name)
        assert built.valid is True

    def test_summary_aggregates_both(self):
        r = _built_registry()
        s = MemorySummarizer(r).summary()
        assert s.total_memories == 2
        assert s.by_category["session"] == 1
        assert s.by_category["mission"] == 1
        assert s.external_calls == 0

    def test_conversation_memory_bridge_summary_queries(self):
        from sam.memory.foundation.conversation_memory import ConversationMemoryBridge
        r = _built_registry()
        b = ConversationMemoryBridge(r)
        assert b.query_1_summary()["total"] == 2
        assert "mem_session" in b.query_2_list()
        assert b.query_3_descriptor("mem_session") == "Session Memory"
        assert b.query_4_metadata("mem_session")["author"] == "SAM"
        assert b.query_5_capability("mem_session") == ["cap_a", "cap_b"]


class TestVersionAndHistory:
    """Cakupan version & history Memory (Sprint 176) — lane cross-layer."""

    def test_version_of_present(self):
        r = _built_registry()
        assert MemoryVersionProvider(r).version_of("mem_session") == "2.0.0"

    def test_version_of_missing_empty(self):
        assert MemoryVersionProvider(MemoryRegistry()).version_of("ghost") == ""

    def test_version_info_stable(self):
        info = MemoryVersionProvider(_built_registry()).info("mem_session")
        assert info.version == "2.0.0"
        assert info.stable is True

    def test_version_info_missing_unstable(self):
        info = MemoryVersionProvider(MemoryRegistry()).info("ghost")
        assert info.version == ""
        assert info.stable is False

    def test_history_record_and_filter(self):
        h = MemoryHistory()
        assert h.count() == 0
        h.record(MemoryHistoryEntry("mem_session", "record"))
        h.record(MemoryHistoryEntry("mem_session", "query"))
        h.record(MemoryHistoryEntry("mem_mission", "record"))
        assert h.count() == 3
        assert len(h.entries("mem_session")) == 2
        assert len(h.entries()) == 3
        # immutable entry, preview-only external
        assert h.entries("mem_session")[0].external_calls == 0
