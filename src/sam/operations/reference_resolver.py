"""
ReferenceResolver — Resolve natural references in conversation.

Maps phrases like "yang tadi", "keputusan terakhir", "mission itu"
to concrete domain objects using the active session context.
Deterministic, no NLP, no LLM.
"""

from dataclasses import dataclass, field
from typing import Optional, Any
from .conversation_session import get_session_context


@dataclass
class ResolvedReference:
    """Result of resolving a natural-language reference."""

    kind: str  # "mission" | "decision" | "recommendation" | "approval" | "timeline" | "verification" | "execution"
    value: Any  # The actual resolved object / identifier
    label: str = ""  # Human-readable description
    confidence: float = 1.0  # 0.0-1.0 how sure the resolver is
    raw_query: str = ""


# ── Phrase patterns ───────────────────────────────────────────────────
# Mapped to resolver strategies; checked in priority order.

_PATTERN_MISSION_REF = [
    "mission itu", "mission ini", "current mission", "saat ini",
]

_PATTERN_DECISION_REF = [
    "keputusan terakhir", "keputusan", "keputusan itu", "keputusan ini",
    "keputusan sebelumnya", "last decision", "decision",
]

_PATTERN_RECOMMENDATION_REF = [
    "rekomendasi", "rekomendasi terakhir", "rekomendasi pertama",
    "rekomendasi itu", "recommendation", "solusi", "saran",
]

_PATTERN_APPROVAL_REF = [
    "approval", "approval tersebut", "approval terakhir",
    "persetujuan", "persetujuan terakhir",
]

_PATTERN_TIMELINE_REF = [
    "yang tadi", "tadi", "baru saja", "terakhir", "sebelumnya",
    "kejadian terakhir", "timeline", "yang baru",
]

_PATTERN_VERIFICATION_REF = [
    "hasil verifikasi", "verifikasi", "verifikasi terakhir",
    "verifikasi sebelumnya", "check result",
]

_PATTERN_EXECUTION_REF = [
    "hasil eksekusi", "eksekusi", "tindakan", "action",
    "execution", "eksekusi terakhir",
]


