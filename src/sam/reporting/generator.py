"""Report Generator for Structured Execution Reporting (Tugas 9.5)."""

import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sam.persistence.database import Database
from sam.events.event_bus import EventBus
from sam.reporting.models import ExecutionReport, ReportSummary


class ReportGenerator:
    """Generates and manages structured execution reports."""

    def __init__(self, db: Database, event_bus: EventBus):
        self.db = db
        self.event_bus = event_bus

    async def generate(self, execution_id: str) -> ExecutionReport:
        """Generate a complete execution report for the given execution_id."""
        # Fetch execution record
        exec_row = await self.db.fetch_one(
            "SELECT * FROM executions WHERE id = ?", [execution_id]
        )
        if not exec_row:
            raise ValueError(f"Execution not found: {execution_id}")

        correlation_id = exec_row.get("correlation_id") or ""
        capability_id = exec_row.get("capability_id") or ""
        workflow_id = exec_row.get("workflow_id")
        status = exec_row.get("status") or "unknown"
        started_at = exec_row.get("started_at")
        completed_at = exec_row.get("completed_at")

        # Calculate duration
        duration_ms = 0
        if started_at and completed_at:
            try:
                start_dt = datetime.fromisoformat(started_at.replace("Z", "+00:00"))
                end_dt = datetime.fromisoformat(completed_at.replace("Z", "+00:00"))
                duration_ms = int((end_dt - start_dt).total_seconds() * 1000)
            except Exception:
                pass

        # Count related records - use correct columns per table schema
        evidence_count = await self._count("evidence", "execution_id", execution_id)
        # knowledge, patterns, recommendations only have correlation_id, not execution_id
        knowledge_count = await self._count("knowledge", "correlation_id", correlation_id)
        pattern_count = await self._count("patterns", "correlation_id", correlation_id)
        recommendation_count = await self._count("recommendations", "correlation_id", correlation_id)

        # Get approval status if any (guard against older schemas missing execution_id)
        approval_status = None
        try:
            approval_row = await self.db.fetch_one(
                "SELECT status FROM approvals WHERE execution_id = ? ORDER BY created_at DESC LIMIT 1",
                [execution_id]
            )
            approval_status = approval_row["status"] if approval_row else None
        except Exception:
            # Older DB schema may not have execution_id on approvals; ignore and continue
            approval_status = None

        # Build summary
        summary = {
            "inputs": exec_row.get("inputs", "{}"),
            "result": exec_row.get("result", "{}"),
            "error": exec_row.get("error"),
        }

        report = ExecutionReport(
            execution_id=execution_id,
            correlation_id=correlation_id,
            capability_id=capability_id,
            workflow_id=workflow_id,
            status=status,
            started_at=datetime.fromisoformat(started_at.replace("Z", "+00:00")) if started_at else datetime.now(timezone.utc),
            completed_at=datetime.fromisoformat(completed_at.replace("Z", "+00:00")) if completed_at else datetime.now(timezone.utc),
            duration_ms=duration_ms,
            evidence_count=evidence_count,
            knowledge_count=knowledge_count,
            pattern_count=pattern_count,
            recommendation_count=recommendation_count,
            approval_status=approval_status,
            summary=summary,
            raw_events=None,  # Could be populated from event store if needed
        )

        # Save to database
        await self.save(report)
        return report

    async def _count(self, table: str, column: str, value: str) -> int:
        """Count rows in a table where column = value."""
        try:
            row = await self.db.fetch_one(
                f"SELECT COUNT(*) as cnt FROM {table} WHERE {column} = ?",
                [value]
            )
            return row["cnt"] if row else 0
        except Exception:
            return 0

    async def save(self, report: ExecutionReport) -> None:
        """Save report to database."""
        import json
        await self.db.execute(
            """
            INSERT OR REPLACE INTO reports (
                execution_id, correlation_id, capability_id, workflow_id, status,
                started_at, completed_at, duration_ms, evidence_count, knowledge_count,
                pattern_count, recommendation_count, approval_status, summary, raw_events
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                report.execution_id,
                report.correlation_id,
                report.capability_id,
                report.workflow_id,
                report.status,
                report.started_at.isoformat(),
                report.completed_at.isoformat(),
                report.duration_ms,
                report.evidence_count,
                report.knowledge_count,
                report.pattern_count,
                report.recommendation_count,
                report.approval_status,
                json.dumps(report.summary),
                json.dumps(report.raw_events) if report.raw_events else None,
            ]
        )

    async def get(self, execution_id: str) -> Optional[ExecutionReport]:
        """Get a report by execution_id."""
        row = await self.db.fetch_one(
            "SELECT * FROM reports WHERE execution_id = ?", [execution_id]
        )
        if not row:
            return None
        return self._row_to_report(row)

    async def get_latest(self, limit: int = 10) -> List[ExecutionReport]:
        """Get the latest reports."""
        rows = await self.db.fetch_all(
            "SELECT * FROM reports ORDER BY created_at DESC LIMIT ?", [limit]
        )
        return [self._row_to_report(row) for row in rows]

    def _row_to_report(self, row: Dict[str, Any]) -> ExecutionReport:
        """Convert database row to ExecutionReport."""
        import json
        return ExecutionReport(
            execution_id=row["execution_id"],
            correlation_id=row["correlation_id"],
            capability_id=row["capability_id"],
            workflow_id=row.get("workflow_id"),
            status=row["status"],
            started_at=datetime.fromisoformat(row["started_at"].replace("Z", "+00:00")),
            completed_at=datetime.fromisoformat(row["completed_at"].replace("Z", "+00:00")),
            duration_ms=row["duration_ms"],
            evidence_count=row["evidence_count"],
            knowledge_count=row["knowledge_count"],
            pattern_count=row["pattern_count"],
            recommendation_count=row["recommendation_count"],
            approval_status=row.get("approval_status"),
            summary=json.loads(row["summary"]) if row.get("summary") else {},
            raw_events=json.loads(row["raw_events"]) if row.get("raw_events") else None,
        )

    async def export_markdown(self, report: ExecutionReport) -> str:
        """Export report as Markdown."""
        lines = [
            f"# Execution Report: {report.execution_id}",
            "",
            "## Overview",
            f"- **Execution ID**: {report.execution_id}",
            f"- **Correlation ID**: {report.correlation_id}",
            f"- **Capability ID**: {report.capability_id}",
            f"- **Workflow ID**: {report.workflow_id or 'N/A'}",
            f"- **Status**: {report.status}",
            f"- **Started**: {report.started_at.isoformat()}",
            f"- **Completed**: {report.completed_at.isoformat()}",
            f"- **Duration**: {report.duration_ms} ms",
            "",
            "## Counts",
            f"- **Evidence**: {report.evidence_count}",
            f"- **Knowledge Facts**: {report.knowledge_count}",
            f"- **Patterns Detected**: {report.pattern_count}",
            f"- **Recommendations**: {report.recommendation_count}",
            f"- **Approval Status**: {report.approval_status or 'N/A'}",
            "",
            "## Summary",
        ]
        for key, value in report.summary.items():
            lines.append(f"- **{key}**: {value}")
        
        if report.raw_events:
            lines.extend([
                "",
                "## Raw Events (Debug)",
                "```json",
                json.dumps(report.raw_events, indent=2),
                "```"
            ])
        
        return "\n".join(lines)

    async def export_json(self, report: ExecutionReport) -> str:
        """Export report as JSON."""
        return json.dumps(report.to_dict(), indent=2)