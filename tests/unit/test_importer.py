"""Unit tests for KnowledgeImporter."""

import sys
import os
import tempfile
import pytest
from pathlib import Path
from uuid import uuid4

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from sam.knowledge.importer import KnowledgeImporter
from sam.knowledge.store import create_knowledge_store, KnowledgeStore


def apply_migrations(db_path):
    """Apply required migrations to test database."""
    import sqlite3
    import glob
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    
    # Create schema_version table so migrations can record their application
    cur.execute('''
        CREATE TABLE IF NOT EXISTS schema_version (
            version INTEGER PRIMARY KEY,
            applied_at TEXT,
            description TEXT
        )
    ''')

    # Apply all migration files in order
    migration_files = sorted(glob.glob("src/sam/persistence/migrations/*.sql"))
    for f in migration_files:
        with open(f, 'r') as mf:
            sql = mf.read()
        try:
            cur.executescript(sql)
        except sqlite3.OperationalError as e:
            # Ignore errors for columns/tables that already exist
            if "duplicate column" in str(e).lower() or "already exists" in str(e).lower():
                pass
            else:
                raise
    conn.commit()
    conn.close()


@pytest.fixture
def test_db():
    """Create an isolated test database."""
    import time
    db_path = os.path.abspath(f"sam_test_importer_{int(time.time()*1000)}.db")
    apply_migrations(db_path)
    yield db_path
    if os.path.exists(db_path):
        os.remove(db_path)


@pytest.fixture
def store(test_db):
    """Create a KnowledgeStore synchronously (async init done in tests)."""
    return KnowledgeStore(test_db)


class TestKnowledgeImporter:
    """Tests for KnowledgeImporter class."""

    @pytest.mark.asyncio
    async def test_import_yaml_valid(self, store):
        """Test importing YAML with facts and relationships."""
        await store.init_tables()
        yaml_content = """
facts:
  - statement: "Provider A supports Model X"
    category: capability
    metadata:
      provider: "A"
      model: "X"
      confidence: 0.95
    relationships:
      - target: "Model X requires GPU"
        type: depends_on

  - statement: "Model X requires GPU"
    category: constraint
    metadata:
      hardware: "GPU"
    relationships: []
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            yaml_path = f.name

        try:
            importer = KnowledgeImporter()
            created = await importer.import_yaml(Path(yaml_path), store)

            assert len(created) == 2

            # Verify facts were created
            facts = await store.list_facts(limit=10)
            assert len(facts) == 2

            # Verify relationships were created
            graph = store.graph
            rels = await graph.get_relationships()
            assert len(rels) >= 1
            # Check depends_on relationship exists
            depends_rels = [r for r in rels if r.relationship_type == 'depends_on']
            assert len(depends_rels) == 1
        finally:
            os.unlink(yaml_path)
            await store.close()

    @pytest.mark.asyncio
    async def test_import_json_valid(self, store):
        """Test importing JSON with facts and relationships."""
        await store.init_tables()
        json_content = {
            "facts": [
                {
                    "statement": "Provider B supports Model Y",
                    "category": "capability",
                    "metadata": {
                        "provider": "B",
                        "model": "Y",
                        "confidence": 0.9
                    },
                    "relationships": [
                        {
                            "target": "Model Y requires TPU",
                            "type": "depends_on"
                        }
                    ]
                },
                {
                    "statement": "Model Y requires TPU",
                    "category": "constraint",
                    "metadata": {
                        "hardware": "TPU"
                    },
                    "relationships": []
                }
            ]
        }
        import json
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(json_content, f)
            json_path = f.name

        try:
            importer = KnowledgeImporter()
            created = await importer.import_json(Path(json_path), store)

            assert len(created) == 2

            facts = await store.list_facts(limit=10)
            assert len(facts) == 2

            graph = store.graph
            rels = await graph.get_relationships()
            depends_rels = [r for r in rels if r.relationship_type == 'depends_on']
            assert len(depends_rels) == 1
        finally:
            os.unlink(json_path)
            await store.close()

    @pytest.mark.asyncio
    async def test_import_markdown_references(self, store):
        """Test that markdown frontmatter and inline links create relationships."""
        await store.init_tables()
        from sam.knowledge.loader import KnowledgeLoader

        md_content = """# Test Document
Version: 1.0
Status: Draft
Knowledge Type: Reference
Evidence Level: Observed
Confidence: High
Owner: Test
Last Updated: 2024-01-01
Related Documents: doc1.md, doc2.md
References: https://example.com/ref1

## Facts

- Fact one references [external link](https://example.com/inline)
- Fact two references doc1.md
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # KnowledgeLoader looks in docs/ and modules/ subdirectories
            docs_dir = Path(tmpdir) / "docs"
            docs_dir.mkdir()
            md_path = docs_dir / "test.md"
            md_path.write_text(md_content, encoding="utf-8")

            loader = KnowledgeLoader(tmpdir)
            docs = await loader.load_all(store=store)

            assert len(docs) == 1
            doc = docs[0]
            # Should have related_documents from frontmatter
            assert "doc1.md" in doc.related_documents
            assert "doc2.md" in doc.related_documents
            # Should have references from frontmatter + inline links
            assert "https://example.com/ref1" in doc.references
            assert "https://example.com/inline" in doc.references

            # Facts should have been created with auto-relationships
            facts = await store.list_facts(limit=10)
            assert len(facts) >= 2
        await store.close()

    @pytest.mark.asyncio
    async def test_import_invalid_format(self, store):
        """Test error handling for invalid import format."""
        await store.init_tables()
        # Missing 'facts' key
        json_content = {"items": []}
        import json
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(json_content, f)
            json_path = f.name

        try:
            importer = KnowledgeImporter()
            with pytest.raises(ValueError, match="Invalid import format"):
                await importer.import_json(Path(json_path), store)
        finally:
            os.unlink(json_path)

        # 'facts' not a list
        json_content2 = {"facts": "not a list"}
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(json_content2, f)
            json_path2 = f.name

        try:
            with pytest.raises(ValueError, match="'facts' must be a list"):
                await importer.import_json(Path(json_path2), store)
        finally:
            os.unlink(json_path2)

        # Fact missing statement
        json_content3 = {"facts": [{"category": "test"}]}
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(json_content3, f)
            json_path3 = f.name

        try:
            importer = KnowledgeImporter()
            created = await importer.import_json(Path(json_path3), store)
            # Should skip facts without statement, create 0
            assert len(created) == 0
        finally:
            os.unlink(json_path3)
        await store.close()

    @pytest.mark.asyncio
    async def test_import_missing_pyyaml(self, store):
        """Test error when PyYAML not available."""
        await store.init_tables()
        try:
            # This test is skipped if PyYAML is installed
            try:
                import yaml
                pytest.skip("PyYAML is installed, cannot test missing dependency")
            except ImportError:
                pass

            importer = KnowledgeImporter()
            # Monkey-patch yaml to None
            import sam.knowledge.importer as importer_module
            original_yaml = importer_module.yaml
            importer_module.yaml = None

            try:
                with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
                    f.write("facts: []")
                    yaml_path = f.name

                try:
                    with pytest.raises(RuntimeError, match="PyYAML not available"):
                        await importer.import_yaml(Path(yaml_path), store)
                finally:
                    os.unlink(yaml_path)
            finally:
                importer_module.yaml = original_yaml
        finally:
            await store.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])