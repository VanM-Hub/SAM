"""
OP-259 — Integration.

Final pipeline for Sprint 20 — Proactive Mission Orchestration.

Pipeline sequence:
  1. Observation (scheduler + multi-source)
  2. Correlation (engine)
  3. Analyzer (existing)
  4. Priority (engine)
  5. Recommendation (existing)
  6. Mission Orchestrator
  7. Proposal Queue
  8. Health Engine
  9. Conversation DTO

All components output DTOs. No auto-execution. All proposals require approval.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from sam.operations.brain.multi_source import (
    MultiSourceObserver,
    MultiSourceSnapshot,
)
from sam.operations.brain.correlation import (
    CorrelationEngine,
    CorrelatedFinding,
    build_finding_dict,
)
from sam.operations.brain.analyzer import (
    OperationalAnalyzer,
    OperationalFinding,
    Severity,
    analyze,
)
from sam.operations.brain.priority import (
    PriorityEngine,
    PriorityScore,
    PriorityConfig,
)
from sam.operations.brain.recommendation import (
    RecommendationBuilder,
    MissionRecommendation,
    build_recommendations,
)
from sam.operations.brain.orchestrator import (
    MissionOrchestrator,
    OperationalPackage,
    OrchestratorConfig,
)
from sam.operations.brain.proposal_queue import (
    ProposalQueue,
    QueueItem,
    ProposalState,
)
from sam.operations.brain.health import (
    OperationalHealthEngine,
    OperationalHealthDTO,
    evaluate_health,
)
from sam.operations.brain.conversation_v2 import (
    BrainConversationBridgeV2,
    ConversationContext,
    BrainAnswer,
)

# Re-export for convenience
from sam.operations.brain.observation_engine import ObservationSnapshot


# ── Pipeline Result ────────────────────────────────────────────────


@dataclass
class ProactivePipelineResult:
    """
    Complete result of the proactive pipeline run.

    All fields are DTO-safe (dicts/lists/primitives).
    """

    snapshot: MultiSourceSnapshot
    findings: List[Dict[str, Any]]
    correlated_findings: List[Dict[str, Any]]
    priority_scores: List[Dict[str, Any]]
    recommendations: List[Dict[str, Any]]
    packages: List[Dict[str, Any]]
    proposals: List[Dict[str, Any]]
    health: Optional[Dict[str, Any]]
    conversation: BrainAnswer
    pipeline_timestamp: float
    pipeline_elapsed_ms: float

    def summary(self) -> Dict[str, Any]:
        return {
            "timestamp": self.pipeline_timestamp,
            "elapsed_ms": self.pipeline_elapsed_ms,
            "findings": len(self.findings),
            "correlated": len(self.correlated_findings),
            "recommendations": len(self.recommendations),
            "packages": len(self.packages),
            "proposals": len(self.proposals),
            "health_score": (self.health or {}).get("score", 1.0),
            "health_status": (self.health or {}).get("status", "healthy"),
        }


# ── Pipeline ───────────────────────────────────────────────────────


class ProactivePipeline:
    """
    End-to-end proactive mission orchestration pipeline.

    Run modes:
      - run(): full pipeline
      - observe_only(): collect + correlate (no proposals)
      - health_only(): collect + health score only
    """

    def __init__(
        self,
        default_ttl: float = 3600.0,
    ):
        # Components
        self.observer = MultiSourceObserver()
        self.correlator = CorrelationEngine()
        self.analyzer_backend = OperationalAnalyzer()
        self.prioritizer = PriorityEngine()
        self.recommender = RecommendationBuilder()
        self.orchestrator = MissionOrchestrator()
        self.queue = ProposalQueue(default_ttl=default_ttl)
        self.health_engine = OperationalHealthEngine()
        self.conversation = BrainConversationBridgeV2()

        # State
        self._last_result: Optional[ProactivePipelineResult] = None
        self._last_summary: Optional[Dict[str, Any]] = None

    # ── Public API ─────────────────────────────────────────────────

    @property
    def last_result(self) -> Optional[ProactivePipelineResult]:
        return self._last_result

    @property
    def last_summary(self) -> Optional[Dict[str, Any]]:
        return self._last_summary

    def run(self) -> ProactivePipelineResult:
        """
        Run the full pipeline.

        Sequence:
          1. Collect multi-source observation
          2. Run correlation engine
          3. Analyze findings
          4. Prioritize
          5. Build recommendations
          6. Orchestrate into packages
          7. Push to proposal queue
          8. Evaluate health
          9. Update conversation context
          10. Build answer
        """
        start = time.time()

        # 1. Observe
        snapshot = self.observer.collect()

        # 2. Correlate
        source_data = self._snapshot_to_source_data(snapshot)
        raw_findings = self._build_findings_from_snapshot(snapshot)
        correlated = self.correlator.find_from_finding_list(raw_findings)

        # 3. Analyze
        # Convert raw operating findings into operational findings
        obs_snapshot = self._to_obs_snapshot(snapshot)
        rule_triggered = self._mock_rules(raw_findings)
        findings = analyze(obs_snapshot, rule_triggered)
        finding_dicts = self._findings_to_dicts(findings)

        # 4. Prioritize
        rec_inputs = self._build_recommendation_inputs(finding_dicts)
        scores = self.prioritizer.rank(rec_inputs)

        # 5. Recommend
        recommendations = build_recommendations(findings)
        rec_dicts = self._recs_to_dicts(recommendations)

        # 6. Orchestrate
        score_dicts = [self._score_to_dict(s) for s in scores]
        packages = self.orchestrator.auto_package(rec_dicts, score_dicts)
        package_dicts = self._packages_to_dicts(packages)

        # 7. Proposal Queue
        proposals: List[Dict[str, Any]] = []
        for rec in recommendations[:10]:
            item = self.queue.add(
                title=rec.title,
                description=rec.description[:200],
                evidence=rec.evidence[:5],
                priority_score=rec.confidence,
            )
            self.queue.finalize(item.proposal_id)
            proposals.append(self._queue_item_to_dict(item))

        # 8. Health
        health = self.health_engine.evaluate(source_data)
        health_dict = self._health_to_dict(health)

        # 9. Conversation context
        ctx = ConversationContext(
            findings=finding_dicts,
            recommendations=rec_dicts,
            proposals=proposals,
            correlated_findings=[self._corr_to_dict(c) for c in correlated],
            priority_scores=[self._score_to_dict(s) for s in scores],
            packages=package_dicts,
            health=health_dict,
            observation=snapshot.get_summary(),
            multi_source={
                "sources_ok": snapshot.total_sources_ok,
                "sources_failed": snapshot.total_failures,
            },
        )
        self.conversation.update_context(
            findings=ctx.findings,
            recommendations=ctx.recommendations,
            proposals=ctx.proposals,
            correlated_findings=ctx.correlated_findings,
            priority_scores=ctx.priority_scores,
            packages=ctx.packages,
            health=ctx.health,
            observation=ctx.observation,
        )

        # 10. Answer (default: status)
        answer = self.conversation.ask("status")

        elapsed = (time.time() - start) * 1000

        result = ProactivePipelineResult(
            snapshot=snapshot,
            findings=finding_dicts,
            correlated_findings=ctx.correlated_findings,
            priority_scores=ctx.priority_scores,
            recommendations=rec_dicts,
            packages=package_dicts,
            proposals=proposals,
            health=health_dict,
            conversation=answer,
            pipeline_timestamp=start,
            pipeline_elapsed_ms=round(elapsed, 1),
        )

        self._last_result = result
        self._last_summary = result.summary()
        return result

    def observe_only(self) -> Dict[str, Any]:
        """Quick pipeline: only observe and correlate."""
        snapshot = self.observer.collect()
        raw = self._build_findings_from_snapshot(snapshot)
        correlated = self.correlator.find_from_finding_list(raw)
        health = self.health_engine.evaluate(
            self._snapshot_to_source_data(snapshot)
        )
        return {
            "snapshot": self._snapshot_summary(snapshot),
            "findings": raw,
            "correlated_findings": [self._corr_to_dict(c) for c in correlated],
            "health": self._health_to_dict(health),
        }

    def health_only(self) -> Dict[str, Any]:
        """Quick pipeline: collect and return health score only."""
        snapshot = self.observer.collect()
        health = self.health_engine.evaluate(
            self._snapshot_to_source_data(snapshot)
        )
        return self._health_to_dict(health)

    def ask(self, query: str) -> BrainAnswer:
        """Ask the conversation bridge with current pipeline context."""
        return self.conversation.ask(query)

    # ── Internal converters ────────────────────────────────────────

    def _snapshot_to_source_data(
        self, snapshot: MultiSourceSnapshot
    ) -> Dict[str, Dict[str, Any]]:
        return {
            "missions": snapshot.missions,
            "approvals": snapshot.approvals,
            "timeline": snapshot.timeline,
            "trust": snapshot.trust,
            "audit": snapshot.audit,
            "scheduler": snapshot.scheduler,
            "notification": snapshot.notification,
            "locks": snapshot.locks,
            "health": snapshot.health,
            "replay": snapshot.replay,
            "benchmark": snapshot.benchmark,
        }

    def _build_findings_from_snapshot(
        self, snapshot: MultiSourceSnapshot
    ) -> List[Dict[str, Any]]:
        """Create finding dicts from snapshot data for correlation."""
        findings = []

        m = snapshot.missions
        if m.get("failed", 0) > 0:
            findings.append(build_finding_dict(
                "mission_failure", "warning", 0.7,
                affected_resources=["missions"],
                recommended_actions=["Investigate failed missions"],
            ))

        a = snapshot.approvals
        if a.get("pending", 0) > 3:
            findings.append(build_finding_dict(
                "approval_backlog", "warning", 0.8,
                affected_resources=["approval"],
                recommended_actions=["Review approval queue"],
            ))

        t = snapshot.trust
        if t.get("overall", 1.0) < 0.6:
            findings.append(build_finding_dict(
                "trust_degradation", "critical", 0.85,
                affected_resources=["trust"],
                recommended_actions=["Investigate trust degradation"],
            ))

        tl = snapshot.timeline
        if tl.get("anomalies", 0) > 0:
            findings.append(build_finding_dict(
                "anomaly_cluster", "warning", 0.75,
                affected_resources=["timeline"],
                recommended_actions=["Review anomaly cluster"],
            ))

        s = snapshot.scheduler
        if s.get("queue_length", 0) > 10:
            findings.append(build_finding_dict(
                "queue_stall", "warning", 0.7,
                affected_resources=["scheduler"],
                recommended_actions=["Check scheduler queue"],
            ))

        n = snapshot.notification
        if n.get("error", 0) + n.get("critical", 0) > 0:
            findings.append(build_finding_dict(
                "notification_alert", "warning", 0.7,
                affected_resources=["notification"],
                recommended_actions=["Review critical notifications"],
            ))

        lk = snapshot.locks
        if lk.get("contended", 0) > 0:
            findings.append(build_finding_dict(
                "lock_contention", "warning", 0.65,
                affected_resources=["locks"],
                recommended_actions=["Resolve lock contention"],
            ))

        rp = snapshot.replay
        if rp.get("success_rate", 1.0) < 0.8:
            findings.append(build_finding_dict(
                "replay_degradation", "warning", 0.7,
                affected_resources=["replay"],
                recommended_actions=["Investigate replay failures"],
            ))

        tm = snapshot.timeline
        if tm.get("events_recent", 0) > 100:
            findings.append(build_finding_dict(
                "high_telemetry", "info", 0.5,
                affected_resources=["telemetry"],
                recommended_actions=["Check event rate"],
            ))

        return findings

    def _to_obs_snapshot(self, snapshot: MultiSourceSnapshot) -> ObservationSnapshot:
        """Convert MultiSourceSnapshot to legacy ObservationSnapshot."""
        import time
        return ObservationSnapshot(
            timestamp=time.time(),
            active_missions=snapshot.missions.get("active", 0),
            failed_missions=snapshot.missions.get("failed", 0),
            pending_approvals=snapshot.approvals.get("pending", 0),
            locks_held=snapshot.locks.get("held", 0),
            queue_length=snapshot.scheduler.get("queue_length", 0),
            trust_summary={"overall": snapshot.trust.get("overall", 1.0)},
            notification_summary={
                "info": snapshot.notification.get("info", 0),
                "warning": snapshot.notification.get("warning", 0),
                "error": snapshot.notification.get("error", 0),
                "total": snapshot.notification.get("total", 0),
            },
            telemetry_summary={
                "events_recent": snapshot.timeline.get("events_recent", 0),
                "rate_per_min": 0.0,
            },
            anomalies=[],
        )

    def _mock_rules(self, findings: List[Dict]) -> List[Any]:
        """Create mock TriggeredRule objects from findings."""
        from sam.operations.brain.rule_engine import TriggeredRule
        import time
        rules = []
        for f in findings:
            rules.append(TriggeredRule(
                rule_id=f.get("finding_id", "unknown"),
                name=f.get("finding_id", "Unknown"),
                description="",
                severity=f.get("severity", "info"),
                snapshot_value=None,
                timestamp=time.time(),
            ))
        return rules

    def _build_recommendation_inputs(
        self, finding_dicts: List[Dict]
    ) -> List[Dict[str, Any]]:
        """Build recommendation inputs from findings."""
        inputs = []
        for f in finding_dicts:
            inputs.append({
                "id": f.get("finding_id", "unknown"),
                "recommendation_id": f.get("finding_id", "unknown"),
                "priority": f.get("severity", "info"),
                "confidence": f.get("confidence", 0.5),
                "title": f.get("title", ""),
                "description": f.get("description", ""),
                "affected_count": len(f.get("affected_resources", [])),
                "age_seconds": 0.0,
                "dependencies": [],
            })
        return inputs

    # ── DTO converters ─────────────────────────────────────────────

    def _findings_to_dicts(self, findings: List[OperationalFinding]) -> List[Dict]:
        return [
            {
                "finding_id": f.finding_id,
                "title": f.title,
                "description": f.description,
                "severity": f.severity.value if hasattr(f.severity, "value") else str(f.severity),
                "confidence": f.confidence,
                "evidence": f.evidence,
                "affected_resources": f.affected_resources,
                "recommended_actions": f.recommended_actions,
            }
            for f in findings
        ]

    def _recs_to_dicts(self, recs: List[MissionRecommendation]) -> List[Dict]:
        return [
            {
                "id": rec.recommendation_id,
                "recommendation_id": rec.recommendation_id,
                "title": rec.title,
                "description": rec.description,
                "priority": rec.priority,
                "confidence": rec.confidence,
                "evidence": rec.evidence,
                "suggested_steps": rec.suggested_steps,
                "source_finding_id": rec.source_finding_id,
                "estimated_impact": rec.estimated_impact,
                "required_approval": rec.required_approval,
            }
            for rec in recs
        ]

    def _score_to_dict(self, score: PriorityScore) -> Dict[str, Any]:
        return {
            "item_id": score.item_id,
            "score": score.score,
            "label": score.label,
            "urgency": score.urgency,
            "impact": score.impact,
            "confidence": score.confidence,
            "risk": score.risk,
            "age": score.age,
            "dependency": score.dependency,
        }

    def _corr_to_dict(self, corr: CorrelatedFinding) -> Dict[str, Any]:
        return {
            "correlation_id": corr.correlation_id,
            "source_finding_ids": corr.source_finding_ids,
            "title": corr.title,
            "description": corr.description,
            "severity": corr.severity,
            "confidence": corr.confidence,
            "evidence": corr.evidence,
            "affected_sources": corr.affected_sources,
            "recommended_actions": corr.recommended_actions,
        }

    def _packages_to_dicts(self, packages: List[OperationalPackage]) -> List[Dict]:
        return [
            {
                "package_id": p.package_id,
                "title": p.title,
                "description": p.description,
                "member_ids": p.member_ids,
                "member_priorities": p.member_priorities,
                "combined_score": p.combined_score,
                "combined_priority": p.combined_priority,
                "strategy": p.strategy,
                "dependencies": p.dependencies,
                "source_summary": p.source_summary,
                "affected_resources": list(p.affected_resources),
            }
            for p in packages
        ]

    def _queue_item_to_dict(self, item: QueueItem) -> Dict[str, Any]:
        return {
            "proposal_id": item.proposal_id,
            "state": item.state.value,
            "title": item.title,
            "description": item.description,
            "created_at": item.created_at,
            "updated_at": item.updated_at,
            "evidence": item.evidence,
            "package_id": item.package_id,
            "reason": item.reason,
            "priority_score": item.priority_score,
            "metadata": item.metadata,
        }

    def _health_to_dict(self, health: OperationalHealthDTO) -> Dict[str, Any]:
        return {
            "score": health.score,
            "status": health.status,
            "dimensions": {
                name: {
                    "score": dh.score,
                    "status": dh.status,
                    "details": dh.details,
                    "warnings": dh.warnings,
                    "errors": dh.errors,
                }
                for name, dh in health.dimensions.items()
            },
            "previous_score": health.previous_score,
            "trend": health.trend,
            "generated_at": health.generated_at,
            "unhealthy_dimensions": health.unhealthy_dimensions,
            "degraded_dimensions": health.degraded_dimensions,
            "has_issues": health.has_issues,
        }

    def _snapshot_summary(self, snapshot: MultiSourceSnapshot) -> Dict[str, Any]:
        return snapshot.get_summary()


# ── Convenience ────────────────────────────────────────────────────


def run_proactive_pipeline() -> ProactivePipelineResult:
    """One-shot: run full proactive pipeline."""
    pipeline = ProactivePipeline()
    return pipeline.run()


def pipeline_summary() -> Dict[str, Any]:
    """One-shot: run pipeline and return summary."""
    return ProactivePipeline().run().summary()
