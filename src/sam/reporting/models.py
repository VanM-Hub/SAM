"""Execution Report Models for Structured Execution Reporting (Tugas 9.5)."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class ReportSummary:
    """Lightweight summary for listing reports."""

    capability_id: str
    correlation_id: str
    workflow_id: Optional[str]
    status: str
    total_evidence: int = 0
    total_knowledge: int = 0
    total_patterns: int = 0
    total_recommendations: int = 0
    approval_status: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ExecutionReport:
    """Complete structured execution report."""

    execution_id: str
    correlation_id: str
    capability_id: str
    workflow_id: Optional[str]
    status: str
    started_at: datetime
    completed_at: datetime
    duration_ms: int
    evidence_count: int = 0
    knowledge_count: int = 0
    pattern_count: int = 0
    recommendation_count: int = 0
    approval_status: Optional[str] = None
    summary: Dict[str, Any] = field(default_factory=dict)
    raw_events: Optional[List[Dict[str, Any]]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "execution_id": self.execution_id,
            "correlation_id": self.correlation_id,
            "capability_id": self.capability_id,
            "workflow_id": self.workflow_id,
            "status": self.status,
            "started_at": self.started_at.isoformat() if isinstance(self.started_at, datetime) else self.started_at,
            "completed_at": self.completed_at.isoformat() if isinstance(self.completed_at, datetime) else self.completed_at,
            "duration_ms": self.duration_ms,
            "evidence_count": self.evidence_count,
            "knowledge_count": self.knowledge_count,
            "pattern_count": self.pattern_count,
            "recommendation_count": self.recommendation_count,
            "approval_status": self.approval_status,
            "summary": self.summary,
            "raw_events": self.raw_events,
        }

    def get_summary(self) -> ReportSummary:
        """Get a ReportSummary from this execution report."""
        return ReportSummary(
            capability_id=self.capability_id,
            correlation_id=self.correlation_id,
            workflow_id=self.workflow_id,
            status=self.status,
            total_evidence=self.evidence_count,
            total_knowledge=self.knowledge_count,
            total_patterns=self.pattern_count,
            total_recommendations=self.recommendation_count,
            approval_status=self.approval_status,
            metadata=self.summary,
        )