"""
OP-258 — Brain Conversation Bridge V2.

Extends BrainConversationBridge with new query types:
  - health, trends, changes, risks, recommendations
  - dependencies, optimization, confidence, learning

Does NOT create storage — only queries existing repositories
(Audit, Timeline, Learning, Replay, Trust).
Conversation-first: all output is DTO-only.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Callable


class QueryType(Enum):
    """Supported brain query types."""

    HEALTH = "health"
    TRENDS = "trends"
    CHANGES = "changes"
    RISKS = "risks"
    RECOMMENDATIONS = "recommendations"
    DEPENDENCIES = "dependencies"
    OPTIMIZATION = "optimization"
    CONFIDENCE = "confidence"
    LEARNING = "learning"
    APPROVAL_PRIORITY = "approval_priority"
    RECURRING = "recurring"
    EXPLAIN = "explain"


@dataclass
class BrainQuery:
    """A query to the brain layer."""

    query_type: QueryType
    parameters: Dict[str, Any] = field(default_factory=dict)
    limit: int = 10
    include_evidence: bool = False

    def __repr__(self) -> str:
        return f"BrainQuery(type={self.query_type.value}, limit={self.limit})"


@dataclass
class BrainAnswer:
    """Answer from the brain layer to a conversation query."""

    query_type: str
    answer: str
    timestamp: float
    confidence: float = 1.0
    details: List[Dict[str, Any]] = field(default_factory=list)
    sources: List[str] = field(default_factory=list)
    error: Optional[str] = None

    @property
    def has_answer(self) -> bool:
        return self.answer != "" and self.error is None


@dataclass
class ConversationContext:
    """Context for a brain conversation."""

    turn_count: int = 0
    last_queries: List[BrainQuery] = field(default_factory=list)
    last_answers: List[BrainAnswer] = field(default_factory=list)

    def add_turn(self, query: BrainQuery, answer: BrainAnswer) -> None:
        self.turn_count += 1
        self.last_queries.append(query)
        self.last_answers.append(answer)
        # Keep last 20
        if len(self.last_queries) > 20:
            self.last_queries.pop(0)
            self.last_answers.pop(0)

    def last_query(self) -> Optional[BrainQuery]:
        return self.last_queries[-1] if self.last_queries else None

    def last_answer(self) -> Optional[BrainAnswer]:
        return self.last_answers[-1] if self.last_answers else None


# ── Query handlers ────────────────────────────────────────────────────

QueryHandler = Callable[[BrainQuery], BrainAnswer]


def _handle_health(query: BrainQuery) -> BrainAnswer:
    """Return platform health summary."""
    try:
        from .health import evaluate_health
        health = evaluate_health()

        lines = [
            f"Overall health: {health.overall_score:.0f}/100 ({health.overall_status})",
        ]
        red_dims = health.red_dimensions
        yellow_dims = health.yellow_dimensions

        if red_dims:
            lines.append(f"  ❌ RED: {', '.join(red_dims)}")
        if yellow_dims:
            lines.append(f"  ⚠️  YELLOW: {', '.join(yellow_dims)}")

        if not red_dims and not yellow_dims:
            lines.append("  ✅ All dimensions healthy")

        details = [
            {
                "dimension": d.dimension,
                "score": d.score,
                "status": d.status,
                "message": d.message,
            }
            for d in health.dimensions
        ]

        return BrainAnswer(
            query_type="health",
            answer="\n".join(lines),
            timestamp=time.time(),
            confidence=0.95,
            details=details,
            sources=["OperationalHealthEngine"],
        )
    except Exception as e:
        return BrainAnswer(
            query_type="health",
            answer="",
            timestamp=time.time(),
            error=str(e),
        )


def _handle_trends(query: BrainQuery) -> BrainAnswer:
    """Return operational trends."""
    try:
        from sam.operations.timeline_query import get_recent_events
        limit = query.limit
        events = get_recent_events(limit=limit + 20)  # buffer

        if not events:
            return BrainAnswer(
                query_type="trends",
                answer="No recent trends detected.",
                timestamp=time.time(),
                confidence=0.8,
                sources=["TimelineQuery"],
            )

        lines = [f"Recent trends (last {len(events)} events):"]
        for ev in events[:limit]:
            ev_type = getattr(ev, "event_type", getattr(ev, "type", "unknown"))
            ts = getattr(ev, "timestamp", "")
            lines.append(f"  • [{ts}] {ev_type}")

        return BrainAnswer(
            query_type="trends",
            answer="\n".join(lines),
            timestamp=time.time(),
            confidence=0.85,
            sources=["TimelineQuery"],
        )
    except Exception as e:
        return BrainAnswer(
            query_type="trends",
            answer="",
            timestamp=time.time(),
            error=str(e),
        )


def _handle_changes(query: BrainQuery) -> BrainAnswer:
    """Return what changed recently."""
    try:
        from sam.operations.audit import get_recent_audit_entries
        entries = get_recent_audit_entries(limit=query.limit)

        if not entries:
            return BrainAnswer(
                query_type="changes",
                answer="No recent changes detected.",
                timestamp=time.time(),
                confidence=0.8,
                sources=["AuditRepository"],
            )

        lines = ["Recent changes:"]
        for entry in entries:
            action = getattr(entry, "action", getattr(entry, "event", "unknown"))
            ts = getattr(entry, "timestamp", "")
            user = getattr(entry, "actor", getattr(entry, "user", "system"))
            lines.append(f"  • [{ts}] {action} by {user}")

        return BrainAnswer(
            query_type="changes",
            answer="\n".join(lines),
            timestamp=time.time(),
            confidence=0.9,
            sources=["AuditRepository"],
        )
    except Exception as e:
        return BrainAnswer(
            query_type="changes",
            answer="",
            timestamp=time.time(),
            error=str(e),
        )


def _handle_risks(query: BrainQuery) -> BrainAnswer:
    """Return highest risks."""
    try:
        from .priority import PriorityEngine, PriorityCategory
        from .analyzer import OperationalAnalyzer

        # Use previous findings from analyzer if available
        analyzer = OperationalAnalyzer()
        last = analyzer.last_findings
        if not last:
            return BrainAnswer(
                query_type="risks",
                answer="No findings available to assess risks.",
                timestamp=time.time(),
                confidence=0.7,
            )

        engine = PriorityEngine()
        scores = engine.prioritize(last)

        critical = [s for s in scores if s.category == PriorityCategory.CRITICAL]
        high = [s for s in scores if s.category == PriorityCategory.HIGH]

        lines = []
        if critical:
            lines.append(f"CRITICAL risks ({len(critical)}):")
            for s in critical[:query.limit]:
                lines.append(f"  • {s.finding_id}: {s.score:.0f}/100")
        if high:
            lines.append(f"HIGH risks ({len(high)}):")
            for s in high[:query.limit]:
                lines.append(f"  • {s.finding_id}: {s.score:.0f}/100")
        if not critical and not high:
            lines.append("No critical or high risks detected.")

        return BrainAnswer(
            query_type="risks",
            answer="\n".join(lines),
            timestamp=time.time(),
            confidence=0.85,
            sources=["PriorityEngine", "OperationalAnalyzer"],
        )
    except Exception as e:
        return BrainAnswer(
            query_type="risks",
            answer="",
            timestamp=time.time(),
            error=str(e),
        )


def _handle_recommendations(query: BrainQuery) -> BrainAnswer:
    """Return current recommendations."""
    try:
        from .recommendation import RecommendationBuilder
        from .analyzer import OperationalAnalyzer

        analyzer = OperationalAnalyzer()
        last = analyzer.last_findings
        if not last:
            return BrainAnswer(
                query_type="recommendations",
                answer="No findings available for recommendations.",
                timestamp=time.time(),
                confidence=0.7,
            )

        builder = RecommendationBuilder()
        recs = builder.build(last)

        if not recs:
            return BrainAnswer(
                query_type="recommendations",
                answer="No actionable recommendations at this time.",
                timestamp=time.time(),
                confidence=0.9,
            )

        lines = [f"Recommendations ({len(recs)}):"]
        for rec in recs[:query.limit]:
            lines.append(f"  • [{rec.priority}] {rec.title}")
            if query.include_evidence:
                for step in rec.suggested_steps:
                    lines.append(f"    - {step}")

        return BrainAnswer(
            query_type="recommendations",
            answer="\n".join(lines),
            timestamp=time.time(),
            confidence=0.85,
            sources=["RecommendationBuilder"],
        )
    except Exception as e:
        return BrainAnswer(
            query_type="recommendations",
            answer="",
            timestamp=time.time(),
            error=str(e),
        )


def _handle_approval_priority(query: BrainQuery) -> BrainAnswer:
    """Return what should be approved first."""
    try:
        from .proposal_queue import ProposalQueue
        q = ProposalQueue()
        ready = q.list_ready()
        if not ready:
            return BrainAnswer(
                query_type="approval_priority",
                answer="No proposals waiting for approval.",
                timestamp=time.time(),
                confidence=0.9,
                sources=["ProposalQueue"],
            )

        lines = ["Proposals sorted by priority:"]
        for item in ready[:query.limit]:
            lines.append(
                f"  • {item.priority_score:.0f}/100 — {item.title} "
                f"[{item.proposal_id[:8]}]"
            )

        return BrainAnswer(
            query_type="approval_priority",
            answer="\n".join(lines),
            timestamp=time.time(),
            confidence=0.9,
            sources=["ProposalQueue"],
        )
    except Exception as e:
        return BrainAnswer(
            query_type="approval_priority",
            answer="",
            timestamp=time.time(),
            error=str(e),
        )


def _handle_recurring(query: BrainQuery) -> BrainAnswer:
    """Return recurring problems."""
    try:
        from .pattern_miner import PatternMiner
        miner = PatternMiner()
        patterns = miner.last_patterns if hasattr(miner, 'last_patterns') else []

        if not patterns:
            return BrainAnswer(
                query_type="recurring",
                answer="No recurring problems detected.",
                timestamp=time.time(),
                confidence=0.8,
                sources=["PatternMiner"],
            )

        lines = ["Recurring patterns:"]
        for p in patterns[:query.limit]:
            freq = getattr(p, "frequency", getattr(p, "count", "?"))
            lines.append(f"  • {getattr(p, 'description', str(p))} (freq: {freq})")

        return BrainAnswer(
            query_type="recurring",
            answer="\n".join(lines),
            timestamp=time.time(),
            confidence=0.8,
            sources=["PatternMiner"],
        )
    except Exception:
        return BrainAnswer(
            query_type="recurring",
            answer="No recurring problem detection available.",
            timestamp=time.time(),
            confidence=0.5,
        )


def _handle_learning(query: BrainQuery) -> BrainAnswer:
    """Return learning summary."""
    try:
        from .learning_pipeline import LearningPipeline
        pipe = LearningPipeline()
        snapshots = pipe.snapshot_count if hasattr(pipe, 'snapshot_count') else 0
        insights = (list(pipe.list_insights()) if hasattr(pipe, 'list_insights')
                    else pipe.last_result.insights if hasattr(pipe, 'last_result')
                    and hasattr(pipe.last_result, 'insights') else [])

        lines = [f"Learning snapshots: {snapshots}"]
        if insights:
            lines.append("Recent insights:")
            for ins in list(insights)[:query.limit]:
                lines.append(f"  • {ins}")

        return BrainAnswer(
            query_type="learning",
            answer="\n".join(lines),
            timestamp=time.time(),
            confidence=0.8,
            sources=["LearningPipeline"],
        )
    except Exception as e:
        return BrainAnswer(
            query_type="learning",
            answer="",
            timestamp=time.time(),
            error=str(e),
        )


def _handle_explain(query: BrainQuery) -> BrainAnswer:
    """Explain a specific finding or recommendation."""
    target = query.parameters.get("target", "")
    if not target:
        return BrainAnswer(
            query_type="explain",
            answer="Please specify what to explain (e.g., target='mission_failure').",
            timestamp=time.time(),
            confidence=1.0,
        )

    try:
        from .analyzer import OperationalAnalyzer
        from .recommendation import RecommendationBuilder

        analyzer = OperationalAnalyzer()
        last = analyzer.last_findings

        for f in last:
            if f.finding_id == target:
                lines = [
                    f"Finding: {f.title} ({f.severity.value})",
                    f"  Description: {f.description}",
                    f"  Confidence: {f.confidence:.0%}",
                    f"  Affected: {', '.join(f.affected_resources)}",
                    "  Evidence:",
                ]
                for ev in f.evidence:
                    lines.append(f"    - {ev}")
                if f.recommended_actions:
                    lines.append("  Recommended actions:")
                    for a in f.recommended_actions:
                        lines.append(f"    - {a}")

                return BrainAnswer(
                    query_type="explain",
                    answer="\n".join(lines),
                    timestamp=time.time(),
                    confidence=f.confidence,
                    sources=["OperationalAnalyzer"],
                )

        return BrainAnswer(
            query_type="explain",
            answer=f"No finding found with id '{target}'.",
            timestamp=time.time(),
            confidence=0.9,
        )
    except Exception as e:
        return BrainAnswer(
            query_type="explain",
            answer="",
            timestamp=time.time(),
            error=str(e),
        )


def _handle_dependencies(query: BrainQuery) -> BrainAnswer:
    """Return dependency chain for a component."""
    target = query.parameters.get("target", "")
    if not target:
        return BrainAnswer(
            query_type="dependencies",
            answer="Please specify a component (e.g., target='brain_pipeline').",
            timestamp=time.time(),
            confidence=1.0,
        )

    dep_map = {
        "brain_pipeline": [
            "ObservationEngine", "RuleEngine", "OperationalAnalyzer",
            "CorrelationEngine", "PriorityEngine", "RecommendationBuilder",
            "ProposalService",
        ],
        "observation": ["ObservationEngine", "MultiSourceObserver"],
        "queue": ["ProposalQueue", "QueueProvider", "ApprovalService"],
        "health": ["OperationalHealthEngine", "ObservationEngine", "RuleEngine"],
    }

    deps = dep_map.get(target, ["Unknown component"])
    lines = [f"Dependencies for '{target}':"]
    for d in deps:
        lines.append(f"  • {d}")

    return BrainAnswer(
        query_type="dependencies",
        answer="\n".join(lines),
        timestamp=time.time(),
        confidence=0.9,
        sources=["Architecture knowledge"],
    )


def _handle_optimization(query: BrainQuery) -> BrainAnswer:
    """Return optimization opportunities."""
    try:
        from .optimizer import RecommendationOptimizer
        opt = RecommendationOptimizer()
        reports = opt.reports if hasattr(opt, 'reports') else []

        if not reports:
            return BrainAnswer(
                query_type="optimization",
                answer="No optimization opportunities identified yet.",
                timestamp=time.time(),
                confidence=0.7,
                sources=["RecommendationOptimizer"],
            )

        lines = ["Optimization opportunities:"]
        for r in list(reports)[:query.limit]:
            lines.append(f"  • {getattr(r, 'summary', str(r))}")

        return BrainAnswer(
            query_type="optimization",
            answer="\n".join(lines),
            timestamp=time.time(),
            confidence=0.8,
            sources=["RecommendationOptimizer"],
        )
    except Exception:
        return BrainAnswer(
            query_type="optimization",
            answer="Optimization analysis not yet available.",
            timestamp=time.time(),
            confidence=0.5,
        )


def _handle_confidence(query: BrainQuery) -> BrainAnswer:
    """Return confidence history."""
    try:
        from sam.operations.trust import get_trust_summary
        from .success_estimator import SuccessEstimator

        trust = get_trust_summary()

        est = SuccessEstimator()
        estimates = est.history if hasattr(est, 'history') else []

        lines = ["Confidence & Trust Summary:"]
        lines.append(f"  Trust scores: {trust}")
        if estimates:
            avg_conf = sum(
                getattr(e, 'confidence', 0) for e in estimates[-10:]
            ) / min(len(estimates), 10)
            lines.append(f"  Recent avg confidence: {avg_conf:.1%}")

        return BrainAnswer(
            query_type="confidence",
            answer="\n".join(lines),
            timestamp=time.time(),
            confidence=0.85,
            sources=["TrustRepository", "SuccessEstimator"],
        )
    except Exception as e:
        return BrainAnswer(
            query_type="confidence",
            answer="",
            timestamp=time.time(),
            error=str(e),
        )


# ── Handler registry ──────────────────────────────────────────────────

_HANDLERS: Dict[QueryType, QueryHandler] = {
    QueryType.HEALTH: _handle_health,
    QueryType.TRENDS: _handle_trends,
    QueryType.CHANGES: _handle_changes,
    QueryType.RISKS: _handle_risks,
    QueryType.RECOMMENDATIONS: _handle_recommendations,
    QueryType.DEPENDENCIES: _handle_dependencies,
    QueryType.OPTIMIZATION: _handle_optimization,
    QueryType.CONFIDENCE: _handle_confidence,
    QueryType.LEARNING: _handle_learning,
    QueryType.APPROVAL_PRIORITY: _handle_approval_priority,
    QueryType.RECURRING: _handle_recurring,
    QueryType.EXPLAIN: _handle_explain,
}


class BrainConversationBridgeV2:
    """Bridge between Conversation layer and Brain layer (V2).

    Supports 12 query types. All queries through DTOs.
    Does NOT create storage — only queries existing repos.
    """

    def __init__(self) -> None:
        self._context = ConversationContext()

    @property
    def context(self) -> ConversationContext:
        return self._context

    def ask(self, query: BrainQuery) -> BrainAnswer:
        """Ask the brain a question.

        Routes to the appropriate handler based on query type.
        """
        handler = _HANDLERS.get(query.query_type)
        if handler is None:
            answer = BrainAnswer(
                query_type=query.query_type.value,
                answer="",
                timestamp=time.time(),
                error=f"Unknown query type: {query.query_type}",
            )
        else:
            try:
                answer = handler(query)
            except Exception as e:
                answer = BrainAnswer(
                    query_type=query.query_type.value,
                    answer="",
                    timestamp=time.time(),
                    error=str(e),
                )

        self._context.add_turn(query, answer)
        return answer

    def ask_health(self) -> BrainAnswer:
        return self.ask(BrainQuery(query_type=QueryType.HEALTH))

    def ask_trends(self, limit: int = 10) -> BrainAnswer:
        return self.ask(BrainQuery(query_type=QueryType.TRENDS, limit=limit))

    def ask_changes(self, limit: int = 10) -> BrainAnswer:
        return self.ask(BrainQuery(query_type=QueryType.CHANGES, limit=limit))

    def ask_risks(self, limit: int = 10) -> BrainAnswer:
        return self.ask(BrainQuery(query_type=QueryType.RISKS, limit=limit))

    def ask_recommendations(
        self,
        limit: int = 10,
        with_evidence: bool = False,
    ) -> BrainAnswer:
        return self.ask(BrainQuery(
            query_type=QueryType.RECOMMENDATIONS,
            limit=limit,
            include_evidence=with_evidence,
        ))

    def ask_explain(self, target: str) -> BrainAnswer:
        return self.ask(BrainQuery(
            query_type=QueryType.EXPLAIN,
            parameters={"target": target},
        ))

    def reset_context(self) -> None:
        self._context = ConversationContext()


# ── Convenience functions ─────────────────────────────────────────────


def classify_query(text: str) -> QueryType:
    """Simple query classification based on text keywords.

    Falls back to HEALTH if no clear match.
    """
    lower = text.lower()
    if any(kw in lower for kw in ["risk", "danger", "threat", "critical"]):
        return QueryType.RISKS
    if any(kw in lower for kw in ["health", "status", "ok?"]):
        return QueryType.HEALTH
    if any(kw in lower for kw in ["trend", "pattern", "recurring"]):
        return QueryType.TRENDS
    if any(kw in lower for kw in ["change", "what happened", "recent"]):
        return QueryType.CHANGES
    if any(kw in lower for kw in ["recommend", "suggest", "what should"]):
        return QueryType.RECOMMENDATIONS
    if any(kw in lower for kw in ["explain", "why", "how"]):
        return QueryType.EXPLAIN
    if any(kw in lower for kw in ["approve", "priority", "first"]):
        return QueryType.APPROVAL_PRIORITY
    if any(kw in lower for kw in ["learn", "insight", "knowledge"]):
        return QueryType.LEARNING
    if any(kw in lower for kw in ["optimize", "improve", "better"]):
        return QueryType.OPTIMIZATION
    if any(kw in lower for kw in ["depend", "chain", "relies"]):
        return QueryType.DEPENDENCIES
    if any(kw in lower for kw in ["confidence", "trust", "sure"]):
        return QueryType.CONFIDENCE
    if any(kw in lower for kw in ["problem", "error", "fail", "broken"]):
        return QueryType.RECURRING
    return QueryType.HEALTH


def ask_brain_v2(
    query_text: str,
    limit: int = 10,
) -> BrainAnswer:
    """One-shot: ask brain from natural text.

    Classifies text -> routes to appropriate handler.
    """
    qtype = classify_query(query_text)
    bridge = BrainConversationBridgeV2()
    return bridge.ask(BrainQuery(
        query_type=qtype,
        limit=limit,
    ))
