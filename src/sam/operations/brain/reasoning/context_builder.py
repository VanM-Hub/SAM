"""
OP-292 — Context Assembler

Membangun ReasoningContext dari DTO sources secara deterministic.
Input: ObservationSnapshot, MissionDashboardDTO, BrainDashboardDTO, TimelineSummary, MissionSummary
Output: ReasoningContext
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime

from .session import ReasoningContext


# ── DTO Input ──────────────────────────────────────────────────────

@dataclass(frozen=True)
class ObservationSnapshot:
    findings: Tuple[Dict[str, Any], ...] = ()
    count: int = 0
    priority_findings: Tuple[Dict[str, Any], ...] = ()
    latest_observations: Tuple[Dict[str, Any], ...] = ()
    timestamp: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "count": self.count,
            "findings": list(self.findings),
            "priority_findings": list(self.priority_findings),
            "latest_observations": list(self.latest_observations),
        }


@dataclass(frozen=True)
class MissionDashboardDTO:
    active_missions: int = 0
    pending_missions: int = 0
    completed_missions: int = 0
    failed_missions: int = 0
    summary: str = ""
    top_priorities: Tuple[str, ...] = ()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "active": self.active_missions,
            "pending": self.pending_missions,
            "completed": self.completed_missions,
            "failed": self.failed_missions,
            "summary": self.summary,
            "priorities": list(self.top_priorities),
        }


@dataclass(frozen=True)
class BrainDashboardDTO:
    decisions: int = 0
    proposals: int = 0
    patterns: int = 0
    observations: int = 0
    latest_insight: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "decisions": self.decisions,
            "proposals": self.proposals,
            "patterns": self.patterns,
            "observations": self.observations,
            "insight": self.latest_insight,
        }


@dataclass(frozen=True)
class TimelineSummary:
    total_events: int = 0
    latest_events: Tuple[Dict[str, Any], ...] = ()
    key_milestones: Tuple[str, ...] = ()
    recent_range: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total": self.total_events,
            "latest": list(self.latest_events),
            "milestones": list(self.key_milestones),
            "range": self.recent_range,
        }


@dataclass(frozen=True)
class MissionSummary:
    current: str = ""
    progress: float = 0.0
    blockers: Tuple[str, ...] = ()
    next_steps: Tuple[str, ...] = ()
    health: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "current": self.current,
            "progress": self.progress,
            "blockers": list(self.blockers),
            "next": list(self.next_steps),
            "health": self.health,
        }


class ContextAssembler:
    """
    Membangun ReasoningContext dari berbagai DTO input.

    Properti:
    - Deterministic: input sama → output sama
    - Size limited: setiap summary dipotong
    - Priority ordering: observasi → mission → brain → timeline
    - Deduplicate: evidence_id ganda dieliminasi
    - Truncate safely: tidak pernah error karena ukuran
    """

    MAX_SUMMARY_LENGTH = 1000
    MAX_EVIDENCE_IDS = 20

    def assemble(self,
                 operator_question: str,
                 observations: Optional[ObservationSnapshot] = None,
                 mission_dashboard: Optional[MissionDashboardDTO] = None,
                 brain_dashboard: Optional[BrainDashboardDTO] = None,
                 timeline: Optional[TimelineSummary] = None,
                 mission: Optional[MissionSummary] = None,
                 template_name: str = "",
                 system_prompt: str = "",
                 ) -> ReasoningContext:
        """Assemble ReasoningContext dari semua input."""
        observation_summary = self._summarize_observations(observations)
        mission_summary = self._summarize_mission_dashboard(mission_dashboard)
        timeline_summary = self._summarize_timeline(timeline)
        mission_status = self._summarize_mission_status(mission)
        brain_summary = self._summarize_brain(brain_dashboard)
        evidence_ids = self._gather_evidence_ids(
            observations, mission_dashboard, brain_dashboard
        )

        conversation_summary = self._build_conversation_summary(
            operator_question, observation_summary,
        )

        token_estimate = self._estimate_tokens(
            operator_question, conversation_summary, mission_summary,
            timeline_summary, observation_summary, mission_status,
            brain_summary, system_prompt,
        )

        return ReasoningContext(
            operator_question=operator_question,
            conversation_summary=conversation_summary[:self.MAX_SUMMARY_LENGTH],
            mission_summary=mission_summary[:self.MAX_SUMMARY_LENGTH],
            timeline_summary=timeline_summary[:self.MAX_SUMMARY_LENGTH],
            observation_summary=observation_summary[:self.MAX_SUMMARY_LENGTH],
            health_summary=mission_status[:self.MAX_SUMMARY_LENGTH],
            trust_summary=brain_summary[:self.MAX_SUMMARY_LENGTH],
            evidence_ids=evidence_ids[:self.MAX_EVIDENCE_IDS],
            template_name=template_name,
            system_prompt=system_prompt,
            token_estimate=token_estimate,
            timestamp=datetime.now().isoformat(timespec="seconds"),
        )

    def _summarize_observations(self, obs: Optional[ObservationSnapshot]) -> str:
        if not obs or obs.count == 0:
            return ""
        parts = [f"Observations: {obs.count} total"]
        if obs.priority_findings:
            parts.append("Priority findings:")
            for f in obs.priority_findings[:3]:
                t = f.get("title") or f.get("description") or str(f)
                parts.append(f"  - {t}")
        if obs.latest_observations:
            parts.append("Latest:")
            for o in obs.latest_observations[:3]:
                t = o.get("detail") or o.get("title") or str(o)
                parts.append(f"  - {t}")
        return "\n".join(parts)

    def _summarize_mission_dashboard(self, md: Optional[MissionDashboardDTO]) -> str:
        if not md:
            return ""
        parts = [
            f"Missions: {md.active_missions} active, {md.pending_missions} pending, "
            f"{md.completed_missions} completed, {md.failed_missions} failed"
        ]
        if md.summary:
            parts.append(f"Summary: {md.summary}")
        if md.top_priorities:
            parts.append("Priorities: " + ", ".join(md.top_priorities))
        return "\n".join(parts)

    def _summarize_timeline(self, tl: Optional[TimelineSummary]) -> str:
        if not tl:
            return ""
        parts = [f"Timeline: {tl.total_events} events"]
        if tl.recent_range:
            parts.append(f"Range: {tl.recent_range}")
        if tl.key_milestones:
            parts.append("Milestones: " + ", ".join(tl.key_milestones))
        if tl.latest_events:
            parts.append("Latest events:")
            for e in tl.latest_events[:3]:
                t = e.get("title") or e.get("description") or str(e)
                parts.append(f"  - {t}")
        return "\n".join(parts)

    def _summarize_mission_status(self, ms: Optional[MissionSummary]) -> str:
        if not ms:
            return ""
        parts = [f"Mission: {ms.current}", f"Progress: {ms.progress*100:.0f}%"]
        if ms.health:
            parts.append(f"Health: {ms.health}")
        if ms.blockers:
            parts.append("Blockers: " + ", ".join(ms.blockers))
        if ms.next_steps:
            parts.append("Next: " + ", ".join(ms.next_steps))
        return "\n".join(parts)

    def _summarize_brain(self, bd: Optional[BrainDashboardDTO]) -> str:
        if not bd:
            return ""
        parts = [
            f"Brain: {bd.decisions} decisions, {bd.proposals} proposals, "
            f"{bd.patterns} patterns, {bd.observations} observations"
        ]
        if bd.latest_insight:
            parts.append(f"Insight: {bd.latest_insight}")
        return "\n".join(parts)

    def _build_conversation_summary(self, question: str,
                                     observation_summary: str) -> str:
        parts = [f"Operator question: {question}"]
        if observation_summary:
            parts.append(observation_summary)
        return "\n".join(parts)

    def _gather_evidence_ids(self, *inputs: Any) -> Tuple[str, ...]:
        seen: set[str] = set()
        result: list[str] = []
        for inp in inputs:
            if hasattr(inp, "to_dict"):
                d = inp.to_dict()
                if "findings" in d and isinstance(d["findings"], list):
                    for f in d["findings"]:
                        if isinstance(f, dict) and "id" in f:
                            if f["id"] not in seen:
                                seen.add(f["id"])
                                result.append(f["id"])
        return tuple(result)

    def _estimate_tokens(self, *texts: str) -> int:
        total = 0
        for t in texts:
            if t:
                total += len(t) // 4 + 1
        return total
