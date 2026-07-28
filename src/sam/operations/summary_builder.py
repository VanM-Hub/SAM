"""
SummaryBuilder — Generates deterministic operational summaries after each mission.

All data comes from existing domain objects. No LLM, no templates.
Fully deterministic, safe for conversation output.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime


@dataclass
class OperationalSummary:
    """Complete mission summary — pure data, no renderer."""
    mission_name: str = ""
    mission_id: str = ""
    mission_state: str = ""
    mission_duration_seconds: float = 0.0
    mission_started_at: str = ""
    mission_ended_at: str = ""

    # ── Problem ───────────────────────────────────────────────────────
    problem: str = ""
    problem_category: str = ""

    # ── Evidence ──────────────────────────────────────────────────────
    evidence_count: int = 0
    evidence_items: list[str] = field(default_factory=list)

    # ── Decision ──────────────────────────────────────────────────────
    decision_taken: str = ""
    decision_risk: str = ""
    decision_confidence: float = 0.0

    # ── Execution ─────────────────────────────────────────────────────
    execution_plan_id: str = ""
    execution_status: str = ""
    execution_steps_completed: int = 0
    execution_steps_total: int = 0

    # ── Verification ──────────────────────────────────────────────────
    verification_status: str = ""
    verification_details: str = ""

    # ── Result ────────────────────────────────────────────────────────
    result_status: str = ""  # "success" | "partial" | "failed"
    result_description: str = ""

    # ── Remaining Risk ────────────────────────────────────────────────
    remaining_risk_level: str = "low"
    remaining_risk_description: str = ""

    # ── Recommendation ────────────────────────────────────────────────
    recommendation_text: str = ""
    recommendation_action: str = ""

    # ── Trust ─────────────────────────────────────────────────────────
    trust_score: float = 0.0
    trust_grade: str = ""

    # ── Metadata ──────────────────────────────────────────────────────
    generated_at: str = field(default_factory=lambda: datetime.now().isoformat())

    @property
    def verdict(self) -> str:
        if self.result_status == "success":
            return "✅ Mission completed successfully."
        elif self.result_status == "partial":
            return "⚠️ Mission completed with partial results."
        elif self.result_status == "failed":
            return "❌ Mission failed."
        return f"Mission ended with status: {self.result_status}"

    @property
    def short_summary(self) -> str:
        return (
            f"[{self.mission_name}] "
            f"{self.result_status.upper()} — "
            f"{self.decision_taken[:40] or '—'}"
        )


class SummaryBuilder:
    """Builds an OperationalSummary from existing domain objects.

    Usage:
        builder = SummaryBuilder()
        summary = builder.build(mission, decision, executor, verification, trust)
    """

    def __init__(self) -> None:
        pass

    def build(
        self,
        mission: Optional[object] = None,
        decision: Optional[object] = None,
        execution: Optional[object] = None,
        verification: Optional[object] = None,
        trust: Optional[object] = None,
    ) -> OperationalSummary:
        """Construct a summary from available domain objects.

        Gracefully handles None inputs — missing data produces empty fields.
        """
        s = OperationalSummary()

        self._extract_mission(s, mission)
        self._extract_decision(s, decision)
        self._extract_execution(s, execution)
        self._extract_verification(s, verification)
        self._extract_trust(s, trust)
        self._determine_result(s)

        return s

    # ── Extractors ────────────────────────────────────────────────────

    @staticmethod
    def _extract_mission(s: OperationalSummary, mission: Optional[object]) -> None:
        if mission is None:
            return
        s.mission_id = _get(mission, "mission_id", "") or _get(mission, "id", "")
        s.mission_name = _get(mission, "name", "") or s.mission_id
        s.mission_state = _get(mission, "state", "") or _get(mission, "status", "")
        s.mission_started_at = _get(mission, "created_at", "") or _get(mission, "started_at", "")
        s.mission_ended_at = _get(mission, "updated_at", "") or _get(mission, "ended_at", "")
        s.problem = _get(mission, "problem", "") or _get(mission, "description", "")
        s.problem_category = _get(mission, "category", "")

        # Evidence
        ev = _get(mission, "evidence", None) or _get(mission, "evidence_items", None)
        if isinstance(ev, list):
            s.evidence_items = [str(e) for e in ev]
            s.evidence_count = len(ev)

        # Duration
        start = _get(mission, "started_at", None) or _get(mission, "created_at", None)
        end = _get(mission, "ended_at", None) or _get(mission, "updated_at", None)
        if start and end:
            try:
                s_start = datetime.fromisoformat(start)
                s_end = datetime.fromisoformat(end)
                s.mission_duration_seconds = (s_end - s_start).total_seconds()
            except Exception:
                pass

    @staticmethod
    def _extract_decision(s: OperationalSummary, decision: Optional[object]) -> None:
        if decision is None:
            return
        s.decision_taken = _get(decision, "title", "") or _get(decision, "description", "") or _get(decision, "action", "")
        s.decision_risk = _get(decision, "risk", "") or _get(decision, "risk_level", "")
        s.decision_confidence = float(_get(decision, "confidence", 0.0))

    @staticmethod
    def _extract_execution(s: OperationalSummary, execution: Optional[object]) -> None:
        if execution is None:
            return
        s.execution_plan_id = _get(execution, "plan_id", "") or _get(execution, "id", "")
        s.execution_status = _get(execution, "status", "")
        s.execution_steps_completed = int(_get(execution, "steps_completed", 0))
        s.execution_steps_total = int(_get(execution, "steps_total", 0))

    @staticmethod
    def _extract_verification(s: OperationalSummary, verification: Optional[object]) -> None:
        if verification is None:
            return
        s.verification_status = _get(verification, "status", "") or _get(verification, "result", "")
        s.verification_details = _get(verification, "details", "") or _get(verification, "description", "")

    @staticmethod
    def _extract_trust(s: OperationalSummary, trust: Optional[object]) -> None:
        if trust is None:
            return
        s.trust_score = float(_get(trust, "score", 0.0))
        s.trust_grade = _get(trust, "grade", "")

    @staticmethod
    def _determine_result(s: OperationalSummary) -> None:
        """Infer result status from execution + verification + mission state."""
        state = s.mission_state.lower() if s.mission_state else ""
        exec_status = s.execution_status.lower() if s.execution_status else ""
        ver_status = s.verification_status.lower() if s.verification_status else ""

        if "failed" in state or "failed" in exec_status or "failed" in ver_status:
            s.result_status = "failed"
        elif "completed" in state or "success" in exec_status or "passed" in ver_status:
            s.result_status = "success"
        elif "partial" in state or "partial" in exec_status:
            s.result_status = "partial"
        else:
            s.result_status = state or "unknown"

        s.result_description = (
            f"Mission {s.mission_name} ended as {s.result_status} "
            f"({s.execution_steps_completed}/{s.execution_steps_total} steps completed)"
        )


# ── Helper ────────────────────────────────────────────────────────────

def _get(obj: object, attr: str, default: object = "") -> object:
    """Safely get an attribute regardless of dict/dataclass/namedtuple."""
    if obj is None:
        return default
    if isinstance(obj, dict):
        return obj.get(attr, default)
    return getattr(obj, attr, default)
