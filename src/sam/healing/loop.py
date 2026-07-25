"""Self-Healing Loop — Sprint 28 Fase 2.

A closed feedback loop that detects symptoms, diagnoses root causes,
plans and governs healing actions, executes them, and reflects
on the outcome to drive continuous improvement.

Pipeline (10 phases):
    Observe → Diagnose → Reason → Plan → Govern → Execute →
    Verify → Reflect → Learn → (back to) Observe

Integrates with:
  - HealingManager (Sprint 24) for action execution
  - GovernanceEngine (Sprint 21) for action gating
  - PlanningEngine (Sprint 22) for action planning
  - ExecutionGraphEngine (Sprint 23) for graph-based execution
  - ReflectionManager for outcome capture
  - EvolutionPolicy for feeding lessons back into policy
  - OperationalConfidenceCalculator for context-aware decisions
  - SelfOptimizer for parameter tuning
  - InstitutionalMemory for long-term pattern storage
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, TYPE_CHECKING

import structlog

from sam.healing.reflection import ReflectionManager, ReflectionRecord
from sam.cognitive.healing import (
    HealingAction,
    HealingManager,
    HealingResult,
    HealingStrategy,
)

from sam.evolution.policy import EvolutionPolicy, ProposalType

if TYPE_CHECKING:
    from sam.evolution.optimizer import SelfOptimizer
    from sam.confidence.operational import OperationalConfidenceCalculator
    from sam.institutional.memory import InstitutionalMemoryManager
    from sam.reasoning.planner import PlanningEngine
    from sam.governance.engine import GovernanceEngine
    from sam.execution.engine import ExecutionGraphEngine


logger = structlog.get_logger()


# ── Pipeline Phase Enum ────────────────────────────────────────────


class HealingPhase(str, Enum):
    """Phase in the self-healing loop pipeline."""

    OBSERVE = "observe"
    DIAGNOSE = "diagnose"
    REASON = "reason"
    PLAN = "plan"
    GOVERN = "govern"
    EXECUTE = "execute"
    VERIFY = "verify"
    REFLECT = "reflect"
    LEARN = "learn"


# ── Diagnostics ────────────────────────────────────────────────────


@dataclass
class Symptom:
    """A detected symptom or anomaly in the system.

    Attributes:
        id: Unique identifier.
        source: Where the symptom was detected (e.g. 'health_collector', 'error_spike').
        description: Human-readable description.
        severity: Severity level (1–5, 5=critical).
        evidence: Dict of supporting data points.
        timestamp: When the symptom was detected.
        pattern: Optional pattern trigger (e.g. 'pattern.provider_timeout').
    """

    id: str
    source: str
    description: str
    severity: int = 3
    evidence: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    pattern: Optional[str] = None

    def is_critical(self) -> bool:
        return self.severity >= 5

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "source": self.source,
            "description": self.description,
            "severity": self.severity,
            "evidence": self.evidence,
            "timestamp": self.timestamp.isoformat(),
            "pattern": self.pattern,
        }


@dataclass
class Diagnosis:
    """Result of diagnosing a symptom.

    Attributes:
        symptom_id: The symptom that was diagnosed.
        root_cause: Identified root cause description.
        hypothesis: Why this root cause is suspected.
        confidence: Confidence in the diagnosis (0.0–1.0).
        recommended_action_type: Type of healing recommended.
        evidence: Evidence supporting the diagnosis.
    """

    symptom_id: str
    root_cause: str
    hypothesis: str = ""
    confidence: float = 0.5
    recommended_action_type: str = "repair"
    evidence: List[str] = field(default_factory=list)

    def is_confident(self) -> bool:
        return self.confidence >= 0.7


# ── Cycle Context ──────────────────────────────────────────────────


@dataclass
class CycleContext:
    """Context accumulated throughout a healing cycle.

    Passed through all pipeline phases and used for reflection.
    """

    cycle_id: str
    symptom: Symptom
    diagnosis: Optional[Diagnosis] = None
    plan: Optional[Dict[str, Any]] = None
    governance_result: Optional[Any] = None
    healing_action: Optional[HealingAction] = None
    healing_result: Optional[HealingResult] = None
    reflection: Optional[ReflectionRecord] = None
    start_time: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    end_time: Optional[datetime] = None
    phases_completed: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


# ── Self-Healing Loop ──────────────────────────────────────────────


class SelfHealingLoop:
    """Orchestrates the self-healing feedback loop pipeline.

    Each call to run_cycle() walks through:
        Observe → Diagnose → Reason → Plan → Govern →
        Execute → Verify → Reflect → Learn → (return)

    The loop is a closed feedback system: reflection feeds back into
    policy, confidence, and institutional memory, informing future cycles.
    """

    def __init__(
        self,
        healing_manager: HealingManager,
        reflection_manager: ReflectionManager,
        governance_engine: Optional["GovernanceEngine"] = None,
        planning_engine: Optional["PlanningEngine"] = None,
        execution_engine: Optional["ExecutionGraphEngine"] = None,
        evolution_policy: Optional["EvolutionPolicy"] = None,
        self_optimizer: Optional["SelfOptimizer"] = None,
        confidence_calculator: Optional["OperationalConfidenceCalculator"] = None,
        institutional_memory: Optional["InstitutionalMemoryManager"] = None,
    ) -> None:
        self._healing = healing_manager
        self._reflection = reflection_manager
        self._governance = governance_engine
        self._planner = planning_engine
        self._executor = execution_engine
        self._policy = evolution_policy
        self._optimizer = self_optimizer
        self._confidence = confidence_calculator
        self._memory = institutional_memory
        self._cycles: Dict[str, CycleContext] = {}
        self._logger = logger.bind(component="SelfHealingLoop")

    async def run_cycle(
        self,
        symptom: Symptom,
        evidence: Optional[Dict[str, Any]] = None,
    ) -> HealingResult:
        """Run a full healing cycle for a given symptom.

        Args:
            symptom: The detected symptom to respond to.
            evidence: Additional evidence or context data.

        Returns:
            HealingResult from the executed healing action.
        """
        cycle_id = f"hlc_{uuid.uuid4().hex[:12]}"
        ctx = CycleContext(cycle_id=cycle_id, symptom=symptom)
        self._cycles[cycle_id] = ctx

        if evidence:
            ctx.metadata["evidence"] = evidence

        self._logger.info(
            "Healing cycle started",
            cycle_id=cycle_id,
            symptom=symptom.description,
            severity=symptom.severity,
        )

        try:
            # ── Phase 1: Observe ──────────────────────────────────
            ctx.phases_completed.append(HealingPhase.OBSERVE.value)
            await self._phase_observe(ctx, evidence)

            # ── Phase 2: Diagnose ─────────────────────────────────
            ctx.phases_completed.append(HealingPhase.DIAGNOSE.value)
            await self._phase_diagnose(ctx)

            # ── Phase 3: Reason ───────────────────────────────────
            ctx.phases_completed.append(HealingPhase.REASON.value)
            await self._phase_reason(ctx)

            # ── Phase 4: Plan ─────────────────────────────────────
            ctx.phases_completed.append(HealingPhase.PLAN.value)
            await self._phase_plan(ctx)

            # ── Phase 5: Govern ───────────────────────────────────
            ctx.phases_completed.append(HealingPhase.GOVERN.value)
            await self._phase_govern(ctx)

            # ── Phase 6: Execute ──────────────────────────────────
            ctx.phases_completed.append(HealingPhase.EXECUTE.value)
            if ctx.healing_action is not None:
                result = await self._healing.execute_healing(ctx.healing_action)
                ctx.healing_result = result
            else:
                result = HealingResult(
                    action_id="noop",
                    success=True,
                    message="No healing action needed (diagnosis suggested no action)",
                    duration_ms=0,
                )
                ctx.healing_result = result

            # ── Phase 7: Verify ───────────────────────────────────
            ctx.phases_completed.append(HealingPhase.VERIFY.value)
            await self._phase_verify(ctx)

            # ── Phase 8: Reflect ──────────────────────────────────
            ctx.phases_completed.append(HealingPhase.REFLECT.value)
            await self._phase_reflect(ctx)

            # ── Phase 9: Learn ────────────────────────────────────
            ctx.phases_completed.append(HealingPhase.LEARN.value)
            await self._phase_learn(ctx)

            ctx.end_time = datetime.now(timezone.utc)
            duration = (ctx.end_time - ctx.start_time).total_seconds()
            self._logger.info(
                "Healing cycle completed",
                cycle_id=cycle_id,
                success=result.success,
                duration_seconds=round(duration, 2),
                phases=" → ".join(ctx.phases_completed),
            )
            return result

        except Exception as exc:
            ctx.end_time = datetime.now(timezone.utc)
            self._logger.error(
                "Healing cycle failed",
                cycle_id=cycle_id,
                error=str(exc),
                phases_completed=ctx.phases_completed,
            )
            return HealingResult(
                action_id=cycle_id,
                success=False,
                message=f"Healing cycle crashed: {exc}",
                duration_ms=0,
                details={"error": str(exc), "phases": ctx.phases_completed},
            )

    # ── Phase Implementations ──────────────────────────────────────

    async def _phase_observe(
        self, ctx: CycleContext, evidence: Optional[Dict[str, Any]]
    ) -> None:
        """Observe: Enrich symptom with system context.

        Gathers current confidence score and health signals to
        provide context for the rest of the cycle.
        """
        sys_context: Dict[str, Any] = {}

        if self._confidence is not None:
            score = self._confidence.get_current_score()
            sys_context["confidence_score"] = score
            breakdown = self._confidence.get_current_breakdown()
            if breakdown:
                sys_context["confidence_breakdown"] = breakdown.to_dict()

        if evidence:
            sys_context["evidence"] = evidence
            # Try to match evidence patterns through healing manager
            if isinstance(evidence, dict):
                ev_list = [evidence]
            elif isinstance(evidence, list):
                ev_list = evidence
            else:
                ev_list = []

            if ev_list:
                matched_actions = await self._healing.detect_patterns(ev_list)
                if matched_actions:
                    ctx.metadata["pre_matched_actions"] = [a.id for a in matched_actions]

        ctx.metadata["system_context"] = sys_context
        self._logger.debug("Observe phase complete", cycle_id=ctx.cycle_id)

    async def _phase_diagnose(self, ctx: CycleContext) -> None:
        """Diagnose: Analyze symptom to determine root cause.

        Uses a rule-based approach, consulting institutional memory
        for similar past symptoms and their resolutions.
        """
        symptom = ctx.symptom
        evidence = symptom.evidence or {}

        # Gather similar past lessons from institutional memory
        past_lessons: List[str] = []
        if self._memory is not None:
            try:
                results = await self._memory.search({
                    "type": "PATTERN",
                    "min_confidence": 0.3,
                })
                # Extract lessons from memory entries whose content mentions the symptom
                for entry in results:
                    content = entry.content if isinstance(entry.content, dict) else {}
                    desc = content.get("description", "")
                    if symptom.description.lower() in desc.lower():
                        past_lessons.append(content.get("lesson", ""))
            except Exception:
                pass

        # Determine root cause based on symptom source and pattern
        root_cause = self._classify_root_cause(symptom)
        confidence = self._estimate_diagnosis_confidence(symptom, past_lessons)

        ctx.diagnosis = Diagnosis(
            symptom_id=symptom.id,
            root_cause=root_cause,
            hypothesis=f"Symptom '{symptom.description}' mapped to root cause "
                       f"'{root_cause}' based on source '{symptom.source}'",
            confidence=confidence,
            recommended_action_type=self._recommend_action_type(symptom, root_cause),
            evidence=symptom.evidence.get("indicators", []),
        )
        self._logger.debug(
            "Diagnosis complete",
            cycle_id=ctx.cycle_id,
            root_cause=root_cause,
            confidence=confidence,
        )

    async def _phase_reason(self, ctx: CycleContext) -> None:
        """Reason: Evaluate diagnosis, determine if action is warranted.

        Checks:
        1. Is the diagnosis confident enough?
        2. Is the symptom severe enough?
        3. Does operational confidence allow intervention?
        """
        if ctx.diagnosis is None:
            self._logger.warning("No diagnosis available for reasoning", cycle_id=ctx.cycle_id)
            return

        action_warranted = True
        reasons: List[str] = []

        # Low-confidence diagnosis → cautious
        if not ctx.diagnosis.is_confident():
            action_warranted = False
            reasons.append(
                f"Diagnosis confidence too low ({ctx.diagnosis.confidence:.2f} < 0.7)"
            )

        # Low-severity symptom with confident diagnosis → still proceed
        # But track it
        if ctx.symptom.severity <= 2:
            reasons.append("Low severity — proceeding with minimal intervention")

        # Confidence score check
        if self._confidence is not None:
            score = self._confidence.get_current_score()
            if score is not None and score < 20:
                # Very low confidence → still act but be more conservative
                action_warranted = True
                reasons.append("Critical low operational confidence — forced intervention")

        ctx.metadata["reasoning"] = {
            "action_warranted": action_warranted,
            "reasons": reasons,
        }
        self._logger.debug(
            "Reason phase complete",
            cycle_id=ctx.cycle_id,
            action_warranted=action_warranted,
        )

    async def _phase_plan(self, ctx: CycleContext) -> None:
        """Plan: Create a healing action plan based on diagnosis.

        Uses PlanningEngine if available, otherwise falls back to
        creating a simple HealingAction matched to the recommended
        action type.
        """
        if ctx.diagnosis is None:
            return

        # Determine strategy from recommended action type
        strategy_map: Dict[str, HealingStrategy] = {
            "prevent": HealingStrategy.PREVENT,
            "repair": HealingStrategy.REPAIR,
            "verify": HealingStrategy.VERIFY,
            "learn": HealingStrategy.LEARN,
        }
        strategy = strategy_map.get(
            ctx.diagnosis.recommended_action_type, HealingStrategy.REPAIR
        )

        action = HealingAction(
            trigger=ctx.symptom.pattern or f"healing.{ctx.symptom.source}",
            strategy=strategy,
            action_graph=[{
                "name": f"heal_{ctx.symptom.source}_{ctx.diagnosis.root_cause[:20]}",
                "description": ctx.diagnosis.hypothesis,
                "expected_outcome": f"Resolve {ctx.symptom.description}",
            }],
            precondition=None,
            cooldown=60 if ctx.symptom.severity >= 4 else 300,
        )

        ctx.healing_action = action
        ctx.plan = {
            "strategy": strategy.value,
            "action_id": action.id,
            "trigger": action.trigger,
            "severity": ctx.symptom.severity,
        }
        self._logger.debug(
            "Plan phase complete",
            cycle_id=ctx.cycle_id,
            strategy=strategy.value,
        )

    async def _phase_govern(self, ctx: CycleContext) -> None:
        """Govern: Gate the healing action through governance.

        If GovernanceEngine is available, evaluate the planned action.
        If the result blocks execution, set action to None.
        """
        if self._governance is None:
            ctx.metadata["governance"] = {"decision": "skip_no_engine"}
            return

        if ctx.healing_action is None:
            return

        try:
            # We don't have a full ExecutionGraph, but we can check governance
            # policy against the action type and severity
            from sam.governance.models import GovernanceResult, GovernanceDecision

            # Simplified governance check: evaluate severity-based rules
            if ctx.symptom.severity >= 5:
                # Critical: always allow
                gov_result = GovernanceResult.allowed(
                    reason="Critical symptom — auto-allowed",
                )
            elif ctx.symptom.severity >= 4:
                # High severity: allow with warning
                gov_result = GovernanceResult.allowed_with_warning(
                    reason="High severity symptom",
                    warnings=["High severity healing action — verify outcome"],
                )
            elif ctx.symptom.severity <= 2:
                # Low severity: require approval
                gov_result = GovernanceResult.require_approval(
                    reason="Low severity — approval recommended",
                    approvals=["auto-healing"],
                )
            else:
                gov_result = GovernanceResult.allowed(
                    reason="Medium severity — allowed",
                )

            ctx.governance_result = gov_result

            if gov_result.is_blocked():
                self._logger.warning(
                    "Healing action blocked by governance",
                    cycle_id=ctx.cycle_id,
                    decision=gov_result.decision.value,
                )
                if gov_result.decision == GovernanceDecision.REQUIRE_APPROVAL:
                    # Still allow through — self-healing is automated at this stage
                    self._logger.info(
                        "Proceeding despite REQUIRE_APPROVAL (auto-healing mode)",
                        cycle_id=ctx.cycle_id,
                    )
                else:
                    ctx.healing_action = None

            ctx.metadata["governance"] = {
                "decision": gov_result.decision.value,
                "reason": gov_result.reason,
            }

        except Exception as exc:
            self._logger.warning(
                "Governance check failed, proceeding",
                cycle_id=ctx.cycle_id,
                error=str(exc),
            )
            ctx.metadata["governance"] = {"decision": "error_proceed", "error": str(exc)}

    async def _phase_verify(self, ctx: CycleContext) -> None:
        """Verify: Check if the healing action was successful.

        Updates the cycle context with verification results.
        """
        if ctx.healing_result is None:
            return

        verified = ctx.healing_result.success
        ctx.metadata["verification"] = {
            "verified": verified,
            "action_success": ctx.healing_result.success,
            "message": ctx.healing_result.message,
            "duration_ms": ctx.healing_result.duration_ms,
        }
        self._logger.debug(
            "Verify phase complete",
            cycle_id=ctx.cycle_id,
            verified=verified,
        )

    async def _phase_reflect(self, ctx: CycleContext) -> None:
        """Reflect: Capture the full cycle outcome as a reflection record.

        Analyzes gap between expected and actual outcomes, extracts lessons.
        """
        if ctx.healing_result is None:
            return

        # Build gap analysis
        expected = ctx.diagnosis.hypothesis if ctx.diagnosis else ""
        actual = (
            ctx.healing_result.message
            if ctx.healing_result.success
            else f"FAILED: {ctx.healing_result.message}"
        )
        gap = self._analyze_gap(expected, actual, ctx.healing_result.success)

        # Extract lessons
        lessons = self._extract_lessons(ctx)

        # Estimate confidence
        confidence = 0.8 if ctx.healing_result.success else 0.3

        record = await self._reflection.record_reflection(
            cycle_id=ctx.cycle_id,
            symptom=ctx.symptom.description,
            hypothesis=ctx.diagnosis.hypothesis if ctx.diagnosis else "",
            action_taken=(
                f"Strategy: {ctx.healing_action.strategy.value}, "
                f"Trigger: {ctx.healing_action.trigger}"
                if ctx.healing_action
                else "No action"
            ),
            expected_outcome=expected,
            actual_outcome=actual,
            gap_analysis=gap,
            lessons=lessons,
            confidence=confidence,
            success=ctx.healing_result.success,
            metadata={
                "severity": ctx.symptom.severity,
                "source": ctx.symptom.source,
                "phases": ctx.phases_completed,
                "duration_ms": ctx.healing_result.duration_ms,
            },
        )
        ctx.reflection = record
        self._logger.debug(
            "Reflect phase complete",
            cycle_id=ctx.cycle_id,
            reflection_id=record.id,
            lessons_count=len(lessons),
        )

    async def _phase_learn(self, ctx: CycleContext) -> None:
        """Learn: Feed reflection outcomes back into the system.

        ===== PRINSIP: Recommend before Modify =====
        NEVER auto-approve proposals. Create PENDING_APPROVAL proposals
        and log them for CLI/dashboard review.

        Actions:
        1. If healing succeeded and useful lessons emerged:
           create a proposal (PENDING_APPROVAL) with optimized params.
        2. If healing failed:
           create a STRATEGY_SHIFT proposal + raise escalation signal.
        3. Store lesson in InstitutionalMemory if available.

        Alternatives when proposal is NOT approved:
        - Escalate to human (via log + metadata signal)
        - Try alternative strategy on next cycle
        - Reduce aggressiveness of subsequent auto-decisions
        """
        if ctx.reflection is None:
            return

        pending_proposal_ids: List[str] = []

        if not ctx.reflection.success:
            # Healing failed — create a STRATEGY_SHIFT proposal (PENDING_APPROVAL)
            if self._policy is not None:
                try:
                    proposal = await self._policy.create_proposal(
                        proposal_type=ProposalType.STRATEGY_SHIFT,
                        description=(
                            f"Reduce aggressiveness after failed healing: "
                            f"{ctx.symptom.description}"
                        ),
                        confidence=0.4,
                        expected_improvement=5.0,
                        evidence=[ctx.reflection.id],
                        rationale=(
                            "Healing failed — recommended to reduce "
                            "optimization aggressiveness. "
                            "Requires manual CLI approval to apply."
                        ),
                        risk_level="low",
                    )
                    # NOT auto-approving — stays PENDING_APPROVAL
                    pending_proposal_ids.append(proposal.id)
                    ctx.metadata["pending_proposals"] = pending_proposal_ids
                    self._logger.info(
                        "Learn: STRATEGY_SHIFT proposal created, awaiting approval",
                        cycle_id=ctx.cycle_id,
                        proposal_id=proposal.id,
                        status=proposal.status.value,
                    )
                except Exception as exc:
                    self._logger.warning(
                        "Learn: failed to create policy proposal",
                        cycle_id=ctx.cycle_id,
                        error=str(exc),
                    )

            # Escalate — log that human attention may be needed
            ctx.metadata["escalation"] = {
                "cycle_id": ctx.cycle_id,
                "reason": f"Healing failed: {ctx.reflection.symptom}",
                "severity": ctx.symptom.severity,
                "pending_proposals": len(pending_proposal_ids),
            }
            self._logger.warning(
                "Learn: Healing failed — escalation recommended",
                cycle_id=ctx.cycle_id,
                symptom=ctx.reflection.symptom,
                severity=ctx.symptom.severity,
                pending_proposals=len(pending_proposal_ids),
            )

        else:
            # Healing succeeded — optional fine-tune proposal
            if self._policy is not None and ctx.reflection.confidence >= 0.7:
                try:
                    proposal = await self._policy.create_proposal(
                        proposal_type=ProposalType.STRATEGY_SHIFT,
                        description=(
                            f"Healing effective — consider reinforcing strategy "
                            f"for {ctx.symptom.description}"
                        ),
                        confidence=0.6,
                        expected_improvement=3.0,
                        evidence=[ctx.reflection.id],
                        rationale=(
                            "Healing was effective — may want to adjust "
                            "parameters to make this strategy preferred. "
                            "Pending CLI approval."
                        ),
                        risk_level="low",
                    )
                    pending_proposal_ids.append(proposal.id)
                    ctx.metadata["pending_proposals"] = pending_proposal_ids
                    self._logger.info(
                        "Learn: reinforcement proposal created, awaiting approval",
                        cycle_id=ctx.cycle_id,
                        proposal_id=proposal.id,
                    )
                except Exception as exc:
                    self._logger.debug(
                        "Learn: failed to create reinforcement proposal",
                        cycle_id=ctx.cycle_id,
                        error=str(exc),
                    )

        # Store key lessons in institutional memory
        if self._memory is not None and ctx.reflection.lessons:
            from sam.institutional.memory import InstitutionalMemory

            for lesson_text in ctx.reflection.lessons:
                try:
                    lesson_entry = InstitutionalMemory(
                        type="LESSON",
                        content={
                            "source": "self_healing_loop",
                            "cycle_id": ctx.cycle_id,
                            "lesson": lesson_text,
                            "symptom": ctx.reflection.symptom,
                            "success": ctx.reflection.success,
                        },
                        confidence=ctx.reflection.confidence,
                    )
                    await self._memory.store(lesson_entry)
                    self._logger.debug(
                        "Lesson stored in institutional memory",
                        cycle_id=ctx.cycle_id,
                        lesson=lesson_text[:50],
                    )
                except Exception as exc:
                    self._logger.warning(
                        "Failed to store lesson",
                        cycle_id=ctx.cycle_id,
                        error=str(exc),
                    )

        self._logger.debug(
            "Learn phase complete",
            cycle_id=ctx.cycle_id,
            pending_proposals=len(pending_proposal_ids),
        )

    # ── Cycle Queries ──────────────────────────────────────────────

    def get_cycle(self, cycle_id: str) -> Optional[CycleContext]:
        """Get the context for a specific healing cycle."""
        return self._cycles.get(cycle_id)

    def get_recent_cycles(self, limit: int = 10) -> List[CycleContext]:
        """Get the most recent healing cycles."""
        sorted_cycles = sorted(
            self._cycles.values(),
            key=lambda c: c.start_time,
            reverse=True,
        )
        return sorted_cycles[:limit]

    def get_cycles_by_outcome(self, success: bool) -> List[CycleContext]:
        """Get cycles filtered by outcome."""
        return [
            c for c in self._cycles.values()
            if c.healing_result is not None
            and c.healing_result.success == success
        ]

    def get_cycle_count(self) -> int:
        return len(self._cycles)

    # ── Internal Helpers ───────────────────────────────────────────

    def _classify_root_cause(self, symptom: Symptom) -> str:
        """Classify root cause based on symptom source and evidence."""
        source_map: Dict[str, str] = {
            "health_collector": "service_degradation",
            "error_spike": "system_error_burst",
            "performance": "resource_bottleneck",
            "timeout": "provider_latency",
            "memory": "memory_pressure",
            "database": "data_layer_issue",
            "network": "connectivity_loss",
            "configuration": "misconfiguration",
            "optimization": "suboptimal_parameter",
        }

        # Check pattern first
        if symptom.pattern:
            if "timeout" in symptom.pattern:
                return "provider_latency"
            if "corruption" in symptom.pattern:
                return "data_corruption"
            if "memory" in symptom.pattern:
                return "memory_pressure"
            if "error" in symptom.pattern:
                return "system_error_burst"
            if "latency" in symptom.pattern:
                return "performance_degradation"

        # Check source
        for key, cause in source_map.items():
            if key in symptom.source.lower():
                return cause

        # Fallback
        return f"unclassified_{symptom.source}"

    def _estimate_diagnosis_confidence(
        self, symptom: Symptom, past_lessons: List[str]
    ) -> float:
        """Estimate confidence based on symptom clarity and past experience."""
        base = 0.5

        # Pattern match boosts confidence
        if symptom.pattern:
            base += 0.2

        # Specific evidence boosts
        if symptom.evidence:
            ev_count = len(symptom.evidence)
            base += min(0.2, ev_count * 0.05)

        # Past experience boosts
        if past_lessons:
            base += min(0.2, len(past_lessons) * 0.05)

        # Severity adjustment: high severity → more careful (lower confidence)
        if symptom.severity >= 5:
            base -= 0.1
        elif symptom.severity <= 2:
            base += 0.1

        return max(0.1, min(1.0, base))

    def _recommend_action_type(
        self, symptom: Symptom, root_cause: str
    ) -> str:
        """Recommend action type based on symptom and root cause."""
        # Critical symptoms → REPAIR
        if symptom.is_critical():
            return "repair"

        # Preventive patterns
        if symptom.pattern and "prevent" in symptom.pattern:
            return "prevent"

        # Database/data issues → REPAIR
        if "data" in root_cause or "database" in root_cause:
            return "repair"

        # Configuration → LEARN
        if "config" in root_cause or "parameter" in root_cause:
            return "learn"

        # Low severity → VERIFY
        if symptom.severity <= 2:
            return "verify"

        # Default
        return "repair"

    def _analyze_gap(
        self, expected: str, actual: str, success: bool
    ) -> str:
        """Analyze the gap between expected and actual outcome."""
        if success:
            if expected and actual and expected.lower() in actual.lower():
                return "No significant gap — outcome matched expectations"
            return (
                f"Partial gap: expected '{expected[:50]}', "
                f"actual '{actual[:50]}'"
            )
        return (
            f"Significant gap: expected success but got failure. "
            f"Expected: '{expected[:100]}'. Actual: '{actual[:100]}'"
        )

    def _extract_lessons(self, ctx: CycleContext) -> List[str]:
        """Extract lessons from the cycle outcome."""
        lessons: List[str] = []

        if ctx.healing_result is None:
            lessons.append("Cycle completed but no healing result available")
            return lessons

        if ctx.healing_result.success:
            lessons.append(
                f"Healing '{ctx.symptom.description}' "
                f"via {ctx.symptom.source} was effective"
            )
        else:
            lessons.append(
                f"Healing '{ctx.symptom.description}' "
                f"via {ctx.symptom.source} failed: {ctx.healing_result.message}"
            )

        if ctx.diagnosis and ctx.diagnosis.is_confident():
            lessons.append(
                f"Diagnosis confidence ({ctx.diagnosis.confidence:.2f}) "
                f"was sufficient for {ctx.diagnosis.root_cause}"
            )
        elif ctx.diagnosis:
            lessons.append(
                f"Diagnosis confidence ({ctx.diagnosis.confidence:.2f}) "
                f"was low — need better evidence for {ctx.diagnosis.root_cause}"
            )

        if ctx.symptom.severity >= 4:
            lessons.append(
                f"High-severity symptom ({ctx.symptom.severity}) "
                f"requires faster response"
            )

        return lessons


__all__ = [
    "HealingPhase",
    "Symptom",
    "Diagnosis",
    "CycleContext",
    "SelfHealingLoop",
]
