"""
OP-246 — Brain Conversation Bridge.

Conversation-style queries that return DTO-based answers.
No AI reasoning — all answers derived from operational state.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class BrainConversationRequest:
    """A user query to the operational brain."""

    query: str
    context: Optional[Dict[str, Any]] = None


@dataclass
class BrainConversationResponse:
    """A response from the operational brain."""

    answer: str
    data: Dict[str, Any] = field(default_factory=dict)
    source: str = "brain"
    confidence: float = 1.0


class BrainConversationBridge:
    """Answers operational questions using Brain DTOs.

    Supported queries:
      - "what do you recommend"
      - "any operational issues"
      - "what needs attention"
      - "any anomaly"
      - "why are you recommending"
      - "show evidence"
      - "show findings"
      - "show recommendations"
      - "show observation"
      - "show rules"
      - "status"
      - "health"
    """

    def __init__(self) -> None:
        # These are injected by BrainPipeline integration
        self._last_findings: List[Dict[str, Any]] = []
        self._last_recommendations: List[Dict[str, Any]] = []
        self._last_observation: Dict[str, Any] = {}
        self._last_rules: List[Dict[str, Any]] = []
        self._last_health_score: float = 1.0

    def set_state(
        self,
        findings: List[Dict[str, Any]],
        recommendations: List[Dict[str, Any]],
        observation: Dict[str, Any],
        rules: List[Dict[str, Any]],
        health_score: float,
    ) -> None:
        """Update internal state from BrainPipeline."""
        self._last_findings = findings
        self._last_recommendations = recommendations
        self._last_observation = observation
        self._last_rules = rules
        self._last_health_score = health_score

    def ask(self, request: BrainConversationRequest) -> BrainConversationResponse:
        """Answer a question based on current brain state."""
        q = request.query.strip().lower()

        if "recommend" in q:
            return self._answer_recommendations()
        elif "issue" in q or "problem" in q:
            return self._answer_issues()
        elif "attention" in q:
            return self._answer_attention()
        elif "anomal" in q:
            return self._answer_anomalies()
        elif "why" in q and "recommend" in q:
            return self._answer_why_recommend()
        elif "evidence" in q:
            return self._answer_evidence()
        elif "finding" in q:
            return self._answer_findings()
        elif "observation" in q or "observe" in q:
            return self._answer_observation()
        elif "rule" in q:
            return self._answer_rules()
        elif "health" in q or "status" in q:
            return self._answer_health()
        else:
            return BrainConversationResponse(
                answer=(
                    "I can answer questions about operational status, "
                    "findings, recommendations, evidence, anomalies, "
                    "and health. Try: 'What do you recommend?' or "
                    "'Any operational issues?'"
                ),
                source="brain",
            )

    def _answer_recommendations(self) -> BrainConversationResponse:
        if not self._last_recommendations:
            return BrainConversationResponse(
                answer="No recommendations at this time. System is operating normally.",
                data={"recommendations": []},
            )
        lines = [f"I have {len(self._last_recommendations)} recommendation(s):"]
        for r in self._last_recommendations:
            lines.append(f"- [{r['priority'].upper()}] {r['title']}: {r.get('description', '')}")
        return BrainConversationResponse(
            answer="\n".join(lines),
            data={"recommendations": self._last_recommendations},
        )

    def _answer_issues(self) -> BrainConversationResponse:
        critical = [
            f for f in self._last_findings
            if f.get("severity", "") in ("critical", "warning")
        ]
        if not critical:
            return BrainConversationResponse(
                answer="No operational issues detected. All clear.",
                data={"issues": []},
            )
        lines = [f"Found {len(critical)} issue(s):"]
        for f in critical:
            lines.append(f"- [{f['severity'].upper()}] {f['title']}")
        return BrainConversationResponse(
            answer="\n".join(lines),
            data={"issues": critical},
        )

    def _answer_attention(self) -> BrainConversationResponse:
        critical = [
            f for f in self._last_findings
            if f.get("severity", "") == "critical"
        ]
        if not critical:
            return BrainConversationResponse(
                answer="Nothing critical needs attention right now.",
                data={"needs_attention": []},
            )
        lines = [f"{len(critical)} item(s) need immediate attention:"]
        for f in critical:
            actions = f.get("recommended_actions", [])
            lines.append(f"- CRITICAL: {f['title']}")
            if actions:
                lines.append(f"  Suggested: {actions[0]}")
        return BrainConversationResponse(
            answer="\n".join(lines),
            data={"needs_attention": critical},
        )

    def _answer_anomalies(self) -> BrainConversationResponse:
        obs = self._last_observation
        anomalies = obs.get("anomalies", [])
        if not anomalies:
            return BrainConversationResponse(
                answer="No anomalies detected.",
                data={"anomalies": []},
            )
        lines = [f"{len(anomalies)} anomaly(ies) detected:"]
        for a in anomalies[:5]:
            lines.append(f"- {a.get('description', str(a)[:80])}")
        return BrainConversationResponse(
            answer="\n".join(lines),
            data={"anomalies": anomalies},
        )

    def _answer_why_recommend(self) -> BrainConversationResponse:
        if not self._last_recommendations:
            return BrainConversationResponse(
                answer="No active recommendations to explain.",
                data={},
            )
        lines = ["Recommendations are based on the following operational observations and rules:"]
        for r in self._last_recommendations:
            evidence = r.get("evidence", [])
            lines.append(f"\n{r['title']}:")
            for e in evidence:
                etype = e.get("type", "data")
                evalue = e.get("value", "N/A")
                lines.append(f"  - {etype}: {evalue}")
        return BrainConversationResponse(
            answer="\n".join(lines),
            data={"recommendations": self._last_recommendations},
        )

    def _answer_evidence(self) -> BrainConversationResponse:
        if not self._last_findings:
            return BrainConversationResponse(
                answer="No findings with evidence available.",
                data={},
            )
        lines = ["Evidence for current findings:"]
        for f in self._last_findings:
            lines.append(f"\n{f['title']}:")
            for e in f.get("evidence", []):
                lines.append(f"  - {e.get('type')}: {e.get('value', 'N/A')}")
        return BrainConversationResponse(
            answer="\n".join(lines),
            data={"findings": self._last_findings},
        )

    def _answer_findings(self) -> BrainConversationResponse:
        if not self._last_findings:
            return BrainConversationResponse(
                answer="No findings at this time.",
                data={"findings": []},
            )
        lines = [f"Current findings ({len(self._last_findings)}):"]
        for f in self._last_findings:
            lines.append(
                f"- [{f.get('severity', 'info').upper()}] "
                f"{f['title']} (confidence: {f.get('confidence', 0):.0%})"
            )
        return BrainConversationResponse(
            answer="\n".join(lines),
            data={"findings": self._last_findings},
        )

    def _answer_observation(self) -> BrainConversationResponse:
        obs = self._last_observation
        if not obs:
            return BrainConversationResponse(
                answer="No observation data available.",
                data={},
            )
        keys = [
            "active_missions", "failed_missions", "pending_approvals",
            "locks_held", "queue_length",
        ]
        lines = ["Current operational observation:"]
        for k in keys:
            v = obs.get(k, "N/A")
            lines.append(f"  {k.replace('_', ' ').title()}: {v}")
        return BrainConversationResponse(
            answer="\n".join(lines),
            data={"observation": obs},
        )

    def _answer_rules(self) -> BrainConversationResponse:
        if not self._last_rules:
            return BrainConversationResponse(
                answer="No rules triggered.",
                data={"triggered_rules": []},
            )
        lines = [f"{len(self._last_rules)} rule(s) triggered:"]
        for r in self._last_rules:
            lines.append(f"  [{r.get('severity', 'info').upper()}] {r.get('name', r.get('rule_id', '?'))}")
        return BrainConversationResponse(
            answer="\n".join(lines),
            data={"triggered_rules": self._last_rules},
        )

    def _answer_health(self) -> BrainConversationResponse:
        score = self._last_health_score
        state = "Healthy" if score >= 0.8 else "Degraded" if score >= 0.5 else "Unhealthy"
        return BrainConversationResponse(
            answer=f"Operational Health Score: {score:.2f} — {state}",
            data={
                "health_score": score,
                "state": state,
                "finding_count": len(self._last_findings),
                "recommendation_count": len(self._last_recommendations),
                "rule_count": len(self._last_rules),
            },
        )


def ask_brain(query: str) -> str:
    """One-shot convenience (creates fresh bridge — no preloaded state)."""
    bridge = BrainConversationBridge()
    req = BrainConversationRequest(query=query)
    return bridge.ask(req).answer
