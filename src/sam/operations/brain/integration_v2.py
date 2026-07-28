"""
OP-259 — Proactive Pipeline Integration V2.

Integrates the full Sprint 20 pipeline into a single cohesive operation:
  Scheduler + MultiSourceObservation + Orchestrator + ProposalQueue + Health

This module ties together the proactive observation pipeline.
Does NOT start any thread/daemon — triggers are manual or via scheduler.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .scheduler import ObservationScheduler, SchedulerConfig, VersionedSnapshot
from .multi_source import MultiSourceObserver, MultiSourceSnapshot
from .orchestrator import MissionOrchestrator, OperationalPackage, OrchestratorConfig
from .proposal_queue import ProposalQueue, QueueItem, ProposalState
from .health import OperationalHealthEngine, OperationalHealthDTO


@dataclass
class ProactivePipelineResult:
    """Aggregated result from a proactive pipeline run."""

    timestamp: float
    sequence: int

    # Sub-results
    observation: Optional[MultiSourceSnapshot] = None
    orchestration: Optional[OperationalPackage] = None
    health: Optional[OperationalHealthDTO] = None

    # Queue state
    queue_size: int = 0
    ready_count: int = 0

    # Status
    success: bool = True
    error: Optional[str] = None

    @property
    def finding_count(self) -> int:
        if self.orchestration:
            return self.orchestration.finding_count
        return 0

    @property
    def recommendation_count(self) -> int:
        if self.orchestration:
            return self.orchestration.recommendation_count
        return 0

    def __repr__(self) -> str:
        return (
            f"ProactivePipelineResult(seq={self.sequence}, "
            f"ok={self.success}, "
            f"findings={self.finding_count}, "
            f"recs={self.recommendation_count}, "
            f"queue={self.queue_size})"
        )


class ProactivePipeline:
    """Integrated proactive pipeline for Sprint 20.

    Ties together:
      1. Multi-source observation
      2. Brain orchestration (rules -> analysis -> correlation -> priority -> recommendation -> proposal)
      3. Proposal queue management
      4. Health evaluation
      5. Scheduler integration

    This is a stateless orchestrator — instantiate and call run().
    """

    def __init__(
        self,
        orchestrator_config: Optional[OrchestratorConfig] = None,
    ) -> None:
        self._sequence = 0
        self._last_result: Optional[ProactivePipelineResult] = None
        self._orchestrator = MissionOrchestrator(config=orchestrator_config)
        self._multi_source = MultiSourceObserver()
        self._health_engine = OperationalHealthEngine()
        self._proposal_queue = ProposalQueue()

    @property
    def last_result(self) -> Optional[ProactivePipelineResult]:
        return self._last_result

    @property
    def proposal_queue(self) -> ProposalQueue:
        return self._proposal_queue

    @property
    def orchestrator(self) -> MissionOrchestrator:
        return self._orchestrator

    # ── Core run ───────────────────────────────────────────────────

    def run(
        self,
        skip_health: bool = False,
        skip_observation: bool = False,
        skip_orchestration: bool = False,
    ) -> ProactivePipelineResult:
        """Run the full proactive pipeline.

        Args:
            skip_health: Skip health evaluation.
            skip_observation: Skip multi-source observation.
            skip_orchestration: Skip brain pipeline orchestration.

        Returns:
            Aggregated pipeline result.
        """
        self._sequence += 1
        result = ProactivePipelineResult(
            timestamp=time.time(),
            sequence=self._sequence,
        )

        try:
            # Step 1: Multi-source observation
            if not skip_observation:
                result.observation = self._multi_source.observe_all()

            # Step 2: Brain orchestration
            if not skip_orchestration:
                result.orchestration = self._orchestrator.orchestrate(
                    skip_proposals=False,
                )
                # Feed proposals into queue
                if result.orchestration.proposals:
                    for prop in result.orchestration.proposals:
                        priority = _extract_priority(prop)
                        self._proposal_queue.push(
                            proposal_id=prop.proposal_id,
                            title=prop.title,
                            priority_score=priority,
                            metadata={
                                "recommendation_id": prop.recommendation_id,
                                "confidence": prop.confidence,
                            },
                        )

            # Step 3: Health evaluation
            if not skip_health:
                result.health = self._health_engine.evaluate()

            # Step 4: Queue state
            self._proposal_queue.expire_stale()
            result.queue_size = self._proposal_queue.size
            result.ready_count = self._proposal_queue.ready_count

            result.success = True

        except Exception as e:
            result.success = False
            result.error = str(e)

        self._last_result = result
        return result

    # ── Scheduler integration ──────────────────────────────────────

    def create_scheduler(
        self,
        interval_seconds: int = 300,
    ) -> ObservationScheduler:
        """Create a scheduler that runs this pipeline.

        Each tick runs run() and captures the result.
        """
        def _pipeline_tick() -> object:
            result = self.run()
            return result

        return ObservationScheduler(
            callback=_pipeline_tick,
            config=SchedulerConfig(interval_seconds=interval_seconds),
        )

    # ── Health convenience ─────────────────────────────────────────

    def get_health(self) -> OperationalHealthDTO:
        """One-shot health evaluation."""
        return self._health_engine.evaluate()


# ── Helpers ───────────────────────────────────────────────────────────


def _extract_priority(proposal: Any) -> float:
    """Extract priority score from a proposal.

    Tries numeric priority, then string mapping, then defaults.
    """
    priority_map: Dict[str, float] = {
        "critical": 90.0,
        "high": 70.0,
        "medium": 50.0,
        "low": 30.0,
        "info": 10.0,
    }
    val = getattr(proposal, "priority", "medium")
    if isinstance(val, (int, float)):
        return float(val)
    return priority_map.get(str(val).lower(), 50.0)


# ── Convenience ───────────────────────────────────────────────────────


def run_proactive_pipeline(
    skip_health: bool = False,
) -> ProactivePipelineResult:
    """One-shot: run the full proactive pipeline."""
    return ProactivePipeline().run(skip_health=skip_health)


def pipeline_summary(result: ProactivePipelineResult) -> str:
    """Build a human-readable summary of a pipeline run."""
    lines = [
        f"Pipeline #{result.sequence} @ {time.strftime('%H:%M:%S', time.localtime(result.timestamp))}",
    ]

    if result.observation:
        obs = result.observation
        lines.append(f"  Observation: {len(obs.ok_sources)}/{len(obs.sources)} sources OK")
        if obs.failed_sources:
            lines.append(f"    Failed: {', '.join(obs.failed_sources)}")

    if result.orchestration:
        orch = result.orchestration
        lines.append(f"  Orchestration: {orch.triggered_count} rules, {orch.finding_count} findings")
        lines.append(f"    {orch.correlation_count} correlations, {orch.recommendation_count} recommendations")
        lines.append(f"    {orch.proposal_count} proposals")

    if result.health:
        lines.append(f"  Health: {result.health.overall_score:.0f}/100 ({result.health.overall_status})")

    lines.append(f"  Queue: {result.queue_size} active ({result.ready_count} ready)")

    if not result.success:
        lines.append(f"  ERROR: {result.error}")

    return "\n".join(lines)
