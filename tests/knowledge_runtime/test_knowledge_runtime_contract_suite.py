"""Knowledge Runtime — Contract Integrity Suite (Dedicated).

WP-04 EA-004 / Program B — suite DEDICATED contract Knowledge Runtime.
Memverifikasi integritas kontrak lintas-lapisan arsitektur Knowledge Runtime
(foundation, model, builder, runtime, catalog, monitor, certification,
integration) dengan registry yang sama — konsistensi data lintas lapisan.

Read-only, deterministik.
"""
from sam.knowledge_runtime.foundation.knowledge_descriptor import KnowledgeDescriptor
from sam.knowledge_runtime.foundation.knowledge_capability import KnowledgeCapability
from sam.knowledge_runtime.foundation.knowledge_contract import KnowledgeContract
from sam.knowledge_runtime.foundation.knowledge_registry import KnowledgeRegistry
from sam.knowledge_runtime.runtime.knowledge_runtime import KnowledgeRuntime
from sam.knowledge_runtime.runtime.knowledge_summary import KnowledgeSummarizer
from sam.knowledge_runtime.builder.knowledge_builder import KnowledgeBuilder
from sam.knowledge_runtime.model.knowledge_fact import KnowledgeFactPreview
from sam.knowledge_runtime.model.knowledge_record import KnowledgeRecord
from sam.knowledge_runtime.model.knowledge_relation import KnowledgeRelationPreview


def _registry():
    r = KnowledgeRegistry()
    r.register(KnowledgeDescriptor(
        "kn1", "Contract Knowledge", version="3.0.0", category="domain",
    ))
    r.attach_capability(KnowledgeCapability(
        "c1", "kn1", name="organize", operations=["organize"],
    ))
    r.attach_contract(KnowledgeContract(
        "ct1", "kn1", "knowledge-contract", guarantees=["no-inference"],
    ))
    return r


class TestContractIntegrityAcrossLayers:
    """Registry yang sama dikonsumsi konsisten oleh semua lapisan."""

    def test_id_consistency_all_layers(self):
        """Semua lapisan melihat knowledge yang sama dari registry yang sama."""
        r = _registry()
        assert r.exists("kn1")
        assert r.list_ids() == ["kn1"]
        assert r.find("kn1").version == "3.0.0"
        # runtime & summary pakai registry yang sama
        assert KnowledgeRuntime(r).run("kn1").ok is True
        assert KnowledgeSummarizer(r).summary().total_knowledge == 1

    def test_capability_bound_to_descriptor(self):
        r = _registry()
        caps = r.get_capabilities("kn1")
        assert caps[0].knowledge_id == "kn1"
        assert caps[0].supports("organize") is True
        assert caps[0].supports("infer") is False
        # preview-only default, tanpa promotion
        assert caps[0].preview_only is True

    def test_contract_guarantee_preserved(self):
        r = _registry()
        assert "no-inference" in r.get_contract("kn1").guarantees

    def test_builder_contract_roundtrip(self):
        r = _registry()
        d = r.find("kn1")
        built = KnowledgeBuilder().build(d.id, name=d.name)
        assert built.valid is True
        assert built.descriptor.id == "kn1"
        assert built.descriptor.name == "Contract Knowledge"
        assert built.record.knowledge_id == "kn1"
        assert built.record.is_valid()


class TestModelContract:
    """Model layer — konstruksi & fokus knowledge (fact/record/relation)."""

    def test_record(self):
        rec = KnowledgeRecord(record_id="rec.1", knowledge_id="kn1")
        assert rec.knowledge_id == "kn1"
        assert rec.record_id == "rec.1"
        assert rec.is_valid() is True
        # preview-only default, tanpa promotion
        assert rec.preview_only is True

    def test_fact(self):
        f = KnowledgeFactPreview("f1", subject="SAM", predicate="is", obj="arch")
        assert f.fact_id == "f1"
        assert f.obj == "arch"
        assert f.is_valid() is True
        assert f.preview_only is True

    def test_relation(self):
        rel = KnowledgeRelationPreview("r1", source_id="kn1", target_id="kn2", rel_type="linked")
        assert rel.rel_type == "linked"
        assert rel.is_valid() is True
