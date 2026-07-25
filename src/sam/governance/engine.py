"""
Governance Engine – Sprint 21 Fase 3

Orchestrates governance evaluators, merges results, and produces
an aggregate GovernanceResult. Integrates with ExecutionGraphEngine
to gate graph execution.
"""

from __future__ import annotations

import json
import uuid
import asyncio
from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Set

import structlog

from .models import GovernanceDecision, GovernanceResult, GovernanceRule
from .evaluator import Evaluator

if TYPE_CHECKING:
    from ..execution.graph import ExecutionGraph
    from ..execution.engine import ExecutionGraphEngine
    from ..runtime.context import ExecutionContext
    from ..persistence.database import Database
    from ..core.clock import TimeProvider
    from ..core.resource_directory import ResourceDirectory


class GovernanceEngine:
    """Orchestrator that runs governance evaluators and merges results.

    Lifecycle:
    1. ``load_rules()`` — load GovernanceRules from the database
    2. ``evaluate(graph, context)`` — run all registered evaluators
    3. Merge results: most-restrictive decision wins
    4. Store the aggregate GovernanceResult in the database

    Integration with ExecutionGraphEngine:
    - Called **before** graph execution starts
    - If REJECT/ESCALATE: abort execution
    - If REQUIRE_APPROVAL: pause graph, store result for approval
    - If WAIT: delay execution (suggested_delay)
    - If ALLOW/ALLOW_WITH_WARNING: proceed
    """

    # Decision priority: higher number = more restrictive
    _DECISION_PRIORITY: Dict[GovernanceDecision, int] = {
        GovernanceDecision.ALLOW: 1,
        GovernanceDecision.ALLOW_WITH_WARNING: 2,
        GovernanceDecision.WAIT: 3,
        GovernanceDecision.REQUIRE_APPROVAL: 4,
        GovernanceDecision.REJECT: 5,
        GovernanceDecision.ESCALATE: 6,
    }

    def __init__(
        self,
        db: Optional["Database"] = None,
        clock: Optional["TimeProvider"] = None,
        resource_directory: Optional["ResourceDirectory"] = None,
    ) -> None:
        self._db = db
        self._clock = clock
        self._resource_directory = resource_directory
        self._evaluators: List[Evaluator] = []
        self._rules: List[GovernanceRule] = []
        self._logger = structlog.get_logger().bind(component="GovernanceEngine")

    # ── Public API ────────────────────────────────────────────────

    async def add_evaluator(self, evaluator: Evaluator) -> None:
        """Register an evaluator with the engine."""
        self._evaluators.append(evaluator)
        self._logger.info(
            "evaluator_added",
            evaluator=evaluator.name,
            total=len(self._evaluators),
        )

    async def load_rules(self) -> List[GovernanceRule]:
        """Load governance rules from the database (migration 020).

        Returns the loaded rules. If no database is configured,
        returns an empty list.
        """
        if not self._db:
            self._logger.debug("no_database_configured")
            self._rules = []
            return self._rules

        try:
            rows = await self._db.fetch_all(
                "SELECT * FROM governance_rules WHERE enabled = 1"
            )
        except Exception as exc:
            self._logger.warning("load_rules_failed", error=str(exc))
            self._rules = []
            return self._rules

        rules: List[GovernanceRule] = []
        for row in rows:
            decision = None
            if row.get("decision_override"):
                try:
                    decision = GovernanceDecision(row["decision_override"])
                except ValueError:
                    decision = None
            created_at = row.get("created_at")
            updated_at = row.get("updated_at")
            if not created_at:
                created_at = None
            if not updated_at:
                updated_at = None

            rules.append(
                GovernanceRule(
                    id=row["id"],
                    name=row["name"],
                    evaluator_type=row["evaluator_type"],
                    condition=row.get("condition", ""),
                    decision_override=decision,
                    enabled=bool(row.get("enabled", 1)),
                    metadata=json.loads(row.get("metadata_json", "{}")),
                    created_at=created_at,
                    updated_at=updated_at,
                )
            )

        self._rules = rules
        self._logger.info("rules_loaded", count=len(rules))
        return self._rules

    async def evaluate(
        self,
        graph: "ExecutionGraph",
        context: "ExecutionContext",
    ) -> GovernanceResult:
        """Run all registered evaluators and merge results.

        Returns an aggregate GovernanceResult with per-evaluator details
        in ``evaluator_results``.
        """
        if not self._evaluators:
            self._logger.warning("no_evaluators_registered", graph_id=graph.id)
            return GovernanceResult.allowed(
                reason="No evaluators registered — allowing by default",
            )

        self._logger.info(
            "evaluation_starting",
            graph_id=graph.id,
            evaluators=[e.name for e in self._evaluators],
        )

        results: Dict[str, GovernanceResult] = {}
        decisions: List[GovernanceDecision] = []
        merged_warnings: List[str] = []
        merged_reasons: List[str] = []
        merged_approvals: List[str] = []
        merged_metadata: Dict[str, Any] = {}
        merged_delay: Optional[int] = None

        for evaluator in self._evaluators:
            try:
                result = await evaluator.evaluate(graph, context)
                results[evaluator.name] = result
                decisions.append(result.decision)

                if result.reason:
                    merged_reasons.append(f"[{evaluator.name}] {result.reason}")
                if result.warnings:
                    merged_warnings.extend(result.warnings)
                if result.required_approvals:
                    merged_approvals.extend(result.required_approvals)
                if result.metadata:
                    merged_metadata[evaluator.name] = result.metadata
                if result.suggested_delay is not None:
                    if merged_delay is None:
                        merged_delay = result.suggested_delay
                    else:
                        merged_delay = max(merged_delay, result.suggested_delay)

            except Exception as exc:
                self._logger.error(
                    "evaluator_crashed",
                    evaluator=evaluator.name,
                    error=str(exc),
                )
                error_result = GovernanceResult.rejected(
                    reason=f"Evaluator '{evaluator.name}' crashed: {exc}",
                )
                results[evaluator.name] = error_result
                decisions.append(GovernanceDecision.REJECT)
                merged_reasons.append(f"[{evaluator.name}] Crashed: {exc}")

        # Merge: most restrictive decision wins
        final_decision = max(
            decisions,
            key=lambda d: self._DECISION_PRIORITY.get(d, 0),
        )

        # Build aggregate result
        aggregate = GovernanceResult(
            decision=final_decision,
            reason=" | ".join(merged_reasons) if merged_reasons else "All checks passed",
            warnings=merged_warnings,
            required_approvals=sorted(set(merged_approvals)),
            suggested_delay=merged_delay,
            evaluator_results=results,
            metadata={
                "graph_id": graph.id,
                "graph_name": getattr(graph, "name", graph.id),
                "evaluators_run": list(results.keys()),
                "decisions": {k: v.decision.value for k, v in results.items()},
                **merged_metadata,
            },
        )

        self._logger.info(
            "evaluation_complete",
            graph_id=graph.id,
            final_decision=final_decision.value,
            is_blocked=aggregate.is_blocked(),
        )

        # Optionally store result in database
        await self._store_result(graph.id, aggregate)

        return aggregate

    def get_rules(self) -> List[GovernanceRule]:
        """Return currently loaded rules."""
        return list(self._rules)

    def get_evaluators(self) -> List[Evaluator]:
        """Return registered evaluators."""
        return list(self._evaluators)

    # ── Integration with ExecutionGraphEngine ────────────────────

    async def gate_graph_execution(
        self,
        graph: "ExecutionGraph",
        context: "ExecutionContext",
        engine: "ExecutionGraphEngine",
    ) -> Optional["GovernanceResult"]:
        """Gate graph execution through governance evaluation.

        This is the main integration point with ExecutionGraphEngine.
        Called before graph execution to decide whether to proceed, pause,
        delay, or reject.

        Returns:
            - None if execution should proceed (ALLOW / ALLOW_WITH_WARNING)
            - GovernanceResult if execution is blocked/paused/delayed
              (caller handles WAIT, REQUIRE_APPROVAL, REJECT, ESCALATE)
        """
        result = await self.evaluate(graph, context)

        if result.is_allowed():
            self._logger.info(
                "governance_gate_allowed",
                graph_id=graph.id,
                decision=result.decision.value,
            )
            return None

        if result.decision == GovernanceDecision.WAIT:
            delay = result.suggested_delay or 60
            self._logger.info(
                "governance_gate_wait",
                graph_id=graph.id,
                delay=delay,
            )
            await engine.pause(graph.id, reason=result.reason)
            # Schedule resume after delay
            asyncio.create_task(self._delayed_resume(graph.id, engine, delay))
            return result

        if result.decision == GovernanceDecision.REQUIRE_APPROVAL:
            self._logger.info(
                "governance_gate_requires_approval",
                graph_id=graph.id,
                approvals=result.required_approvals,
            )
            await engine.pause(graph.id, reason=result.reason)
            return result

        # REJECT or ESCALATE
        self._logger.info(
            "governance_gate_blocked",
            graph_id=graph.id,
            decision=result.decision.value,
        )
        return result

    # ── Internal ──────────────────────────────────────────────────

    async def _store_result(
        self, graph_id: str, result: GovernanceResult
    ) -> None:
        """Persist the aggregate governance result to the database."""
        if not self._db:
            return

        try:
            rid = f"gr-{graph_id}-{uuid.uuid4().hex[:8]}"
            now = (self._clock.now() if self._clock else datetime.utcnow()).isoformat()

            evaluator_json = json.dumps(
                {k: v.model_dump() for k, v in result.evaluator_results.items()},
                default=str,
            )

            await self._db.execute(
                """
                INSERT INTO governance_results (
                    id, graph_id, decision, reason, warnings_json,
                    required_approvals_json, evaluator_results_json,
                    suggested_delay, metadata_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    rid,
                    graph_id,
                    result.decision.value,
                    result.reason,
                    json.dumps(result.warnings),
                    json.dumps(result.required_approvals),
                    evaluator_json,
                    result.suggested_delay,
                    json.dumps(result.metadata, default=str),
                    now,
                ],
            )
            self._logger.debug("result_stored", result_id=rid, graph_id=graph_id)
        except Exception as exc:
            self._logger.warning("store_result_failed", error=str(exc), graph_id=graph_id)

    async def _delayed_resume(
        self, graph_id: str, engine: "ExecutionGraphEngine", delay: int
    ) -> None:
        """Resume a paused graph after a delay (WAIT decision)."""
        try:
            if self._clock:
                await self._clock.sleep(delay)
            else:
                await asyncio.sleep(delay)
            await engine.resume(graph_id)
            self._logger.info("delayed_resume", graph_id=graph_id)
        except Exception as exc:
            self._logger.error("delayed_resume_failed", graph_id=graph_id, error=str(exc))
