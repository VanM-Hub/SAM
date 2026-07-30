"""Dashboard Readiness Bridge — 5 immutable cards."""

from dataclasses import dataclass, field
from typing import Any, Dict, List

from sam.operational_brain.operational_context import OperationalContext
from sam.operational_brain.readiness_checker import ReadinessChecker, ReadinessStatus


@dataclass(frozen=True)
class ReadinessCard:
    """Kartu dashboard readiness — immutable."""
    title: str
    value: Any
    card_type: str = "readiness"
    metadata: Dict[str, Any] = field(default_factory=dict)


class DashboardReadiness:
    """Dashboard 5 kartu immutable untuk readiness."""

    def __init__(self, checker: ReadinessChecker = None):
        self._checker = checker or ReadinessChecker()
        self.card_count = 5

    def _overall_card(self, ctx: OperationalContext) -> ReadinessCard:
        r = self._checker.check_all(ctx)
        return ReadinessCard(
            title="Overall Readiness",
            value={
                "score": round(r.overall_score, 4),
                "status": r.overall_status.name,
                "summary": r.summary,
            },
            card_type="overall",
        )

    def _checks_card(self, ctx: OperationalContext) -> ReadinessCard:
        r = self._checker.check_all(ctx)
        return ReadinessCard(
            title="Check Results",
            value={"passed": r.passed, "total": r.total},
            card_type="checks",
        )

    def _score_card(self, ctx: OperationalContext) -> ReadinessCard:
        r = self._checker.check_all(ctx)
        scores = {c.check_id: c.score for c in r.checks}
        return ReadinessCard(
            title="Scores",
            value=scores,
            card_type="scores",
        )

    def _critical_issues(self, ctx: OperationalContext) -> ReadinessCard:
        r = self._checker.check_all(ctx)
        issues = [
            {"check_id": c.check_id, "message": c.message}
            for c in r.checks
            if c.status in (ReadinessStatus.BLOCKED, ReadinessStatus.UNKNOWN)
        ]
        return ReadinessCard(
            title="Critical Issues",
            value=issues,
            card_type="issues",
        )

    def _category_card(self, ctx: OperationalContext) -> ReadinessCard:
        categories = self._checker.categories
        return ReadinessCard(
            title="Categories",
            value=categories,
            card_type="categories",
        )

    def get_cards(self, ctx: OperationalContext) -> List[ReadinessCard]:
        return [
            self._overall_card(ctx),
            self._checks_card(ctx),
            self._score_card(ctx),
            self._critical_issues(ctx),
            self._category_card(ctx),
        ]
