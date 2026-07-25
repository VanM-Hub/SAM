"""Unit tests for ReportGenerator (Tugas 9.5)."""

import asyncio
import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import pytest
import pytest_asyncio

from sam.persistence.database import Database
from sam.events.event_bus import EventBus
from sam.reporting.generator import ReportGenerator
from sam.reporting.models import ExecutionReport


@pytest_asyncio.fixture
async def temp_db():
    """Create a temporary database for testing."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    
    db = Database(db_path)
    await db.initialize()
    
    # Apply migrations manually to create required tables
    from sam.persistence.migrations.manager import MigrationManager
    migrations_dir = Path(__file__).parent.parent.parent / "sam" / "persistence" / "migrations"
    manager = MigrationManager(db, str(migrations_dir))
    await manager.migrate()
    
    yield db
    
    await db.close()
    Path(db_path).unlink(missing_ok=True)


@pytest_asyncio.fixture
async def event_bus():
    """Create an event bus for testing."""
    bus = EventBus()
    yield bus


@pytest_asyncio.fixture
async def report_generator(temp_db, event_bus):
    """Create a ReportGenerator instance."""
    return ReportGenerator(temp_db, event_bus)


async def _create_test_execution(db, execution_id: str, capability_id: str = "test.capability"):
    """Create a test execution record in the database."""
    import uuid
    correlation_id = str(uuid.uuid4())
    started_at = datetime.now(timezone.utc).isoformat()
    
    await db.execute(
        """
        INSERT INTO executions (id, correlation_id, capability_id, workflow_id, step_name, status, started_at, inputs)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [execution_id, correlation_id, capability_id, None, "test_step", "running", started_at, '{"input": "value"}']
    )
    
    return correlation_id


async def _complete_execution(db, execution_id: str, status: str = "success", result: dict = None, error: str = None):
    """Mark an execution as completed."""
    completed_at = datetime.now(timezone.utc).isoformat()
    result_json = json.dumps(result) if result else '{}'
    
    await db.execute(
        """
        UPDATE executions SET status = ?, completed_at = ?, result = ?, error = ? WHERE id = ?
        """,
        [status, completed_at, result_json, error, execution_id]
    )


