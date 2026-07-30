"""
Approval Summary Builder.

Builds human-readable summaries for approval packages.
Deterministic. DTO only.
"""

from typing import Dict, Any

from .approval_preparation import ApprovalPreparation, ApprovalCandidate


class ApprovalSummaryBuilder:
    """Builds approval summaries."""

    def build(self, prep: ApprovalPreparation) -> Dict[str, Any]:
        """Build a complete summary dict."""
        metadata = prep.metadata

        return {
            "preparation_id": prep.preparation_id,
            "ready": prep.ready_for_submission,
            "decision": {
                "risk": "HIGH" if not prep.ready_for_submission else "LOW",
                "confidence": self._avg_confidence(prep.candidates),
                "readiness": "READY" if prep.ready_for_submission else "NOT_READY",
            },
            "strategy": metadata.strategy_approach if metadata else "unknown",
            "constraints": {
                "total_requirements": len(prep.requirements),
                "satisfied": sum(1 for r in prep.requirements if r.satisfied),
            },
            "justification": prep.summary,
            "recommendation": self._recommendation(prep),
        }

    def _avg_confidence(self, candidates: list) -> float:
        if not candidates:
            return 0.0
        return sum(c.confidence for c in candidates) / len(candidates)

    def _recommendation(self, prep: ApprovalPreparation) -> str:
        if prep.ready_for_submission:
            return "Ready for approval submission"
        missing = [r.name for r in prep.requirements if not r.satisfied]
        return f"Not ready. Missing: {', '.join(missing)}" if missing else "Not ready"
