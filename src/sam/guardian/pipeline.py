"""
Guardian Decision Pipeline (GDP) — Phase 0

Mengintegrasikan semua engine menjadi satu pipeline yang konsisten.

Pipeline:
    Observe → Normalize → Evaluate → Policy Check →
    Risk Assessment → Plan → Approve → Execute → Verify → Audit
"""

import structlog
import time
from typing import Dict, Any, List, Optional

from ..runtime.coordinator import RuntimeCoordinator
from ..contracts import DesiredOperationalState
from .observer import ObserverEngine
from .analyzer import AnalyzerEngine
from .policy import PolicyEngine
from .action import ActionEngine
from .verification import VerificationEngine
from .decision import DecisionEngine, GuardianDecision

logger = structlog.get_logger()


class GuardianPipeline:
    """Guardian Decision Pipeline — satu siklus penuh GDP."""

    def __init__(
        self,
        coordinator: RuntimeCoordinator,
        dos: Optional[DesiredOperationalState] = None,
    ):
        self.coordinator = coordinator
        dos = dos or DesiredOperationalState()

        # Initialize all engines
        self.observer = ObserverEngine(coordinator)
        self.analyzer = AnalyzerEngine(dos)
        self.policy = PolicyEngine()
        self.action = ActionEngine()
        self.verification = VerificationEngine()
        self.decision = DecisionEngine(self.policy, self.action)

        # Track last decision
        self.last_decision: Optional[GuardianDecision] = None
        self.cycle_count: int = 0

    async def run_cycle(self) -> Dict[str, Any]:
        """Jalankan satu siklus penuh Guardian Decision Pipeline.

        Returns:
            Dict dengan status, drifts, dan decision.
        """
        start = time.time()
        self.cycle_count += 1
        cycle_id = f"cycle-{self.cycle_count}"

        logger.info("guardian_cycle_started", cycle_id=cycle_id)

        # 1. Observe — kumpulkan kondisi aktual
        observation = await self.observer.observe()

        # 2. Analyze — deteksi drift terhadap DOS
        drifts = await self.analyzer.analyze(observation)

        if not drifts:
            logger.info("guardian_cycle_no_drift", cycle_id=cycle_id)
            elapsed = int((time.time() - start) * 1000)
            return {
                "cycle_id": cycle_id,
                "status": "healthy",
                "drifts": [],
                "decision": None,
                "duration_ms": elapsed,
            }

        # 3-9. Decision Pipeline (Evaluate → Policy Check → Risk → Plan → Approve → Execute → Verify → Audit)
        decision = await self.decision.make_decision(drifts)
        self.last_decision = decision

        elapsed = int((time.time() - start) * 1000)
        logger.info("guardian_cycle_completed",
            cycle_id=cycle_id,
            drift_count=len(drifts),
            decision_id=decision.decision_id,
            approved=decision.approved,
            executed=decision.executed,
            verified=decision.verified,
            duration_ms=elapsed,
        )

        return {
            "cycle_id": cycle_id,
            "status": "completed",
            "drifts": drifts,
            "decision": decision.model_dump(),
            "duration_ms": elapsed,
        }

    async def run_cycles(self, count: int = 1, interval_sec: float = 5.0) -> List[Dict[str, Any]]:
        """Jalankan beberapa siklus GDP dengan interval.

        Args:
            count: Jumlah siklus.
            interval_sec: Interval antar siklus dalam detik.

        Returns:
            List hasil setiap siklus.
        """
        import asyncio
        results = []
        for i in range(count):
            result = await self.run_cycle()
            results.append(result)
            if i < count - 1:
                await asyncio.sleep(interval_sec)
        return results
