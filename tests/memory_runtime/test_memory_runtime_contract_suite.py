"""Memory Runtime — Contract Integrity Suite (Evidence, WP-B1).

Program B / EA-004 — suite DEDICATED contract Memory Runtime.
Memverifikasi integritas kontrak lintas-lapisan Memory (foundation, model,
builder, runtime) dari registry yang sama — konsistensi data lintas-lapisan.

Read-only, deterministik.
"""
from sam.memory.foundation.memory_descriptor import MemoryDescriptor
from sam.memory.foundation.memory_capability import MemoryCapability
from sam.memory.foundation.memory_contract import MemoryContract
from sam.memory.foundation.memory_registry import MemoryRegistry
from sam.memory.runtime.memory_runtime import MemoryRuntime
from sam.memory.runtime.memory_summary import MemorySummarizer
from sam.memory.builder.memory_builder import MemoryBuilder
from sam.memory.model.memory_record import MemoryRecord
from sam.memory.model.memory_scope import MemoryScope
from sam.memory.model.memory_reference import MemoryReference


def _registry():
    r = MemoryRegistry()
    r.register(MemoryDescriptor(
        "mem1", "Contract Memory", version="3.0.0", category="session",
    ))
    r.attach_capability(MemoryCapability(
        "c1", "mem1", name="organize", operations=["organize"],
    ))
    r.attach_contract(MemoryContract(
        "ct1", "mem1", "memory-contract", guarantees=["no-inference"],
    ))
    return r


class TestContractIntegrityAcrossLayers:
    """Registry yang sama dikonsumsi konsisten oleh semua lapisan."""

    def test_id_consistency_all_layers(self):
        r = _registry()
        assert r.exists("mem1")
        assert r.list_ids() == ["mem1"]
        assert r.find("mem1").version == "3.0.0"
        assert MemoryRuntime(r).run("mem1").ok is True
        assert MemorySummarizer(r).summary().total_memories == 1

    def test_capability_bound_to_descriptor(self):
        r = _registry()
        caps = r.get_capabilities("mem1")
        assert caps[0].memory_id == "mem1"
        assert caps[0].supports("organize") is True
        assert caps[0].supports("infer") is False
        # preview-only default, tanpa promotion
        assert caps[0].preview_only is True

    def test_contract_guarantee_preserved(self):
        r = _registry()
        assert "no-inference" in r.get_contract("mem1").guarantees

    def test_builder_contract_roundtrip(self):
        r = _registry()
        d = r.find("mem1")
        built = MemoryBuilder().build(d.id, name=d.name)
        assert built.valid is True
        assert built.descriptor.id == "mem1"
        assert built.descriptor.name == "Contract Memory"
        assert built.record.memory_id == "mem1"
        assert built.record.is_valid()


class TestModelContract:
    """Model layer — konstruksi record/scope/reference."""

    def test_record(self):
        rec = MemoryRecord(record_id="rec.1", memory_id="mem1", scope="session")
        assert rec.memory_id == "mem1"
        assert rec.scope == "session"
        assert rec.is_valid() is True
        # preview-only default, tanpa promotion
        assert rec.preview_only is True

    def test_scope(self):
        scope = MemoryScope(scope_id="session", name="Session")
        assert scope.scope_id == "session"
        assert scope.allows("anything") is True  # tanpa daftar tag, semua diizinkan

    def test_scope_allows_filtered(self):
        scope = MemoryScope(scope_id="session", name="Session", allowed_tags=["x"])
        assert scope.allows("x") is True
        assert scope.allows("y") is False

    def test_reference(self):
        ref = MemoryReference("ref1", source_id="mem1", target_id="mem2")
        assert ref.source_id == "mem1"
        assert ref.target_id == "mem2"
        assert ref.is_valid() is True
