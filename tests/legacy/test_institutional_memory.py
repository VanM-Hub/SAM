"""Tests for Institutional Intelligence — Sprint 25 Fase 1.

InstitutionalMemory, InstitutionalMemoryManager, Lesson, LessonManager.
"""

import json
import tempfile
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
import pytest_asyncio

from sam.persistence.database import Database
from sam.institutional.memory import (
    InstitutionalMemory,
    InstitutionalMemoryManager,
    MEMORY_TYPES,
)
from sam.institutional.lesson import Lesson, LessonManager


@pytest_asyncio.fixture
async def db():
    """Create temporary database with all migrations applied."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    database = Database(db_path)
    await database.initialize()
    from sam.persistence.migrations.manager import MigrationManager
    migrations_dir = Path(__file__).parent.parent / "sam" / "persistence" / "migrations"
    manager = MigrationManager(database, str(migrations_dir))
    await manager.migrate()
    yield database
    await database.close()
    Path(db_path).unlink(missing_ok=True)


# ─────────────────────────────────────────────
# InstitutionalMemory model tests
# ─────────────────────────────────────────────

class TestInstitutionalMemoryModel:
    def test_create_minimal(self):
        mem = InstitutionalMemory(
            id="mem-1",
            type="KNOWLEDGE",
            content={"key": "value"},
        )
        assert mem.id == "mem-1"
        assert mem.type == "KNOWLEDGE"
        assert mem.content == {"key": "value"}
        assert mem.confidence == 1.0
        assert mem.success_count == 0
        assert mem.failure_count == 0

    def test_invalid_type_raises(self):
        with pytest.raises(ValueError, match="Invalid memory type"):
            InstitutionalMemory(id="x", type="INVALID", content={})

    def test_invalid_confidence_raises(self):
        with pytest.raises(ValueError, match="confidence"):
            InstitutionalMemory(id="x", type="KNOWLEDGE", content={}, confidence=1.5)

    def test_all_memory_types_accepted(self):
        for t in MEMORY_TYPES:
            mem = InstitutionalMemory(id=f"mem-{t}", type=t, content={})
            assert mem.type == t

    def test_to_dict_and_from_dict_roundtrip(self):
        now = datetime.now(timezone.utc)
        mem = InstitutionalMemory(
            id="mem-rt",
            type="PATTERN",
            content={"pattern": "p1", "severity": "high"},
            source="cluster-1",
            confidence=0.85,
            success_count=10,
            failure_count=2,
            last_used_at=now - timedelta(hours=1),
            created_at=now - timedelta(days=1),
            updated_at=now,
        )
        d = mem.to_dict()
        mem2 = InstitutionalMemory.from_dict(d)
        assert mem2.id == mem.id
        assert mem2.type == mem.type
        assert mem2.content == mem.content
        assert mem2.source == mem.source
        assert mem2.confidence == mem.confidence
        assert mem2.success_count == mem.success_count
        assert mem2.failure_count == mem.failure_count
        assert mem2.last_used_at is not None

    def test_from_dict_with_json_content_string(self):
        d = {
            "id": "mem-1",
            "type": "KNOWLEDGE",
            "content": '{"key": "value"}',
            "source": "",
            "confidence": 1.0,
            "success_count": 0,
            "failure_count": 0,
        }
        mem = InstitutionalMemory.from_dict(d)
        assert mem.content == {"key": "value"}

    def test_from_dict_with_none_timestamps(self):
        d = {"id": "mem-1", "type": "KNOWLEDGE", "content": "{}"}
        mem = InstitutionalMemory.from_dict(d)
        assert mem.created_at is not None
        assert mem.updated_at is not None


# ─────────────────────────────────────────────
# InstitutionalMemoryManager tests
# ─────────────────────────────────────────────

class TestInstitutionalMemoryManager:
    @pytest.mark.asyncio
    async def test_store_and_get(self, db):
        manager = InstitutionalMemoryManager(db)
        mem = InstitutionalMemory(
            id="mem-store-1",
            type="KNOWLEDGE",
            content={"fact": "water boils at 100°C"},
            source="knowledge-base",
        )
        await manager.store(mem)
        retrieved = await manager.get("mem-store-1")
        assert retrieved is not None
        assert retrieved.id == mem.id
        assert retrieved.content == mem.content
        assert retrieved.confidence == mem.confidence

    @pytest.mark.asyncio
    async def test_get_nonexistent_returns_none(self, db):
        manager = InstitutionalMemoryManager(db)
        result = await manager.get("nonexistent-id")
        assert result is None

    @pytest.mark.asyncio
    async def test_store_overwrites_existing(self, db):
        manager = InstitutionalMemoryManager(db)
        mem1 = InstitutionalMemory(
            id="mem-overwrite",
            type="KNOWLEDGE",
            content={"v": 1},
            confidence=0.5,
        )
        await manager.store(mem1)
        mem2 = InstitutionalMemory(
            id="mem-overwrite",
            type="KNOWLEDGE",
            content={"v": 2},
            confidence=0.9,
        )
        await manager.store(mem2)
        retrieved = await manager.get("mem-overwrite")
        assert retrieved.content == {"v": 2}
        assert retrieved.confidence == 0.9

    @pytest.mark.asyncio
    async def test_search_by_type(self, db):
        manager = InstitutionalMemoryManager(db)
        types = ["KNOWLEDGE", "PATTERN", "RECOMMENDATION", "LESSON"]
        for t in types:
            await manager.store(InstitutionalMemory(
                id=f"mem-search-{t}",
                type=t,
                content={},
            ))
        results = await manager.search({"type": "PATTERN"})
        assert len(results) == 1
        assert results[0].type == "PATTERN"

    @pytest.mark.asyncio
    async def test_search_by_source_substring(self, db):
        manager = InstitutionalMemoryManager(db)
        await manager.store(InstitutionalMemory(
            id="mem-src-1",
            type="KNOWLEDGE",
            content={},
            source="cluster-alpha/workflow-42",
        ))
        await manager.store(InstitutionalMemory(
            id="mem-src-2",
            type="KNOWLEDGE",
            content={},
            source="cluster-beta/workflow-99",
        ))
        results = await manager.search({"source": "alpha"})
        assert len(results) == 1
        assert "alpha" in results[0].source

    @pytest.mark.asyncio
    async def test_search_by_min_confidence(self, db):
        manager = InstitutionalMemoryManager(db)
        await manager.store(InstitutionalMemory(
            id="mem-conf-1", type="KNOWLEDGE", content={}, confidence=0.3,
        ))
        await manager.store(InstitutionalMemory(
            id="mem-conf-2", type="KNOWLEDGE", content={}, confidence=0.7,
        ))
        await manager.store(InstitutionalMemory(
            id="mem-conf-3", type="KNOWLEDGE", content={}, confidence=0.9,
        ))
        results = await manager.search({"min_confidence": 0.6})
        assert len(results) == 2
        assert all(r.confidence >= 0.6 for r in results)

    @pytest.mark.asyncio
    async def test_search_empty_query_returns_all(self, db):
        manager = InstitutionalMemoryManager(db)
        for i in range(3):
            await manager.store(InstitutionalMemory(
                id=f"mem-all-{i}",
                type="KNOWLEDGE",
                content={},
            ))
        results = await manager.search({})
        assert len(results) == 3

    @pytest.mark.asyncio
    async def test_update_success_rate_success(self, db):
        manager = InstitutionalMemoryManager(db)
        mem = InstitutionalMemory(
            id="mem-rate",
            type="KNOWLEDGE",
            content={},
        )
        await manager.store(mem)
        await manager.update_success_rate("mem-rate", success=True)
        retrieved = await manager.get("mem-rate")
        assert retrieved.success_count == 1
        assert retrieved.failure_count == 0

    @pytest.mark.asyncio
    async def test_update_success_rate_failure(self, db):
        manager = InstitutionalMemoryManager(db)
        mem = InstitutionalMemory(
            id="mem-rate-2",
            type="KNOWLEDGE",
            content={},
        )
        await manager.store(mem)
        await manager.update_success_rate("mem-rate-2", success=False)
        retrieved = await manager.get("mem-rate-2")
        assert retrieved.failure_count == 1
        assert retrieved.success_count == 0

    @pytest.mark.asyncio
    async def test_get_most_successful(self, db):
        manager = InstitutionalMemoryManager(db)
        for i in range(5):
            await manager.store(InstitutionalMemory(
                id=f"mem-top-{i}",
                type="KNOWLEDGE",
                content={},
                success_count=i * 2,
                confidence=0.5 + i * 0.1,
            ))
        top3 = await manager.get_most_successful("KNOWLEDGE", limit=3)
        assert len(top3) == 3
        # Highest success_count first
        assert top3[0].success_count >= top3[1].success_count

    @pytest.mark.asyncio
    async def test_get_most_successful_invalid_type_raises(self, db):
        manager = InstitutionalMemoryManager(db)
        with pytest.raises(ValueError, match="Invalid memory type"):
            await manager.get_most_successful("BOGUS")

    @pytest.mark.asyncio
    async def test_search_combined_filters(self, db):
        manager = InstitutionalMemoryManager(db)
        await manager.store(InstitutionalMemory(
            id="mem-comb-1", type="PATTERN", content={},
            source="cluster-1", confidence=0.9,
        ))
        await manager.store(InstitutionalMemory(
            id="mem-comb-2", type="PATTERN", content={},
            source="cluster-2", confidence=0.5,
        ))
        await manager.store(InstitutionalMemory(
            id="mem-comb-3", type="KNOWLEDGE", content={},
            source="cluster-1", confidence=0.8,
        ))
        # Combined filter: type=PATTERN, source=cluster-1, min_confidence=0.6
        results = await manager.search({
            "type": "PATTERN",
            "source": "cluster-1",
            "min_confidence": 0.6,
        })
        assert len(results) == 1
        assert results[0].id == "mem-comb-1"


# ─────────────────────────────────────────────
# Lesson model tests
# ─────────────────────────────────────────────

class TestLessonModel:
    def test_create_lesson(self):
        lesson = Lesson(
            id="lesson-1",
            intent_id="intent-42",
            graph_id="graph-7",
            what_worked="Great query performance",
            what_failed="Excessive memory usage",
            insight="Use pagination for large result sets",
            confidence=0.8,
            evidence_ids=["ev-1", "ev-2"],
        )
        assert lesson.id == "lesson-1"
        assert lesson.intent_id == "intent-42"
        assert lesson.graph_id == "graph-7"
        assert lesson.what_worked == "Great query performance"
        assert lesson.confidence == 0.8
        assert lesson.evidence_ids == ["ev-1", "ev-2"]

    def test_lesson_invalid_confidence_raises(self):
        with pytest.raises(ValueError, match="confidence"):
            Lesson(id="x", intent_id="i", graph_id="g", confidence=1.5)

    def test_lesson_to_dict_and_from_dict_roundtrip(self):
        now = datetime.now(timezone.utc)
        lesson = Lesson(
            id="lesson-rt",
            intent_id="intent-1",
            graph_id="graph-2",
            what_worked="worked",
            what_failed="failed",
            insight="insight",
            confidence=0.75,
            evidence_ids=["e1", "e2"],
            timestamp=now,
        )
        d = lesson.to_dict()
        lesson2 = Lesson.from_dict(d)
        assert lesson2.id == lesson.id
        assert lesson2.intent_id == lesson.intent_id
        assert lesson2.confidence == lesson.confidence
        assert lesson2.evidence_ids == lesson.evidence_ids
        assert lesson2.timestamp is not None

    def test_lesson_from_dict_with_json_string_list(self):
        d = {
            "id": "l1",
            "intent_id": "i1",
            "graph_id": "g1",
            "evidence_ids": '["ev-1","ev-2"]',
        }
        lesson = Lesson.from_dict(d)
        assert lesson.evidence_ids == ["ev-1", "ev-2"]

    def test_lesson_default_timestamp(self):
        lesson = Lesson(id="l1", intent_id="i1", graph_id="g1")
        assert lesson.timestamp is not None


# ─────────────────────────────────────────────
# LessonManager tests
# ─────────────────────────────────────────────

class TestLessonManager:
    @pytest.mark.asyncio
    async def test_record_and_get_by_intent(self, db):
        manager = LessonManager(db)
        lesson = Lesson(
            id="l-rec-1",
            intent_id="intent-a",
            graph_id="graph-1",
            what_worked="Fast response",
            what_failed="Timeout on large data",
            insight="Add streaming",
        )
        await manager.record_lesson(lesson)
        lessons = await manager.get_lessons(intent_id="intent-a")
        assert len(lessons) == 1
        assert lessons[0].id == "l-rec-1"
        assert lessons[0].insight == "Add streaming"

    @pytest.mark.asyncio
    async def test_record_and_get_by_graph(self, db):
        manager = LessonManager(db)
        await manager.record_lesson(Lesson(
            id="l-graph",
            intent_id="intent-b",
            graph_id="graph-99",
        ))
        lessons = await manager.get_lessons(graph_id="graph-99")
        assert len(lessons) == 1

    @pytest.mark.asyncio
    async def test_get_lessons_no_filter_returns_all(self, db):
        manager = LessonManager(db)
        for i in range(3):
            await manager.record_lesson(Lesson(
                id=f"l-all-{i}",
                intent_id="intent-x",
                graph_id=f"graph-{i}",
            ))
        lessons = await manager.get_lessons()
        assert len(lessons) == 3

    @pytest.mark.asyncio
    async def test_get_lessons_empty_result(self, db):
        manager = LessonManager(db)
        lessons = await manager.get_lessons(intent_id="nonexistent")
        assert lessons == []

    @pytest.mark.asyncio
    async def test_multiple_lessons_same_intent(self, db):
        manager = LessonManager(db)
        for i in range(3):
            await manager.record_lesson(Lesson(
                id=f"l-multi-{i}",
                intent_id="intent-multi",
                graph_id=f"graph-{i}",
                what_worked=f"worked-{i}",
            ))
        lessons = await manager.get_lessons(intent_id="intent-multi")
        assert len(lessons) == 3
        what_worked_list = [l.what_worked for l in lessons]
        assert "worked-0" in what_worked_list
        assert "worked-2" in what_worked_list

    @pytest.mark.asyncio
    async def test_record_multiple_graphs(self, db):
        manager = LessonManager(db)
        await manager.record_lesson(Lesson(
            id="l-mg-1", intent_id="i1", graph_id="g1",
        ))
        await manager.record_lesson(Lesson(
            id="l-mg-2", intent_id="i2", graph_id="g2",
        ))
        g1_lessons = await manager.get_lessons(graph_id="g1")
        assert len(g1_lessons) == 1
        assert g1_lessons[0].id == "l-mg-1"

    @pytest.mark.asyncio
    async def test_lesson_with_full_evidence(self, db):
        manager = LessonManager(db)
        lesson = Lesson(
            id="l-evidence",
            intent_id="intent-e",
            graph_id="graph-e",
            what_worked="Caching improved perf",
            insight="Always cache reference data",
            confidence=0.95,
            evidence_ids=["ev-cache-1", "ev-cache-2", "ev-cache-3"],
        )
        await manager.record_lesson(lesson)
        lessons = await manager.get_lessons(intent_id="intent-e")
        assert len(lessons) == 1
        assert len(lessons[0].evidence_ids) == 3