class TestReportGenerator:
    """Test ReportGenerator.generate() functionality."""

    @pytest.mark.asyncio
    async def test_generate_creates_report_for_successful_execution(self, report_generator, temp_db):
        """Test that generate() creates a report for a successful execution."""
        execution_id = "test-exec-1"
        correlation_id = await _create_test_execution(temp_db, execution_id)
        await _complete_execution(temp_db, execution_id, "success", {"status": "ok"})
        
        report = await report_generator.generate(execution_id)
        
        assert report is not None
        assert report.execution_id == execution_id
        assert report.correlation_id == correlation_id
        assert report.capability_id == "test.capability"
        assert report.status == "success"
        assert report.evidence_count == 0
        assert report.knowledge_count == 0
        assert report.pattern_count == 0
        assert report.recommendation_count == 0

    @pytest.mark.asyncio
    async def test_generate_creates_report_for_failed_execution(self, report_generator, temp_db):
        """Test that generate() creates a report for a failed execution."""
        execution_id = "test-exec-failed"
        correlation_id = await _create_test_execution(temp_db, execution_id)
        await _complete_execution(temp_db, execution_id, "failed", error="Something went wrong")
        
        report = await report_generator.generate(execution_id)
        
        assert report is not None
        assert report.execution_id == execution_id
        assert report.status == "failed"
        assert report.summary.get("error") == "Something went wrong"

    @pytest.mark.asyncio
    async def test_generate_returns_none_for_nonexistent_execution(self, report_generator):
        """Test that generate() raises ValueError for non-existent execution."""
        with pytest.raises(ValueError, match="Execution not found"):
            await report_generator.generate("nonexistent-execution")

    @pytest.mark.asyncio
    async def test_generate_saves_report_to_database(self, report_generator, temp_db):
        """Test that generate() saves the report to the database."""
        execution_id = "test-exec-save"
        await _create_test_execution(temp_db, execution_id)
        await _complete_execution(temp_db, execution_id, "success")
        
        await report_generator.generate(execution_id)
        
        # Verify report was saved
        row = await temp_db.fetch_one(
            "SELECT * FROM reports WHERE execution_id = ?", [execution_id]
        )
        assert row is not None
        assert row["execution_id"] == execution_id
        assert row["status"] == "success"

    @pytest.mark.asyncio
    async def test_generate_counts_related_records(self, report_generator, temp_db):
        """Test that generate() correctly counts evidence, knowledge, patterns, recommendations."""
        execution_id = "test-exec-counts"
        correlation_id = await _create_test_execution(temp_db, execution_id)
        await _complete_execution(temp_db, execution_id, "success")
        
        # Insert related records with correct schema
        await temp_db.execute(
            """
            INSERT INTO evidence (id, correlation_id, execution_id, capability_id, type, confidence, payload, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            ["ev-1", correlation_id, execution_id, "test.capability", "test", 0.9, '{}', datetime.now(timezone.utc).isoformat()]
        )
        await temp_db.execute(
            """
            INSERT INTO evidence (id, correlation_id, execution_id, capability_id, type, confidence, payload, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            ["ev-2", correlation_id, execution_id, "test.capability", "test", 0.8, '{}', datetime.now(timezone.utc).isoformat()]
        )
        await temp_db.execute(
            """
            INSERT INTO knowledge (id, correlation_id, capability_id, status, confidence, payload, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            ["kf-1", correlation_id, "test.capability", "verified", 0.9, '{}', datetime.now(timezone.utc).isoformat()]
        )
        await temp_db.execute(
            """
            INSERT INTO patterns (id, correlation_id, rule_id, severity, message, metadata, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            ["pat-1", correlation_id, "test-rule", "info", "test pattern", '{}', datetime.now(timezone.utc).isoformat()]
        )
        await temp_db.execute(
            """
            INSERT INTO recommendations (id, correlation_id, rule_id, severity, title, description, action_hint, status, metadata, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            ["rec-1", correlation_id, "test-rule", "info", "Test recommendation", "desc", "hint", "pending", '{}', datetime.now(timezone.utc).isoformat()]
        )
        
        report = await report_generator.generate(execution_id)
        
        assert report.evidence_count == 2
        assert report.knowledge_count == 1
        assert report.pattern_count == 1
        assert report.recommendation_count == 1


class TestReportGeneratorExport:
    """Test ReportGenerator export methods."""

    @pytest.mark.asyncio
    async def test_export_markdown(self, report_generator, temp_db):
        """Test export_markdown() produces valid markdown."""
        execution_id = "test-exec-md"
        correlation_id = await _create_test_execution(temp_db, execution_id)
        await _complete_execution(temp_db, execution_id, "success", {"result": "ok"})
        
        report = await report_generator.generate(execution_id)
        markdown = await report_generator.export_markdown(report)
        
        assert isinstance(markdown, str)
        assert "# Execution Report:" in markdown
        assert execution_id in markdown
        assert correlation_id in markdown
        assert "test.capability" in markdown
        assert "success" in markdown
        assert "## Counts" in markdown
        assert "## Summary" in markdown

    @pytest.mark.asyncio
    async def test_export_json(self, report_generator, temp_db):
        """Test export_json() produces valid JSON."""
        execution_id = "test-exec-json"
        correlation_id = await _create_test_execution(temp_db, execution_id)
        await _complete_execution(temp_db, execution_id, "success", {"key": "value"})
        
        report = await report_generator.generate(execution_id)
        json_str = await report_generator.export_json(report)
        
        data = json.loads(json_str)
        assert data["execution_id"] == execution_id
        assert data["correlation_id"] == correlation_id
        assert data["capability_id"] == "test.capability"
        assert data["status"] == "success"
        assert data["summary"]["result"] == '{"key": "value"}'


class TestReportGeneratorGet:
    """Test ReportGenerator get methods."""

    @pytest.mark.asyncio
    async def test_get_existing_report(self, report_generator, temp_db):
        """Test get() retrieves an existing report."""
        execution_id = "test-exec-get"
        correlation_id = await _create_test_execution(temp_db, execution_id)
        await _complete_execution(temp_db, execution_id, "success")
        
        await report_generator.generate(execution_id)
        
        report = await report_generator.get(execution_id)
        
        assert report is not None
        assert report.execution_id == execution_id
        assert report.correlation_id == correlation_id

    @pytest.mark.asyncio
    async def test_get_nonexistent_report(self, report_generator):
        """Test get() returns None for non-existent report."""
        report = await report_generator.get("nonexistent")
        assert report is None

    @pytest.mark.asyncio
    async def test_get_latest(self, report_generator, temp_db):
        """Test get_latest() returns reports in descending order."""
        # Create multiple executions
        for i in range(3):
            exec_id = f"test-exec-latest-{i}"
            await _create_test_execution(temp_db, exec_id)
            await _complete_execution(temp_db, exec_id, "success")
            await report_generator.generate(exec_id)
        
        reports = await report_generator.get_latest(limit=2)
        
        assert len(reports) == 2
        # Should be ordered by created_at DESC (latest first)
        assert reports[0].execution_id == "test-exec-latest-2"
        assert reports[1].execution_id == "test-exec-latest-1"


class TestExecutionReportModel:
    """Test ExecutionReport model."""

    def test_to_dict(self):
        """Test to_dict() serialization."""
        report = ExecutionReport(
            execution_id="exec-1",
            correlation_id="corr-1",
            capability_id="test.cap",
            workflow_id=None,
            status="success",
            started_at=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            completed_at=datetime(2024, 1, 1, 12, 0, 1, tzinfo=timezone.utc),
            duration_ms=1000,
            evidence_count=1,
            knowledge_count=2,
            pattern_count=1,
            recommendation_count=1,
            approval_status="approved",
            summary={"result": "ok"},
            raw_events=[{"type": "test"}],
        )
        
        data = report.to_dict()
        
        assert data["execution_id"] == "exec-1"
        assert data["correlation_id"] == "corr-1"
        assert data["status"] == "success"
        assert data["duration_ms"] == 1000
        assert data["evidence_count"] == 1
        assert data["approval_status"] == "approved"
        assert data["summary"] == {"result": "ok"}
        assert data["raw_events"] == [{"type": "test"}]

    def test_get_summary(self):
        """Test get_summary() returns ReportSummary."""
        report = ExecutionReport(
            execution_id="exec-1",
            correlation_id="corr-1",
            capability_id="test.cap",
            workflow_id="wf-1",
            status="success",
            started_at=datetime.now(timezone.utc),
            completed_at=datetime.now(timezone.utc),
            duration_ms=100,
            evidence_count=5,
            knowledge_count=3,
            pattern_count=2,
            recommendation_count=1,
            approval_status="approved",
            summary={"key": "value"},
        )
        
        summary = report.get_summary()
        
        assert summary.capability_id == "test.cap"
        assert summary.correlation_id == "corr-1"
        assert summary.workflow_id == "wf-1"
        assert summary.status == "success"
        assert summary.total_evidence == 5
        assert summary.total_knowledge == 3
        assert summary.total_patterns == 2
        assert summary.total_recommendations == 1
        assert summary.approval_status == "approved"
        assert summary.metadata == {"key": "value"}