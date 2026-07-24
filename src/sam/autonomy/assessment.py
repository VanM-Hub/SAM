"""Self-Assessment — Sprint 32.

Evaluates autonomous actions before and after execution.
Provides confidence scores and risk estimates for each action.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import structlog

logger = structlog.get_logger()


@dataclass
class AssessmentResult:
    """Result of a self-assessment evaluation.

    Attributes:
        id: Unique assessment ID.
        action_id: ID of the assessed action.
        phase: "before" or "after".
        confidence: Confidence in this action (0.0–100.0).
        risk: Estimated risk (0.0–1.0).
        expected_impact: Expected impact description.
        issues: List of potential issues found.
        recommendation: What to do (proceed, cautious, abort).
        timestamp: When assessed.
    """
    id: str = ""
    action_id: str = ""
    phase: str = "before"
    confidence: float = 100.0
    risk: float = 0.0
    expected_impact: str = ""
    issues: List[str] = field(default_factory=list)
    recommendation: str = "proceed"
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self) -> None:
        if not self.id:
            object.__setattr__(self, "id", f"ar_{uuid.uuid4().hex[:12]}")

    @property
    def should_proceed(self) -> bool:
        return self.recommendation != "abort"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "action_id": self.action_id,
            "phase": self.phase,
            "confidence": self.confidence,
            "risk": self.risk,
            "expected_impact": self.expected_impact,
            "issues": self.issues,
            "recommendation": self.recommendation,
            "timestamp": self.timestamp.isoformat(),
        }


class SelfAssessment:
    """Evaluates autonomous actions before and after execution."""

    def __init__(self) -> None:
        self._assessments: List[AssessmentResult] = []
        self.logger = logger.bind(component="SelfAssessment")

    async def assess_before(self, action: Dict[str, Any]) -> AssessmentResult:
        """Assess an action before execution.

        Evaluates confidence, risk, and potential issues based on
        action parameters and current context.
        """
        issues = []

        # Check for known risk factors
        risk_score = float(action.get("risk", 0.0))
        action_type = action.get("type", "unknown")

        if risk_score > 0.7:
            issues.append("High risk score detected")
        if action.get("resource_estimate", 0) > 80:
            issues.append("High resource consumption expected")
        if action_type in ("deploy", "destroy", "reconfigure"):
            issues.append(f"Destructive action type: {action_type}")

        # Compute confidence inversely proportional to issues
        base_conf = 100.0 - (risk_score * 50)
        conf_penalty = len(issues) * 10
        confidence = max(0, base_conf - conf_penalty)

        # Recommendation
        if risk_score > 0.8 or confidence < 30:
            recommendation = "abort"
        elif risk_score > 0.5 or len(issues) > 2:
            recommendation = "cautious"
        else:
            recommendation = "proceed"

        result = AssessmentResult(
            action_id=action.get("id", ""),
            phase="before",
            confidence=round(confidence, 1),
            risk=risk_score,
            expected_impact=action.get("expected_impact", "unknown"),
            issues=issues,
            recommendation=recommendation,
        )
        self._assessments.append(result)
        return result

    async def assess_after(
        self,
        action: Dict[str, Any],
        result: Dict[str, Any],
    ) -> AssessmentResult:
        """Assess an action after execution.

        Compares expected vs actual outcome.
        """
        success = result.get("success", True)
        issues = []

        if not success:
            issues.append("Action failed")

        duration = result.get("duration_ms", 0)
        expected_duration = action.get("expected_duration_ms", 0)
        if expected_duration > 0 and duration > expected_duration * 2:
            issues.append(f"Action took {duration}ms, expected {expected_duration}ms (2x over)")

        confidence = 100.0 if success else 50.0
        confidence -= len(issues) * 15
        confidence = max(0, confidence)

        assessment = AssessmentResult(
            action_id=action.get("id", ""),
            phase="after",
            confidence=round(confidence, 1),
            risk=result.get("risk", 0.0),
            expected_impact=action.get("expected_impact", ""),
            issues=issues,
            recommendation="proceed" if success else "cautious",
        )
        self._assessments.append(assessment)
        return assessment

    async def get_assessment_history(self, limit: int = 50) -> List[AssessmentResult]:
        history = list(self._assessments)
        history.reverse()
        return history[:limit]

    async def clear(self) -> None:
        self._assessments.clear()