class ReferenceResolver:
    """Resolves natural-language references using session context."""

    def __init__(self) -> None:
        self._ctx = get_session_context()

    def resolve(self, query: str) -> Optional[ResolvedReference]:
        """Try to resolve a natural phrase to a domain reference.

        Returns None if no pattern matches.
        """
        q = query.lower().strip()

        # ── Priority 1: Mission references ──────────────────────────
        for pat in _PATTERN_MISSION_REF:
            if pat in q:
                return self._resolve_mission()

        # ── Priority 2: Decision references ─────────────────────────
        for pat in _PATTERN_DECISION_REF:
            if pat in q:
                return self._resolve_decision()

        # ── Priority 3: Recommendation references ───────────────────
        for pat in _PATTERN_RECOMMENDATION_REF:
            if pat in q:
                return self._resolve_recommendation()

        # ── Priority 4: Approval references ─────────────────────────
        for pat in _PATTERN_APPROVAL_REF:
            if pat in q:
                return self._resolve_approval()

        # ── Priority 5: Timeline references ─────────────────────────
        for pat in _PATTERN_TIMELINE_REF:
            if pat in q:
                return self._resolve_timeline()

        # ── Priority 6: Verification references ─────────────────────
        for pat in _PATTERN_VERIFICATION_REF:
            if pat in q:
                return self._resolve_verification()

        # ── Priority 7: Execution references ────────────────────────
        for pat in _PATTERN_EXECUTION_REF:
            if pat in q:
                return self._resolve_execution()

        return None

    # ── Internal resolvers ─────────────────────────────────────────────

    def _resolve_mission(self) -> Optional[ResolvedReference]:
        if self._ctx.current_mission_id:
            return ResolvedReference(
                kind="mission",
                value=self._ctx.current_mission_id,
                label=self._ctx.current_mission_name or f"Mission {self._ctx.current_mission_id}",
            )
        return None

    def _resolve_decision(self) -> Optional[ResolvedReference]:
        if self._ctx.last_decision_id:
            return ResolvedReference(
                kind="decision",
                value={
                    "id": self._ctx.last_decision_id,
                    "title": self._ctx.last_decision_title,
                    "action": self._ctx.last_decision_action,
                    "risk": self._ctx.last_decision_risk,
                    "confidence": self._ctx.last_decision_confidence,
                },
                label=self._ctx.last_decision_title or f"Decision {self._ctx.last_decision_id}",
            )
        return None

    def _resolve_recommendation(self) -> Optional[ResolvedReference]:
        if self._ctx.last_recommendation_id:
            return ResolvedReference(
                kind="recommendation",
                value={
                    "id": self._ctx.last_recommendation_id,
                    "text": self._ctx.last_recommendation_text,
                    "alternatives": self._ctx.last_recommendation_alternatives,
                },
                label=self._ctx.last_recommendation_text or f"Recommendation {self._ctx.last_recommendation_id}",
            )
        return None

    def _resolve_approval(self) -> Optional[ResolvedReference]:
        if self._ctx.last_approval_id:
            return ResolvedReference(
                kind="approval",
                value={
                    "id": self._ctx.last_approval_id,
                    "status": self._ctx.last_approval_status,
                    "reason": self._ctx.last_approval_reason,
                },
                label=f"Approval {self._ctx.last_approval_id} ({self._ctx.last_approval_status or 'unknown'})",
            )
        return None

    def _resolve_timeline(self) -> Optional[ResolvedReference]:
        if self._ctx.last_timeline_event_id:
            return ResolvedReference(
                kind="timeline",
                value={
                    "id": self._ctx.last_timeline_event_id,
                    "type": self._ctx.last_timeline_event_type,
                    "description": self._ctx.last_timeline_event_description,
                    "timestamp": self._ctx.last_timeline_timestamp,
                },
                label=self._ctx.last_timeline_event_description or f"Event {self._ctx.last_timeline_event_id}",
            )
        return None

    def _resolve_verification(self) -> Optional[ResolvedReference]:
        if self._ctx.last_verification_result:
            return ResolvedReference(
                kind="verification",
                value=self._ctx.last_verification_result,
                label=f"Verification: {self._ctx.last_verification_result[:60]}",
            )
        return None

    def _resolve_execution(self) -> Optional[ResolvedReference]:
        if self._ctx.last_execution_plan_id:
            return ResolvedReference(
                kind="execution",
                value={
                    "plan_id": self._ctx.last_execution_plan_id,
                    "status": self._ctx.last_execution_status,
                },
                label=f"Execution {self._ctx.last_execution_plan_id} ({self._ctx.last_execution_status or 'unknown'})",
            )
        return None

    # ── Bulk resolver ──────────────────────────────────────────────────

    def resolve_all(self, query: str) -> list[ResolvedReference]:
        """Resolve all matching references in a query (order by priority)."""
        results: list[ResolvedReference] = []
        q = query.lower().strip()

        # Check each pattern group independently
        for pat in _PATTERN_MISSION_REF:
            if pat in q:
                ref = self._resolve_mission()
                if ref:
                    results.append(ref)
                break

        for pat in _PATTERN_DECISION_REF:
            if pat in q:
                ref = self._resolve_decision()
                if ref:
                    results.append(ref)
                break

        for pat in _PATTERN_RECOMMENDATION_REF:
            if pat in q:
                ref = self._resolve_recommendation()
                if ref:
                    results.append(ref)
                break

        for pat in _PATTERN_APPROVAL_REF:
            if pat in q:
                ref = self._resolve_approval()
                if ref:
                    results.append(ref)
                break

        for pat in _PATTERN_TIMELINE_REF:
            if pat in q:
                ref = self._resolve_timeline()
                if ref:
                    results.append(ref)
                break

        for pat in _PATTERN_VERIFICATION_REF:
            if pat in q:
                ref = self._resolve_verification()
                if ref:
                    results.append(ref)
                break

        for pat in _PATTERN_EXECUTION_REF:
            if pat in q:
                ref = self._resolve_execution()
                if ref:
                    results.append(ref)
                break

        return results
