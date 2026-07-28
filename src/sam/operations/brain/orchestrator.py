"""
OP-255 — Mission Orchestrator.

Orchestrates the complete Brain pipeline:
  Scheduler -> Observation -> Rules -> Analyzer -> Correlation
  -> Priority -> Recommendation -> Proposal

Sequential, deterministic, synchronous pipeline.
If any stage fails, the pipeline stops with an Error DTO.
Does NOT skip stages.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .observation_engine import ObservationEngine, ObservationSnapshot
from .rule_engine import RuleEngine, TriggeredRule
from .analyzer import OperationalAnalyzer, OperationalFinding
from .correlation import CorrelationEngine, CorrelatedFinding
from .priority import PriorityEngine, PriorityScore
from .recommendation import RecommendationBuilder, MissionRecommendation
from .proposal import ProposalService, MissionProposal


@dataclass
class OrchestratorConfig:
    """Configuration for the orchestrator pipeline."""

    enabled: bool = True
    auto_observe: bool = True
    run_rules: bool = True
    run_analysis: bool = True
    run_correlation: bool = True
    run_priority: bool = True
    run_recommendation: bool = True
    run_proposal: bool = True
    max_findings: int = 50
    max_recommendations: int = 20


@dataclass
class OperationalPackage:
    """Complete result of one pipeline run."""

    timestamp: float
    sequence: int

    # Pipeline stages
    snapshot: Optional[ObservationSnapshot] = None
    triggered_rules: List[TriggeredRule] = field(default_factory=list)
    findings: List[OperationalFinding] = field(default_factory=list)
    correlations: List[CorrelatedFinding] = field(default_factory=list)
    priorities: List[PriorityScore] = field(default_factory=list)
    recommendations: List[MissionRecommendation] = field(default_factory=list)
    proposals: List[MissionProposal] = field(default_factory=list)

    # Status
    success: bool = True
    error: Optional[str] = None
    failed_stage: Optional[str] = None

    @property
    def finding_count(self) -> int:
        return len(self.findings)

    @property
    def triggered_count(self) -> int:
        return len(self.triggered_rules)

    @property
    def correlation_count(self) -> int:
        return len(self.correlations)

    @property
    def recommendation_count(self) -> int:
        return len(self.recommendations)

    @property
    def proposal_count(self) -> int:
        return len(self.proposals)

    def __repr__(self) -> str:
        return (
            f"OperationalPackage(seq={self.sequence}, "
            f"ok={self.success}, "
            f"findings={self.finding_count}, "
            f"recs={self.recommendation_count})"
        )


class MissionOrchestrator:
    """Runs the full Brain pipeline sequentially.

    Each stage runs if:
      1. The stage is enabled in config, AND
      2. The previous stage succeeded.

    If a stage fails, pipeline stops and error is recorded.
    Orchestrator is stateless — each run produces a fresh OperationalPackage.
    """

    def __init__(
        self,
        config: Optional[OrchestratorConfig] = None,
    ) -> None:
        self._config = config or OrchestratorConfig()
        self._sequence = 0
        self._last_package: Optional[OperationalPackage] = None
        self._running = False

        # Lazily initialized components
        self._observation_engine: Optional[ObservationEngine] = None
        self._rule_engine: Optional[RuleEngine] = None
        self._analyzer: Optional[OperationalAnalyzer] = None
        self._correlation_engine: Optional[CorrelationEngine] = None
        self._priority_engine: Optional[PriorityEngine] = None
        self._recommendation_builder: Optional[RecommendationBuilder] = None
        self._proposal_service: Optional[ProposalService] = None

    @property
    def config(self) -> OrchestratorConfig:
        return self._config

    @property
    def last_package(self) -> Optional[OperationalPackage]:
        return self._last_package

    @property
    def is_running(self) -> bool:
        return self._running

    # ── Component accessors (lazy init) ────────────────────────────

    def _get_observation_engine(self) -> ObservationEngine:
        if self._observation_engine is None:
            self._observation_engine = ObservationEngine()
        return self._observation_engine

    def _get_rule_engine(self) -> RuleEngine:
        if self._rule_engine is None:
            self._rule_engine = RuleEngine()
        return self._rule_engine

    def _get_analyzer(self) -> OperationalAnalyzer:
        if self._analyzer is None:
            self._analyzer = OperationalAnalyzer()
        return self._analyzer

    def _get_correlation_engine(self) -> CorrelationEngine:
        if self._correlation_engine is None:
            self._correlation_engine = CorrelationEngine()
        return self._correlation_engine

    def _get_priority_engine(self) -> PriorityEngine:
        if self._priority_engine is None:
            self._priority_engine = PriorityEngine()
        return self._priority_engine

    def _get_recommendation_builder(self) -> RecommendationBuilder:
        if self._recommendation_builder is None:
            self._recommendation_builder = RecommendationBuilder()
        return self._recommendation_builder

    def _get_proposal_service(self) -> ProposalService:
        if self._proposal_service is None:
            self._proposal_service = ProposalService()
        return self._proposal_service

    # ── Pipeline execution ─────────────────────────────────────────

    def orchestrate(
        self,
        skip_proposals: bool = False,
    ) -> OperationalPackage:
        """Run the full pipeline.

        Args:
            skip_proposals: If True, stops after recommendations
                            (useful for preview mode).

        Returns:
            OperationalPackage with all stage results.
        """
        self._sequence += 1
        self._running = True
        pkg = OperationalPackage(
            timestamp=time.time(),
            sequence=self._sequence,
        )

        try:
            # Stage 1: Observation
            if self._config.auto_observe:
                engine = self._get_observation_engine()
                pkg.snapshot = engine.collect()
            else:
                pkg.error = "Observation disabled in config"
                pkg.failed_stage = "observation"
                pkg.success = False
                self._last_package = pkg
                self._running = False
                return pkg

            # Stage 2: Rules
            if self._config.run_rules:
                rule_eng = self._get_rule_engine()
                pkg.triggered_rules = rule_eng.evaluate(pkg.snapshot)
            else:
                pkg.triggered_rules = []

            # Stage 3: Analysis
            if self._config.run_analysis:
                analyzer = self._get_analyzer()
                rules = pkg.triggered_rules
                pkg.findings = analyzer.analyze(pkg.snapshot, rules)
                # Cap findings
                if len(pkg.findings) > self._config.max_findings:
                    pkg.findings = pkg.findings[:self._config.max_findings]

            # Stage 4: Correlation
            if self._config.run_correlation and pkg.findings:
                corr = self._get_correlation_engine()
                pkg.correlations = corr.correlate(pkg.findings)

            # Stage 5: Priority
            if self._config.run_priority and pkg.findings:
                pri = self._get_priority_engine()
                pkg.priorities = pri.prioritize(pkg.findings)

            # Stage 6: Recommendation
            if self._config.run_recommendation and pkg.findings:
                rec = self._get_recommendation_builder()
                recommendations = rec.build(pkg.findings)
                if len(recommendations) > self._config.max_recommendations:
                    # Keep highest priority ones
                    priority_map = {s.finding_id: s for s in pkg.priorities}
                    recommendations.sort(
                        key=lambda r: priority_map.get(
                            r.source_finding_id, PriorityScore(
                                finding_id="", score=0,
                                category="info"  # type: ignore
                            )
                        ).score,
                        reverse=True,
                    )
                    recommendations = recommendations[:self._config.max_recommendations]
                pkg.recommendations = recommendations

            # Stage 7: Proposal
            if not skip_proposals and self._config.run_proposal and pkg.recommendations:
                prop = self._get_proposal_service()
                pkg.proposals = [
                    prop.create_proposal(rec)
                    for rec in pkg.recommendations
                ]

            pkg.success = True

        except Exception as e:
            pkg.success = False
            pkg.error = str(e)
            pkg.failed_stage = self._last_stage(pkg)

        self._last_package = pkg
        self._running = False
        return pkg

    @staticmethod
    def _last_stage(pkg: OperationalPackage) -> str:
        """Determine which stage was running when error occurred."""
        if pkg.recommendations:
            return "proposal"
        if pkg.findings:
            return "recommendation"
        if pkg.triggered_rules:
            return "analysis"
        if pkg.snapshot:
            return "rules"
        return "observation"

    def stop(self) -> None:
        """Signal the orchestrator to stop (if running)."""
        self._running = False


# ── Convenience ───────────────────────────────────────────────────────


def auto_orchestrate(
    config: Optional[OrchestratorConfig] = None,
) -> OperationalPackage:
    """One-shot: run the full pipeline."""
    return MissionOrchestrator(config=config).orchestrate()
