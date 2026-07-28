"""
OP-258 — Conversation Brain Upgrade.

Upgraded conversation bridge that can answer:
  - What is the biggest problem right now?
  - What is today's priority?
  - Why was this proposal created?
  - What evidence supports this?
  - What is the impact if ignored?

Uses the brain pipeline output (findings, recommendations, proposals,
correlated findings, priority scores, packages, health).

All answers are DTO-based, deterministic, no AI.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple


# ── Data ───────────────────────────────────────────────────────────


@dataclass
class ConversationContext:
    """
    Full context for the conversation bridge.

    Populated by BrainPipeline.run() and/or manual update.
    """

    findings: List[Dict[str, Any]] = field(default_factory=list)
    recommendations: List[Dict[str, Any]] = field(default_factory=list)
    proposals: List[Dict[str, Any]] = field(default_factory=list)
    correlated_findings: List[Dict[str, Any]] = field(default_factory=list)
    priority_scores: List[Dict[str, Any]] = field(default_factory=list)
    packages: List[Dict[str, Any]] = field(default_factory=list)
    health: Optional[Dict[str, Any]] = None
    observation: Dict[str, Any] = field(default_factory=dict)
    triggered_rules: List[Dict[str, Any]] = field(default_factory=list)
    multi_source: Dict[str, Any] = field(default_factory=dict)

    def snapshot(self) -> Dict[str, Any]:
        """Create immutable snapshot of current context."""
        return {
            "findings_count": len(self.findings),
            "recommendations_count": len(self.recommendations),
            "proposals_count": len(self.proposals),
            "correlated_findings_count": len(self.correlated_findings),
            "packages_count": len(self.packages),
            "health_score": (self.health or {}).get("score", 1.0),
            "health_status": (self.health or {}).get("status", "healthy"),
            "timestamp": time.time(),
        }


@dataclass
class BrainQuery:
    """A query to the conversation bridge."""

    text: str
    query_type: str = "general"  # classified from text
    context: Optional[Dict[str, Any]] = None


@dataclass
class BrainAnswer:
    """Structured answer from the conversation bridge."""

    answer: str
    data: Dict[str, Any] = field(default_factory=dict)
    query_type: str = "general"
    confidence: float = 1.0
    generated_at: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "answer": self.answer,
            "data": self.data,
            "confidence": self.confidence,
        }


# ── Query classifiers ──────────────────────────────────────────────

_KEYWORD_MAP: Dict[str, str] = {
    # Biggest problem
    "biggest problem": "biggest_problem",
    "biggest issue": "biggest_problem",
    "worst": "biggest_problem",
    "most critical": "biggest_problem",
    # Priority
    "priority": "priority",
    "priorities": "priority",
    "most important": "priority",
    # Why
    "why": "why",
    "reason": "why",
    "rationale": "why",
    # Evidence
    "evidence": "evidence",
    "proof": "evidence",
    "supporting": "evidence",
    "data": "evidence",
    # Impact
    "impact": "impact",
    "consequence": "impact",
    "what if": "impact",
    "ignore": "impact",
    "skip": "impact",
    # Status / summary
    "status": "status",
    "summary": "status",
    "overview": "status",
    "how is": "status",
    # Recommendations
    "recommend": "recommendation",
    "suggest": "recommendation",
    "what should": "recommendation",
    # Proposals
    "proposal": "proposal",
    "pending": "pending",
    "waiting": "pending",
    # Health
    "health": "health",
    "score": "health",
    "all good": "health",
    "fine": "health",
    # Issues
    "issue": "issues",
    "problem": "issues",
    "wrong": "issues",
    "anomaly": "issues",
    "alert": "issues",
}


def classify_query(text: str) -> str:
    """Classify a question into a query type."""
    lower = text.lower().strip()
    for keyword, qtype in _KEYWORD_MAP.items():
        if keyword in lower:
            return qtype
    # Check starts with common patterns
    if lower.startswith("what") and "recommend" in lower:
        return "recommendation"
    if lower.startswith("are there") or lower.startswith("any"):
        return "issues"
    return "general"


# ── Bridge ─────────────────────────────────────────────────────────


class BrainConversationBridgeV2:
    """
    Upgraded conversation bridge with context-aware answers.

    Answers questions about:
      - biggest problems
      - priorities
      - proposal rationale
      - evidence
      - impact analysis
      - health status
      - pending items
      - recommendations
    """

    def __init__(self):
        self._context = ConversationContext()
        self._last_answer: Optional[BrainAnswer] = None

    # ── State management ───────────────────────────────────────────

    @property
    def context(self) -> ConversationContext:
        return self._context

    def update_context(self, **kwargs) -> None:
        """Update context fields."""
        for key, value in kwargs.items():
            if hasattr(self._context, key):
                setattr(self._context, key, value)

    def update_from_pipeline(self, pipeline_result: Any) -> None:
        """Update context from a pipeline result object."""
        if hasattr(pipeline_result, "findings"):
            self._context.findings = pipeline_result.findings
        if hasattr(pipeline_result, "recommendations"):
            self._context.recommendations = pipeline_result.recommendations
        if hasattr(pipeline_result, "proposals"):
            self._context.proposals = pipeline_result.proposals
        if hasattr(pipeline_result, "dashboard"):
            d = pipeline_result.dashboard
            if hasattr(d, "health_score"):
                self._context.health = {"score": d.health_score, "status": d.health_state}
            if hasattr(d, "observation_summary"):
                self._context.observation = d.observation_summary

    def context_snapshot(self) -> Dict[str, Any]:
        return self._context.snapshot()

    # ── Query ──────────────────────────────────────────────────────

    def ask(self, query: str) -> BrainAnswer:
        """Process a natural-language query and return a structured answer."""
        qtype = classify_query(query)
        answer = self._dispatch(qtype, query)
        return answer

    def ask_with_context(self, query: str, context: Dict[str, Any]) -> BrainAnswer:
        """Process query with additional context overlay."""
        for key, value in context.items():
            if hasattr(self._context, key):
                setattr(self._context, key, value)
        return self.ask(query)

    # ── Dispatch ───────────────────────────────────────────────────

    def _dispatch(self, qtype: str, query: str) -> BrainAnswer:
        handler = getattr(self, f"_answer_{qtype}", self._answer_general)
        try:
            answer = handler(query)
        except Exception as e:
            answer = BrainAnswer(
                answer=f"Error processing query: {e}",
                query_type=qtype,
                confidence=0.0,
                generated_at=time.time(),
            )
        answer.query_type = qtype
        answer.generated_at = time.time()
        self._last_answer = answer
        return answer

    # ── Answer handlers ────────────────────────────────────────────

    def _answer_biggest_problem(self, query: str) -> BrainAnswer:
        """Find the single highest-severity issue."""
        ctx = self._context

        # Check correlated findings first
        if ctx.correlated_findings:
            worst = max(
                ctx.correlated_findings,
                key=lambda f: {"info": 0, "warning": 1, "critical": 2}.get(
                    f.get("severity", "info"), 0
                ),
            )
            return BrainAnswer(
                answer=(
                    f"**{worst.get('title', 'Unknown issue')}**\n"
                    f"{worst.get('description', '')}\n"
                    f"Severity: {worst.get('severity', 'info')} | "
                    f"Confidence: {worst.get('confidence', 0.5):.0%}"
                ),
                data={"biggest_problem": worst},
            )

        # Fall back to findings
        findings = ctx.findings
        if not findings:
            return BrainAnswer(
                answer="No problems detected. System appears stable.",
                data={},
            )

        worst = max(
            findings,
            key=lambda f: {"info": 0, "warning": 1, "critical": 2}.get(
                f.get("severity", "info"), 0
            ),
        )
        return BrainAnswer(
            answer=(
                f"**{worst.get('title', 'Issue')}**\n"
                f"Severity: {worst.get('severity', 'info')} | "
                f"Confidence: {worst.get('confidence', 0.5):.0%}\n"
                f"{worst.get('description', '')}"
            ),
            data={"biggest_problem": worst},
        )

    def _answer_priority(self, query: str) -> BrainAnswer:
        """List current priorities."""
        ctx = self._context

        if ctx.priority_scores:
            top = sorted(ctx.priority_scores, key=lambda x: x.get("score", 0), reverse=True)[:3]
            lines = []
            for i, p in enumerate(top, 1):
                lines.append(
                    f"{i}. **{p.get('item_id', 'Unknown')}** — "
                    f"Score: {p.get('score', 0):.2f} ({p.get('label', 'low')})"
                )
            # Find matching titles
            title_map = {}
            for rec in ctx.recommendations:
                rid = rec.get("id", rec.get("recommendation_id", ""))
                title_map[rid] = rec.get("title", rid)
            detail_lines = []
            for p in top:
                pid = p.get("item_id", "")
                title = title_map.get(pid, pid)
                detail_lines.append(f"  • {title} — urgency {p.get('urgency', 0):.2f}, "
                                    f"impact {p.get('impact', 0):.2f}")
            answer_lines = lines + [""] + detail_lines
            return BrainAnswer(
                answer="\n".join(answer_lines),
                data={"top_priorities": top},
            )

        if ctx.recommendations:
            crit = [r for r in ctx.recommendations
                    if r.get("priority") == "critical"]
            high = [r for r in ctx.recommendations
                    if r.get("priority") == "high"]
            return BrainAnswer(
                answer=(
                    f"Priorities: {len(crit)} critical, {len(high)} high, "
                    f"{len(ctx.recommendations)} total recommendations."
                ),
                data={"critical_count": len(crit), "high_count": len(high)},
            )

        return BrainAnswer(
            answer="No priorities set. No active recommendations.",
            data={},
        )

    def _answer_why(self, query: str) -> BrainAnswer:
        """Explain why a proposal or recommendation was created."""
        ctx = self._context

        # Try to find what the user is asking about
        lower = query.lower()
        proposals = ctx.proposals
        recs = ctx.recommendations

        # Search for a specific title or ID in the query
        candidates = []
        for item in proposals + recs:
            title = item.get("title", "")
            item_id = item.get("id", item.get("proposal_id", item.get("recommendation_id", "")))
            desc = item.get("description", "")
            evidence = item.get("evidence", item.get("supporting_data", []))
            if title.lower() in lower or item_id.lower() in lower:
                candidates.append((item, title, item_id, desc, evidence))

        if candidates:
            item, title, item_id, desc, evidence = candidates[0]
            evidence_summary = self._summarize_evidence(evidence[-3:])  # last 3
            return BrainAnswer(
                answer=(
                    f"**Why {title}?**\n"
                    f"{desc}\n\n"
                    f"Evidence:\n{evidence_summary}"
                ),
                data={
                    "item_id": item_id,
                    "title": title,
                    "description": desc,
                    "evidence": evidence,
                },
            )

        # General: show why each proposal exists
        if proposals:
            lines = []
            for p in proposals:
                title = p.get("title", "Proposal")
                reason = p.get("description", "No description")[:100]
                lines.append(f"  • **{title}**: {reason}")
            return BrainAnswer(
                answer=f"Active proposals:\n" + "\n".join(lines),
                data={"proposals": proposals},
            )

        return BrainAnswer(
            answer="No proposals to explain.",
            data={},
        )

    def _answer_evidence(self, query: str) -> BrainAnswer:
        """Show evidence supporting findings or proposals."""
        ctx = self._context
        all_evidence = []

        for f in ctx.findings:
            for e in f.get("evidence", []):
                all_evidence.append({
                    **e,
                    "_source": f.get("finding_id", f.get("title", "unknown")),
                    "_type": "finding",
                })
        for r in ctx.recommendations:
            for e in r.get("evidence", []):
                all_evidence.append({
                    **e,
                    "_source": r.get("title", r.get("recommendation_id", "unknown")),
                    "_type": "recommendation",
                })

        if not all_evidence:
            return BrainAnswer(
                answer="No evidence available.",
                data={"evidence": []},
            )

        # Filter by query if keyword given
        lower = query.lower()
        filtered = all_evidence
        keywords = [kw for kw in ["approval", "mission", "trust", "queue",
                                   "lock", "anomaly", "failure", "notification"]
                    if kw in lower]
        if keywords:
            filtered = [e for e in all_evidence
                        if any(kw in str(e).lower() for kw in keywords)]

        # Group by source
        by_source: Dict[str, List[Dict]] = {}
        for e in filtered:
            src = e.get("_source", "unknown")
            if src not in by_source:
                by_source[src] = []
            by_source[src].append(e)

        lines = [f"**Evidence** ({len(filtered)} items)"]
        for src, items in list(by_source.items())[:5]:
            lines.append(f"\n  From: {src}")
            for item in items[:3]:
                value = item.get("value", item.get("field", item.get("message", "")))
                etype = item.get("type", "data")
                lines.append(f"    [{etype}] {value}")

        return BrainAnswer(
            answer="\n".join(lines),
            data={"evidence": filtered, "sources": list(by_source.keys())},
        )

    def _answer_impact(self, query: str) -> BrainAnswer:
        """Describe impact of ignoring recommendations."""
        ctx = self._context
        if not ctx.recommendations:
            return BrainAnswer(
                answer="No active recommendations to evaluate impact.",
                data={},
            )

        # Find highest priority recs and describe impact
        top = sorted(
            ctx.recommendations,
            key=lambda r: {"critical": 4, "high": 3, "medium": 2, "low": 1}.get(
                r.get("priority", "low"), 0
            ),
            reverse=True,
        )[:3]

        lines = ["**Impact if ignored**"]
        for r in top:
            title = r.get("title", "Issue")
            priority = r.get("priority", "low")
            conf = r.get("confidence", 0.5)
            affected = r.get("affected_resources", r.get("affected_sources", ["system"]))
            resources = ", ".join(affected[:3])
            impact_desc = r.get("estimated_impact", "Unknown impact")
            lines.append(
                f"\n• **{title}** ({priority}, {conf:.0%} confidence)\n"
                f"  Resources: {resources}\n"
                f"  Impact: {impact_desc}"
            )

        return BrainAnswer(
            answer="\n".join(lines),
            data={"top_impacts": top},
        )

    def _answer_status(self, query: str) -> BrainAnswer:
        """Overall system status summary."""
        ctx = self._context
        health = ctx.health or {}
        health_score = health.get("score", 1.0)
        health_status = health.get("status", "healthy")

        findings_count = len(ctx.findings)
        recs_count = len(ctx.recommendations)
        proposals_count = len(ctx.proposals)
        correlated_count = len(ctx.correlated_findings)
        packages_count = len(ctx.packages)

        obs = ctx.observation
        active_missions = obs.get("active_missions", obs.get("active", 0))
        pending_approvals = obs.get("pending_approvals", obs.get("pending", 0))
        anomalies = obs.get("anomalies", 0)

        return BrainAnswer(
            answer=(
                f"**System Status** — Health: {health_score:.2f} ({health_status})\n\n"
                f"• Findings: {findings_count}  |  Recommendations: {recs_count}\n"
                f"• Proposals: {proposals_count}  |  Correlated: {correlated_count}\n"
                f"• Packages: {packages_count}\n"
                f"• Active missions: {active_missions}  |  Pending approvals: {pending_approvals}\n"
                f"• Anomalies: {anomalies}"
            ),
            data=ctx.snapshot(),
        )

    def _answer_recommendation(self, query: str) -> BrainAnswer:
        """List recommendations."""
        ctx = self._context
        if not ctx.recommendations:
            return BrainAnswer(
                answer="No recommendations at this time.",
                data={},
            )

        lines = [f"**Recommendations** ({len(ctx.recommendations)} total)"]
        for r in ctx.recommendations:
            title = r.get("title", r.get("recommendation_id", "Unknown"))
            priority = r.get("priority", "low")
            confidence = r.get("confidence", 0.5)
            steps = r.get("suggested_steps", [])
            steps_str = ", ".join(steps[:3]) if steps else ""
            lines.append(f"  • **{title}** ({priority}, {confidence:.0%})")
            if steps_str:
                lines.append(f"    Steps: {steps_str}")

        return BrainAnswer(
            answer="\n".join(lines),
            data={"recommendations": ctx.recommendations},
        )

    def _answer_proposal(self, query: str) -> BrainAnswer:
        """List proposals."""
        ctx = self._context
        if not ctx.proposals:
            return BrainAnswer(
                answer="No proposals active.",
                data={},
            )
        lines = [f"**Proposals** ({len(ctx.proposals)} total)"]
        for p in ctx.proposals:
            title = p.get("title", p.get("proposal_id", "Unknown"))
            state = p.get("state", p.get("status", "draft"))
            lines.append(f"  • **{title}** — {state}")
        return BrainAnswer(
            answer="\n".join(lines),
            data={"proposals": ctx.proposals},
        )

    def _answer_pending(self, query: str) -> BrainAnswer:
        """List pending items (waiting approval)."""
        ctx = self._context
        pending = [p for p in ctx.proposals
                   if p.get("state", p.get("status", "")) == "waiting_approval"]
        if not pending:
            return BrainAnswer(
                answer="No pending approvals.",
                data={},
            )
        lines = [f"**Pending Approval** ({len(pending)} items)"]
        for p in pending:
            title = p.get("title", p.get("proposal_id", "Unknown"))
            lines.append(f"  • {title}")
        return BrainAnswer(
            answer="\n".join(lines),
            data={"pending": pending},
        )

    def _answer_health(self, query: str) -> BrainAnswer:
        """Report health status."""
        ctx = self._context
        health = ctx.health or {}
        score = health.get("score", 1.0)
        status = health.get("status", "healthy")
        dims = health.get("dimensions", {})

        if dims:
            dim_lines = []
            for name, dh in sorted(dims.items()):
                if isinstance(dh, dict):
                    ds = dh.get("score", 1.0)
                    dst = dh.get("status", "healthy")
                else:
                    ds = getattr(dh, "score", 1.0)
                    dst = getattr(dh, "status", "healthy")
                dim_lines.append(f"  • {name}: {ds:.2f} ({dst})")
            dim_str = "\n" + "\n".join(dim_lines)
        else:
            dim_str = ""

        trend = health.get("trend", "stable")

        return BrainAnswer(
            answer=(
                f"**Operational Health**: {score:.2f} ({status}) — {trend}"
                f"{dim_str}"
            ),
            data={
                "health_score": score,
                "health_status": status,
                "trend": trend,
                "dimensions": dims,
            },
        )

    def _answer_issues(self, query: str) -> BrainAnswer:
        """List all current issues (critical + warning)."""
        ctx = self._context
        issues = [
            f for f in ctx.findings
            if f.get("severity") in ("critical", "warning")
        ]
        if not issues:
            return BrainAnswer(
                answer="No issues detected. System is clear.",
                data={},
            )

        crit = [f for f in issues if f.get("severity") == "critical"]
        warn = [f for f in issues if f.get("severity") == "warning"]

        lines = [f"**Issues**: {len(crit)} critical, {len(warn)} warning"]
        for f in crit[:5]:
            lines.append(f"  🔴 **{f.get('title', 'Issue')}** — {f.get('description', '')[:100]}")
        for f in warn[:5]:
            lines.append(f"  🟡 **{f.get('title', 'Issue')}** — {f.get('description', '')[:100]}")

        return BrainAnswer(
            answer="\n".join(lines),
            data={"critical": crit, "warning": warn},
        )

    def _answer_general(self, query: str) -> BrainAnswer:
        """Fallback: show available query types."""
        return BrainAnswer(
            answer=(
                "I can answer questions about:\n"
                "  • **biggest problem** — what's the most critical issue?\n"
                "  • **priorities** — what needs attention now?\n"
                "  • **why** — why was a proposal created?\n"
                "  • **evidence** — what evidence supports recommendations?\n"
                "  • **impact** — what happens if ignored?\n"
                "  • **status** — overall system status\n"
                "  • **health** — operational health score\n"
                "  • **recommendations** — active recommendations\n"
                "  • **proposals** — active proposals\n"
                "  • **pending** — items waiting approval\n"
                "  • **issues** — current warnings and problems\n\n"
                "Try: 'What's the biggest problem?' or 'What is today's priority?'"
            ),
            data={"available_queries": list(_KEYWORD_MAP.values())},
        )

    # ── Helpers ────────────────────────────────────────────────────

    def _summarize_evidence(self, evidence: List[Dict]) -> str:
        if not evidence:
            return "No evidence."
        lines = []
        for e in evidence:
            val = e.get("value", e.get("field", e.get("message", str(e))))
            etype = e.get("type", "data")
            lines.append(f"    [{etype}] {val}")
        return "\n".join(lines)


# ── Convenience ────────────────────────────────────────────────────


def ask_brain_v2(query: str, context: Optional[ConversationContext] = None) -> BrainAnswer:
    """One-shot: ask a question with optional context."""
    bridge = BrainConversationBridgeV2()
    if context:
        bridge.update_context(findings=context.findings,
                              recommendations=context.recommendations,
                              proposals=context.proposals)
    return bridge.ask(query)
