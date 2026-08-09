"""Recovery API - WP-17 (MISSION-4.5 / IP-4.5-002).

Antarmuka standar untuk Autonomous Recovery. Read-only query; eksekusi
hanya lewat RecoveryExecutor (approval-gated).
"""
from __future__ import annotations

from typing import Any, Dict, Optional, Tuple

from .recovery_planning import RecoveryPlanner, RecoveryPlan
from .recovery_execution import RecoveryExecutor, RecoverySession
from .recovery_verification import RecoveryVerifier
from .recovery_explainability import RecoveryExplainer


class RecoveryAPI:
    """Facade untuk Autonomous Recovery."""

    def __init__(
        self,
        *,
        planner: RecoveryPlanner,
        executor: RecoveryExecutor,
        verifier: Optional[RecoveryVerifier] = None,
        explainer: Optional[RecoveryExplainer] = None,
    ) -> None:
        self._planner = planner
        self._executor = executor
        self._verifier = verifier or RecoveryVerifier()
        self._explainer = explainer or RecoveryExplainer()

    def plan(
        self, investigation_id: str, detected_issues: Tuple[str, ...], severity: str = "warning"
    ) -> RecoveryPlan:
        return self._planner.plan(
            investigation_id, detected_issues=detected_issues, severity=severity
        )

    def execute(
        self, plan: RecoveryPlan, *, approved: bool = False
    ) -> RecoverySession:
        session = self._executor.create_session(plan)
        return self._executor.execute(session, plan, approved=approved)

    def verify(self, session: RecoverySession) -> Dict[str, Any]:
        return self._verifier.verify(session).as_dict()

    def explain(self, plan: RecoveryPlan) -> Dict[str, Any]:
        return self._explainer.explain(plan).as_dict()

    def audit(self) -> Dict[str, Any]:
        return self._executor.audit()
