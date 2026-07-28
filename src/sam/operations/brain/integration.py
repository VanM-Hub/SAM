"""
OP-248 — Operational Brain Integration.

Wires the full pipeline together:

  Observation → Rules → Analyzer → Recommendation → Proposal → Dashboard DTO

No auto-execution. All decisions through existing pipelines.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from .observation_engine import ObservationEngine, ObservationSnapshot
from .rule_engine import RuleEngine, TriggeredRule
from .analyzer import OperationalAnalyzer, OperationalFinding
from .recommendation import RecommendationBuilder, MissionRecommendation
from .proposal import ProposalService, MissionProposal
from .conversation import BrainConversationBridge
from .dashboard import BrainDashboardData, build_dashboard_data


class BrainPipeline:
    """End-to-end operational brain pipeline.

    Usage:
        pipeline = BrainPipeline()
        result = pipeline.run()
        # result contains dashboard DTO + new proposals
    """

    def __init__(self) -> None:
        self.observation_engine = ObservationEngine()
        self.rule_engine = RuleEngine()
        self.analyzer = OperationalAnalyzer()
        self.recommendation_builder = RecommendationBuilder()
        self.proposal_service = ProposalService()
        self.conversation_bridge = BrainConversationBridge()

        # Last run results
        self._last_snapshot: Optional[ObservationSnapshot] = None
        self._last_rules: List[TriggeredRule] = []
        self._last_findings: List[OperationalFinding] = []
        self._last_recommendations: List[MissionRecommendation] = []
        self._last_proposals: List[MissionProposal] = []
        self._last_dashboard: Optional[BrainDashboardData] = None

    def run(self) -> BrainPipelineResult:
        """Execute full pipeline once.

        Pipeline stops at Proposal — nothing auto-executes.
        """
        # 1. Observe
        snapshot = self.observation_engine.collect()
        self._last_snapshot = snapshot

        # 2. Evaluate rules
        triggered = self.rule_engine.evaluate(snapshot)
        self._last_rules = triggered

        # 3. Analyze
        findings = self.analyzer.analyze(snapshot, triggered)
        self._last_findings = findings

        # 4. Build recommendations
        recommendations = self.recommendation_builder.build(findings)
        self._last_recommendations = recommendations

        # 5. Create proposals (but do NOT submit)
        proposals = []
        for rec in recommendations:
            proposal = self.proposal_service.create_proposal(rec)
            proposals.append(proposal)
        self._last_proposals = proposals

        # 6. Build dashboard DTO
        dashboard = build_dashboard_data(
            findings=findings,
            recommendations=recommendations,
            observation=snapshot,
            rules=triggered,
        )
        self._last_dashboard = dashboard

        # 7. Update conversation bridge
        self.conversation_bridge.set_state(
            findings=dashboard.findings,
            recommendations=dashboard.recommendations,
            observation=dashboard.observation_summary,
            rules=dashboard.triggered_rules,
            health_score=dashboard.health_score,
        )

        return BrainPipelineResult(
            snapshot=snapshot,
            triggered_rules=triggered,
            findings=findings,
            recommendations=recommendations,
            proposals=proposals,
            dashboard=dashboard,
        )

    # ── Properties ──────────────────────────────────────────────────

    @property
    def last_snapshot(self) -> Optional[ObservationSnapshot]:
        return self._last_snapshot

    @property
    def last_dashboard(self) -> Optional[BrainDashboardData]:
        return self._last_dashboard

    @property
    def last_findings(self) -> List[OperationalFinding]:
        return list(self._last_findings)

    @property
    def last_recommendations(self) -> List[MissionRecommendation]:
        return list(self._last_recommendations)

    @property
    def last_proposals(self) -> List[MissionProposal]:
        return list(self._last_proposals)


class BrainPipelineResult:
    """Result of a single pipeline run."""

    def __init__(
        self,
        snapshot: ObservationSnapshot,
        triggered_rules: List[TriggeredRule],
        findings: List[OperationalFinding],
        recommendations: List[MissionRecommendation],
        proposals: List[MissionProposal],
        dashboard: BrainDashboardData,
    ) -> None:
        self.snapshot = snapshot
        self.triggered_rules = triggered_rules
        self.findings = findings
        self.recommendations = recommendations
        self.proposals = proposals
        self.dashboard = dashboard


def run_pipeline() -> BrainPipelineResult:
    """One-shot convenience."""
    return BrainPipeline().run()


def run_and_summarize() -> Dict[str, Any]:
    """Run pipeline and return plain dict summary."""
    result = BrainPipeline().run()
    return {
        "observation": {
            "active_missions": result.snapshot.active_missions,
            "failed_missions": result.snapshot.failed_missions,
            "pending_approvals": result.snapshot.pending_approvals,
            "locks": result.snapshot.locks_held,
            "queue": result.snapshot.queue_length,
        },
        "rules_triggered": len(result.triggered_rules),
        "findings": len(result.findings),
        "recommendations": len(result.recommendations),
        "proposals": len(result.proposals),
        "health_score": result.dashboard.health_score,
        "health_state": result.dashboard.health_state,
    }
