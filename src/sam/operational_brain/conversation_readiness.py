"""Conversation Readiness Bridge — 5 query read-only."""

from typing import Any, Dict, List

from sam.operational_brain.operational_context import OperationalContext
from sam.operational_brain.readiness_checker import (
    ReadinessChecker,
    ReadinessReport,
    ReadinessStatus,
)


class ConversationReadiness:
    """Conversation bridge untuk readiness checks."""

    def __init__(self, checker: ReadinessChecker = None):
        self._checker = checker or ReadinessChecker()

    @property
    def query_count(self) -> int:
        return 5

    def query_readiness_summary(self, ctx: OperationalContext) -> Dict[str, Any]:
        report = self._checker.check_all(ctx)
        return {
            "overall_score": round(report.overall_score, 4),
            "overall_status": report.overall_status.name,
            "summary": report.summary,
            "passed": report.passed,
            "total": report.total,
        }

    def query_readiness_detail(self, ctx: OperationalContext) -> List[Dict[str, Any]]:
        report = self._checker.check_all(ctx)
        return [
            {
                "check_id": c.check_id,
                "name": c.name,
                "passed": c.passed,
                "score": c.score,
                "status": c.status.name,
                "message": c.message,
            }
            for c in report.checks
        ]

    def query_failed_checks(self, ctx: OperationalContext) -> List[Dict[str, Any]]:
        report = self._checker.check_all(ctx)
        return [
            {
                "check_id": c.check_id,
                "name": c.name,
                "score": c.score,
                "status": c.status.name,
                "message": c.message,
            }
            for c in report.checks
            if not c.passed
        ]

    def query_by_status(self, ctx: OperationalContext, status_name: str) -> List[Dict[str, Any]]:
        report = self._checker.check_all(ctx)
        return [
            {"check_id": c.check_id, "name": c.name, "score": c.score, "message": c.message}
            for c in report.checks
            if c.status.name == status_name
        ]

    def query_categories(self) -> List[str]:
        return self._checker.categories
