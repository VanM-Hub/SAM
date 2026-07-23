"""Unit tests for KnowledgeStore history/versioning."""

import os
import tempfile
import pytest
import pytest_asyncio

from uuid import UUID
from datetime import datetime

from sam.knowledge.store import KnowledgeStore, create_knowledge_store
from sam.knowledge.models import KnowledgeDocument, KnowledgeFact


@pytest_asyncio.fixture
async def test_db():
    """Create a temporary database for testing."""
    # Create temp file
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)

    # Create store and initialize tables (this creates all tables with new schema)
    store = await create_knowledge_store(path)
    await store.close()

    yield path

    # Cleanup
    if os.path.exists(path):
        os.unlink(path)


@pytest_asyncio.fixture
async def store(test_db):
    """Create a KnowledgeStore with initialized tables."""
    s = KnowledgeStore(test_db)
    await s.init_tables()
    yield s
    await s.close()


class TestKnowledgeStoreHistory:
    """Tests for KnowledgeStore history/versioning."""

    @pytest_asyncio.fixture
    async def store(self, test_db):
        """Create a KnowledgeStore with initialized tables."""
        s = KnowledgeStore(test_db)
        await s.init_tables()
        yield s
        await s.close()

    @pytest.mark.asyncio
    async def test_history_created(self, store):
        """Test that add_fact creates a history entry with change_type='created'."""
        # Create a document first
        doc = KnowledgeDocument(
            path="test.md",
            title="Test Doc",
            version="1.0",
            status="Draft",
            knowledge_type="Reference",
            evidence_level="Observed",
            confidence="High",
            owner="Test",
            last_updated="2024-01-01T00:00:00",
            content="Test content",
        )
        doc_id = await store.add_document(doc)

        # Add a fact
        fact = await store.add_fact(
            document_id=doc_id,
            statement="Test fact statement",
            category="capability",
            confidence=0.9,
            metadata={"key": "value"}
        )

        # Check history
        history = await store.list_history(fact.id)
        assert len(history) == 1
        entry = history[0]
        assert entry.change_type == "created"
        assert entry.version == 1
        assert entry.payload_snapshot["statement"] == "Test fact statement"
        assert entry.payload_snapshot["category"] == "capability"
        assert entry.payload_snapshot["metadata"]["key"] == "value"

    @pytest.mark.asyncio
    async def test_history_updated(self, store):
        """Test that update_fact creates a history entry with change_type='updated'."""
        doc = KnowledgeDocument(
            path="test.md",
            title="Test Doc",
            version="1.0",
            status="Draft",
            knowledge_type="Reference",
            evidence_level="Observed",
            confidence="High",
            owner="Test",
            last_updated="2024-01-01T00:00:00",
            content="Test content",
        )
        doc_id = await store.add_document(doc)

        fact = await store.add_fact(
            document_id=doc_id,
            statement="Original statement",
            category="capability",
            confidence=0.9,
        )

        # Update the fact
        updated = await store.update_fact(fact.id, {
            "statement": "Updated statement",
            "category": "constraint",
            "confidence": 0.8,
        })

        assert updated is not None
        assert updated.version == 2
        assert updated.statement == "Updated statement"
        assert updated.category == "constraint"
        assert updated.confidence == 0.8

        # Check history has 2 entries
        history = await store.list_history(fact.id)
        assert len(history) == 2

        # First entry: created
        created_entry = history[0]
        assert created_entry.change_type == "created"
        assert created_entry.version == 1
        assert created_entry.payload_snapshot["statement"] == "Original statement"

        # Second entry: updated
        updated_entry = history[1]
        assert updated_entry.change_type == "updated"
        assert updated_entry.version == 2
        assert updated_entry.payload_snapshot["statement"] == "Updated statement"
        assert updated_entry.payload_snapshot["category"] == "constraint"

    @pytest.mark.asyncio
    async def test_history_deleted(self, store):
        """Test that delete_fact creates a history entry with change_type='deleted'."""
        doc = KnowledgeDocument(
            path="test.md",
            title="Test Doc",
            version="1.0",
            status="Draft",
            knowledge_type="Reference",
            evidence_level="Observed",
            confidence="High",
            owner="Test",
            last_updated="2024-01-01T00:00:00",
            content="Test content",
        )
        doc_id = await store.add_document(doc)

        fact = await store.add_fact(
            document_id=doc_id,
            statement="Fact to be deleted",
            category="capability",
            confidence=0.9,
        )

        # Delete the fact
        result = await store.delete_fact(fact.id)
        assert result is True

        # Check history has 2 entries: created and deleted
        history = await store.list_history(fact.id)
        assert len(history) == 2

        created_entry = history[0]
        assert created_entry.change_type == "created"
        assert created_entry.version == 1
        assert created_entry.payload_snapshot["statement"] == "Fact to be deleted"

        deleted_entry = history[1]
        assert deleted_entry.change_type == "deleted"
        assert deleted_entry.version == 1  # Version doesn't increment on delete
        assert deleted_entry.payload_snapshot["statement"] == "Fact to be deleted"

        # Verify fact is actually deleted
        fact_gone = await store.get_fact(fact.id)
        assert fact_gone is None

    @pytest.mark.asyncio
    async def test_history_list_complete(self, store):
        """Test that list_history returns complete history in correct order."""
        doc = KnowledgeDocument(
            path="test.md",
            title="Test Doc",
            version="1.0",
            status="Draft",
            knowledge_type="Reference",
            evidence_level="Observed",
            confidence="High",
            owner="Test",
            last_updated="2024-01-01T00:00:00",
            content="Test content",
        )
        doc_id = await store.add_document(doc)

        fact = await store.add_fact(
            document_id=doc_id,
            statement="Version 1",
            category="capability",
            confidence=0.9,
        )

        # Update multiple times
        await store.update_fact(fact.id, {"statement": "Version 2"})
        await store.update_fact(fact.id, {"statement": "Version 3"})
        await store.update_fact(fact.id, {"statement": "Version 4"})

        history = await store.list_history(fact.id)
        
        # Should have 4 entries (created + 3 updates)
        assert len(history) == 4

        # Check order: version 1, 2, 3, 4
        assert history[0].version == 1
        assert history[0].change_type == "created"
        assert history[1].version == 2
        assert history[1].change_type == "updated"
        assert history[2].version == 3
        assert history[2].change_type == "updated"
        assert history[3].version == 4
        assert history[3].change_type == "updated"

        # Check snapshots match
        assert history[0].payload_snapshot["statement"] == "Version 1"
        assert history[1].payload_snapshot["statement"] == "Version 2"
        assert history[2].payload_snapshot["statement"] == "Version 3"
        assert history[3].payload_snapshot["statement"] == "Version 4"

    @pytest.mark.asyncio
    async def test_previous_version_link(self, store):
        """Test that previous_version column is updated correctly."""
        doc = KnowledgeDocument(
            path="test.md",
            title="Test Doc",
            version="1.0",
            status="Draft",
            knowledge_type="Reference",
            evidence_level="Observed",
            confidence="High",
            owner="Test",
            last_updated="2024-01-01T00:00:00",
            content="Test content",
        )
        doc_id = await store.add_document(doc)

        fact = await store.add_fact(
            document_id=doc_id,
            statement="Original",
            category="capability",
        )

        # Check previous_version is NULL for new fact
        import sqlite3
        conn = sqlite3.connect(store.db_path)
        cur = conn.cursor()
        cur.execute("SELECT previous_version FROM knowledge WHERE id = ?", (str(fact.id),))
        row = cur.fetchone()
        assert row[0] is None

        # Update
        await store.update_fact(fact.id, {"statement": "Updated"})

        cur.execute("SELECT previous_version, version FROM knowledge WHERE id = ?", (str(fact.id),))
        row = cur.fetchone()
        assert row[0] == 1  # previous_version points to v1
        assert row[1] == 2  # current version is v2
        conn.close()

    @pytest.mark.asyncio
    async def test_history_nonexistent_fact(self, store):
        """Test list_history returns empty list for non-existent fact."""
        history = await store.list_history(UUID("00000000-0000-0000-0000-000000000000"))
        assert history == []


if __name__ == "__main__":
    pytest.main([__file__, "-v"])